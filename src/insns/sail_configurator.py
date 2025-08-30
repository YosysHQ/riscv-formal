"""configure instruction checker from sail"""
from itertools import product
import json
from pathlib import Path
import re
import click

from .wrapped_model import WrappedInstruction

@click.command()
@click.argument('sail', type=click.Path(exists=True, path_type=Path))
@click.argument('out_file', type=click.Path(path_type=Path))
def configure(sail: Path, out_file: Path):
    """main function"""

    insn = WrappedInstruction(
        name = "",
        insn_parts = [],
        opcode = "",
        checker_module = "",   
        extra_sig1 = [
            ("t_ExecutionResult", "sail_return_2", None),
        ],
        extra_sig2 = [
            ("bit", "sail_have_exception_2", None),
            ("t_exception", "sail_current_exception_2", None),
        ],
    )

    # load sail
    arg_types: list[str]
    maybe_args: list[str]
    in_encdec_op = False
    in_encdec_insn = False
    op_bits: int
    op_type: str = ""
    arg_remap: set[str] = set()
    enum_value_map: dict[str, str] = {}
    in_mnemonic = False
    in_assembly = False
    with open(sail, 'rt', encoding='utf-8') as f:
        for line in f:
            # instruction type def
            m = re.match(r"union clause instruction = (?P<insn>\w+) : \((?P<arg_types>.*)\)", line)
            if m:
                d = m.groupdict()
                insn.name = d['insn'].lower()
                insn.checker_module = f"execute_{d['insn']}"
                arg_types = d['arg_types'].split(", ")

            # op encoding
            m = re.match(r"mapping encdec_(?P<op_type>\w+) : (?P=op_type) <-> bits\((?P<op_bits>\d+)\) = {", line)
            if m and m.group(1) in arg_types:
                d = m.groupdict()
                in_encdec_op = True
                op_type = d['op_type']
                insn.op_type_enum = f"t_{op_type}"
                op_bits = int(d['op_bits'])
            if in_encdec_op:
                m = re.match(r"\s+(.*?)\s+<-> 0b([01]+),?", line)
                if line == "}":
                    in_encdec_op = False
                elif m:
                    x, y = m.groups()
                    enum_value_map[x] = y

            # instruction decoding
            m = re.match(r"mapping clause encdec = (?P<insn>\w+)\((?P<args>.*)\)(?:$|\s+<-> (?P<mapping>.*))", line)
            mapping = None
            if m and m.group(1) == insn.name.upper():
                maybe_args = []
                for maybe_arg in m.group(2).split(", "):
                    if "@" in maybe_arg:
                        maybe_args.append(maybe_arg.split(" @ "))
                    else:
                        maybe_args.append(maybe_arg)
                mapping = m.group(3)
                if mapping is None:
                    in_encdec_insn = True
            if in_encdec_insn:
                m = re.match(r"\s+<-> (?P<mapping>.*)", line)
                if m:
                    mapping = m.group(1)
                    in_encdec_insn = False
            if mapping:
                parts = mapping.split(" @ ")
                maybe_opcode = parts[-1]
                if maybe_opcode.startswith("0b") and len(maybe_opcode) == 9:
                    insn.opcode = maybe_opcode[2:]
                    parts[-1] = "opcode"
                part_idx = 0
                has_insn_parts = len(insn.insn_parts) != 0
                binary_parts: list[str] = []
                binary_part_names: list[str] = []
                for part in parts:
                    known_funcs = ["encdec_reg", "bool_bits", "width_enc"]
                    m = re.match(r"(\w+)\((\w+)\)", part)
                    if m and m.group(1) in known_funcs: part = m.group(2)
                    try:
                        idx = maybe_args.index(part)
                    except ValueError:
                        if part == "opcode":
                            part_size = 7
                        elif part.startswith("0b"):
                            value = part[2:]
                            part_size = len(value)
                            part = f"part_{part_idx}"
                            part_idx += 1
                            binary_parts.append(value)
                            binary_part_names.append(part)
                        elif part.startswith(f"encdec_{op_type}"):
                            part_size = op_bits
                            part = f"part_{part_idx}"
                            part_idx += 1
                            insn.op_value_switch = part
                        else:
                            m = re.match(r"((\w+?)_?[\d_]+) : bits\((\d+)\)", part)
                            part, arg_name, part_size = m.groups()
                            part_size = int(part_size)
                            arg_remap.add(arg_name)
                    else:
                        arg_type = arg_types[idx]
                        if arg_type == "regidx":
                            part_size = 5
                        elif arg_type.startswith("bits("):
                            part_size = int(arg_type[5:-1])
                        elif arg_type == "bool":
                            part_size = 1
                        elif arg_type == "word_width":
                            part_size = 2
                        else:
                            raise NotImplementedError(arg_type)
                    insn_part = (part, part_size)
                    if has_insn_parts:
                        if insn_part not in insn.insn_parts:
                            raise NotImplementedError
                    else:
                        insn.insn_parts.append(insn_part)
                if binary_parts:
                    # assumes the op is the last arg
                    enum_value_map[maybe_args[-1]] = "_".join(binary_parts)
                    insn.op_value_switch = " ".join(binary_part_names)
                    op_type = arg_types[-1]
                    insn.op_type_enum = f"t_{op_type}"

            # instruction args
            m = re.match(r"function clause execute \((?P<insn>\w+)\s?\((?P<args>.*)\)\) = {", line)
            if m and m.group(1) == insn.name.upper():
                d = m.groupdict()
                insn.inst_args = []
                for idx, inst_arg in enumerate(d['args'].split(', ')):
                    if inst_arg in arg_remap:
                        inst_arg = []
                        for inst_arg_part in maybe_args[idx]:
                            if inst_arg_part.startswith("0b"):
                                value = inst_arg_part[2:]
                                inst_arg_part = f"{len(value)}'b{value}"
                            inst_arg.append(inst_arg_part)
                        inst_arg = " ".join(inst_arg)
                    elif op_type == arg_types[idx]:
                            insn.op_name = inst_arg
                    insn.inst_args.append(inst_arg)
                insn.wrap_x_in = "rs2" in insn.inst_args or "rs1" in insn.inst_args
                insn.wrap_x_out = "rd" in insn.inst_args

            # jump check
            ml = re.findall(r"\b(jump_to|set_next_pc|get_next_pc)\(.*\)", line)
            if ml:
                insn.wrap_next_pc = True
            ml = re.findall(r"\b(PC\b|get_arch_pc\(\))", line)
            if ml:
                insn.wrap_pc = True

            # mnemonic mapping
            m = re.match(r"mapping (\w+)_mnemonic : (\w+) <-> string = {", line)
            if m and m.group(2) in arg_types:
                in_mnemonic = True
            if in_mnemonic:
                m = re.match(r"\s+(.*?)\s+<-> \"(\w+)\",?", line)
                if line == "}":
                    in_mnemonic = False
                elif m:
                    enum_value, mnemonic = m.groups()
                    value = enum_value_map[enum_value]
                    # convert mul_op to verilog struct
                    # e.g. struct { high = false, signed_rs1 = true,  signed_rs2 = true  }
                    # becomes {0, 1, 1}
                    if enum_value.startswith("struct"):
                        enum_value = "{" + ", ".join(value) + "}"
                    insn.op_values.append([mnemonic, enum_value, value])

            # assembly mapping as backup for mnemonic
            m = re.match(r"mapping clause assembly = (?P<insn>\w+)\s?\((?P<args>.*)\)", line)
            if m and len(insn.op_values) == 0:
                in_assembly = True
            if in_assembly:
                m = re.match(r"\s+<-> (?P<mapping>.*?) \^ spc\(\)", line)
                if m:
                    known_funcs = {
                        "width_mnemonic": ("logic [63:0]", [
                            ("b", "1", "00"),
                            ("h", "2", "01"),
                            ("w", "4", "10"),
                            ("d", "8", "11"),
                        ]),
                        "maybe_u": ("bit", [
                            ("", "0", "0"),
                            ("u", "1", "1"),
                        ]),
                    }
                    mnemonic_parts: list[str | tuple[str, str]] = []
                    mnemonic_keys: list[str] = []
                    mnemonic_types: list[str] = []
                    for part in m.group(1).split(" ^ "):
                        if re.match(r"\"(\w+)\"", part):
                            mnemonic_parts.append(part[1:-1])
                        else:
                            m = re.match(r"(\w+)\((\w+)\)", part)
                            if m and m.group(1) in known_funcs:
                                func, key = m.groups()
                                mnemonic_type, mnemonic_part = known_funcs[func]
                                mnemonic_parts.append(mnemonic_part)
                                mnemonic_keys.append(key)
                                mnemonic_types.append(mnemonic_type)
                            else:
                                raise NotImplementedError(f"assembly part {part}")
                    for prod in product(*mnemonic_parts):
                        mnemonic = ""
                        args = []
                        bits = []
                        for val in prod:
                            if isinstance(val, str):
                                mnemonic += val
                            else:
                                mnem, arg, bit = val
                                mnemonic += mnem
                                args.append(arg)
                                bits.append(bit)
                        insn.op_values.append((mnemonic, args, bits))
                    insn.op_name = mnemonic_keys
                    insn.op_type_enum = mnemonic_types
                    insn.op_value_switch = None
                    in_assembly = False

    # write json
    click.echo(f"Writing to {out_file}")
    with open(out_file, 'wt', encoding='utf-8') as f:
        json.dump(insn, f, indent=4)

if __name__ == "__main__":
    configure()
