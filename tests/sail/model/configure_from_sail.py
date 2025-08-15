"""configure_from_sail"""
import json
from pathlib import Path
import re
import click

@click.command()
@click.argument('sail', type=click.Path(exists=True, path_type=Path))
def configure(sail: Path):
    """main function"""

    name: str = ""
    insn_parts: list[tuple[str, int]] = []
    inst_args: list[str] = []
    wrap_x_in: bool = False
    wrap_x_out: bool = False
    wrap_pc: bool = False
    wrap_next_pc: bool = False
    x_upper: int = 31
    x_lower: int = 1
    r_bits: int = 5
    extra_sig1: list[tuple[str, str, str]] = [
        ("t_ExecutionResult", "sail_return_2", None),
    ]
    extra_sig2: list[tuple[str, str, str]] = [
        ("bit", "sail_have_exception_2", None),
        ("t_exception", "sail_current_exception_2", None),
    ]
    op_type_enum: str = ""
    op_values: list[tuple[str, str]] = []
    op_value_switch: str = ""
    checker_module: str = ""
    opcode: str = ""
    
    # load sail
    arg_types: list[str]
    maybe_args: list[str]
    in_encdec_op = False
    in_encdec_insn = False
    op_bits: int
    op_type: str = ""
    arg_remap: set[str] = set()
    with open(sail, 'rt', encoding='utf-8') as f:
        for line in f:
            # instruction type def
            m = re.match(r"union clause instruction = (?P<insn>\w+) : \((?P<arg_types>.*)\)", line)
            if m:
                d = m.groupdict()
                name = d['insn'].lower()
                checker_module = f"execute_{d['insn']}"
                arg_types = d['arg_types'].split(", ")

            # op encoding
            m = re.match(r"mapping encdec_(?P<op_type>\w+) : (?P=op_type) <-> bits\((?P<op_bits>\d+)\) = {", line)
            if m and m.group(1) in arg_types:
                d = m.groupdict()
                in_encdec_op = True
                op_type = d['op_type']
                op_type_enum = f"t_{op_type}"
                op_bits = int(d['op_bits'])
            if in_encdec_op:
                m = re.match(r"\s+(\w+)\s+<-> 0b([01]+),?", line)
                if line == "}":
                    in_encdec_op = False
                elif m:
                    x, y = m.groups()
                    op_values.append((y, x))

            # instruction decoding
            m = re.match(r"mapping clause encdec = (?P<insn>\w+)\((?P<args>.*)\)(?:$|\s+<-> (?P<mapping>.*))", line)
            mapping = None
            if m and m.group(1) == name.upper():
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
                    opcode = maybe_opcode[2:]
                    parts[-1] = "opcode"
                part_idx = 0
                has_insn_parts = len(insn_parts) != 0
                binary_parts: list[str] = []
                binary_part_names: list[str] = []
                for part in parts:
                    m = re.match(r"encdec_reg\((\w+)\)", part)
                    if m: part = m.group(1)
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
                            op_value_switch = part
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
                        else:
                            assert False
                    insn_part = (part, part_size)
                    if has_insn_parts:
                        assert insn_part in insn_parts
                    else:
                        insn_parts.append(insn_part)
                if binary_parts:
                    # assumes the op is the last arg
                    op_values.append(("_".join(binary_parts), maybe_args[-1]))
                    op_value_switch = " ".join(binary_part_names)
                    op_type_enum = f"t_{arg_types[-1]}"

            # instruction args
            m = re.match(r"function clause execute \((?P<insn>\w+)\s?\((?P<args>.*)\)\) = {", line)
            if m and m.group(1) == name.upper():
                d = m.groupdict()
                inst_args = []
                for idx, inst_arg in enumerate(d['args'].split(', ')):
                    if inst_arg in arg_remap:
                        inst_arg = []
                        for inst_arg_part in maybe_args[idx]:
                            if inst_arg_part.startswith("0b"):
                                value = inst_arg_part[2:]
                                inst_arg_part = f"{len(value)}'b{value}"
                            inst_arg.append(inst_arg_part)
                        inst_arg = " ".join(inst_arg)
                    inst_args.append(inst_arg)
                wrap_x_in = "rs2" in inst_args or "rs1" in inst_args
                wrap_x_out = "rd" in inst_args

            # jump check
            ml = re.findall(r"\b(jump_to|set_next_pc|get_next_pc)\(.*\)", line)
            if ml:
                wrap_next_pc = True
            ml = re.findall(r"\b(PC\b|get_arch_pc\(\))", line)
            if ml:
                wrap_pc = True

    # write json
    if name:
        click.echo(f"Writing to {name}.json")
        with open(f"{name}.json", 'wt', encoding='utf-8') as f:
            json.dump({
                "name": name,
                "insn_parts": insn_parts,
                "inst_args": inst_args,
                "wrap_x_in": wrap_x_in,
                "wrap_x_out": wrap_x_out,
                "wrap_pc": wrap_pc,
                "wrap_next_pc": wrap_next_pc,
                "x_upper": x_upper,
                "x_lower": x_lower,
                "r_bits": r_bits,
                "extra_sig1": extra_sig1,
                "extra_sig2": extra_sig2,
                "op_type_enum": op_type_enum,
                "op_values": op_values,
                "op_value_switch": op_value_switch,
                "checker_module": checker_module,
                "opcode": opcode,
            }, f, indent=4)

if __name__ == "__main__":
    configure()
