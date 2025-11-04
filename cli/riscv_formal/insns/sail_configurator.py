"""configure instruction checker from sail"""
from dataclasses import dataclass, field
from typing import Optional
from itertools import product
import json
from pathlib import Path
import re
import click

from .model import Instruction_format
from .wrapped_model import WrappedInstruction
from riscv_formal.named_set import NamedClass, NamedSet

@dataclass
class SailParseHelper(NamedClass):
    op_type: str
    arg_types: list[str] = field(default_factory=list)
    maybe_args: list[str | list[str]] = field(default_factory=list)
    arg_remap: set[str] = field(default_factory=set)


@dataclass
class SailEncdecHelper(NamedClass):
    op_bits: Optional[int] = None
    enum_value_map: dict[str, str] = field(default_factory=dict)
    op_values: list[tuple[str, str, str]] = field(default_factory=list)


def check_wrapped_insn(insn: WrappedInstruction) -> None:
    if insn.op_values_list:
        mnemonics = [mnemonic for mnemonic, _, _ in insn.op_values_list]
    else:
        mnemonics = [insn.name]
    click.echo(f"{insn.checker_module} -> {mnemonics}")
    if insn.opcode == "":
        if isinstance(insn.insn_parts, Instruction_format):
            raise NotImplementedError(insn.insn_parts)
        part_name, part_size = insn.insn_parts.pop()
        if part_name != "part_0" or part_size != 7:
            raise NotImplementedError((part_name, part_size))
        insn.insn_parts.append(("opcode", 7))
        insn.op_value_switch = "opcode"
    insn._process_insn_parts()

@click.command()
@click.argument('sail', type=click.Path(exists=True, path_type=Path))
@click.argument('out_file', type=click.Path(path_type=Path))
def configure(sail: Path, out_file: Path):
    """main function"""

    # load sail
    in_encdec_op: Optional[str] = None
    in_encdec_insn: Optional[str] = None
    in_execute: Optional[str] = None
    in_mnemonic: Optional[str] = None
    in_assembly: Optional[str] = None

    sail_parse_helpers: NamedSet[SailParseHelper] = NamedSet()
    sail_encdec_helpers: NamedSet[SailEncdecHelper] = NamedSet()
    sail_executors: NamedSet[WrappedInstruction] = NamedSet()

    with open(sail, 'rt', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            # instruction type def
            m = re.match(r"union clause instruction = (?P<insn>\w+) : (?:\((?P<arg_types>.*)\)|unit)", line)
            if m:
                d = m.groupdict()
                if d['arg_types'] is not None:
                    arg_types: list[str] = d['arg_types'].split(", ")
                    op_type = arg_types[-1] if "op" in arg_types[-1] else None
                else:
                    arg_types = ["unit"]
                    op_type = None

                sail_parse_helpers.add(SailParseHelper(
                    name = d['insn'],
                    arg_types = arg_types,
                    op_type = op_type or d['insn'],
                ))
                sail_executors.add(WrappedInstruction(
                    name = d['insn'].lower(),
                    insn_parts = [],
                    opcode = "",
                    checker_module = f"execute_{d['insn']}",   
                    extra_sig1 = [
                        ("t_ExecutionResult", "sail_return_2", None),
                    ],
                    extra_sig2 = [
                        ("bit", "sail_have_exception_2", None),
                        ("t_exception", "sail_current_exception_2", None),
                    ],
                ))

            # op encoding
            m = re.match(r"mapping encdec_(?P<op_type>\w+) : (?P=op_type) <-> bits\((?P<op_bits>\d+)\) = {", line)
            if m:
                d = m.groupdict()
                in_encdec_op = d['op_type']
                sail_encdec_helpers.add(SailEncdecHelper(
                    name = d['op_type'],
                    op_bits = int(d['op_bits']),
                ))
            if in_encdec_op:
                m = re.match(r"\s+(.*?)\s+<-> 0b([01]+),?", line)
                if line == "}":
                    in_encdec_op = None
                elif m:
                    x, y = m.groups()
                    sail_encdec_helpers[in_encdec_op].enum_value_map[x] = y

            # instruction decoding
            m = re.match(r"mapping clause encdec = (?P<insn>\w+)\((?P<args>.*)\)(?:$|\s+<-> .*)", line)
            mapping = None
            if m:
                d = m.groupdict()
                parsed = sail_parse_helpers[d['insn']]
                parsed.maybe_args = []
                for maybe_arg in d['args'].split(", "):
                    if "@" in maybe_arg:
                        parsed.maybe_args.append(maybe_arg.split(" @ "))
                    else:
                        parsed.maybe_args.append(maybe_arg)
                in_encdec_insn = d['insn']
            if in_encdec_insn:
                m = (re.match(r"\s+<-> (?P<mapping>.*)", line) or 
                     re.match(r"(.*\s+<-> (?P<mapping>.*))", line))
                if m:
                    mapping = m.groupdict()['mapping']
            if in_encdec_insn and mapping:
                parsed = sail_parse_helpers[in_encdec_insn]
                insn = sail_executors[in_encdec_insn.lower()]
                parts = mapping.split(" @ ")
                maybe_opcode = parts[-1]
                if maybe_opcode.startswith("0b") and len(maybe_opcode) == 9:
                    insn.opcode = maybe_opcode[2:]
                    parts[-1] = "opcode"
                part_idx = 0
                if isinstance(insn.insn_parts, Instruction_format):
                    raise NotImplementedError()
                has_insn_parts = len(insn.insn_parts) != 0
                binary_parts: list[str] = []
                binary_part_names: list[str] = []
                for part in parts:
                    known_funcs = ["encdec_reg", "bool_bits", "width_enc"]
                    m = re.match(r"(\w+)\((\w+)\)", part)
                    if m and m.group(1) in known_funcs: part = m.group(2)
                    try:
                        idx = parsed.maybe_args.index(part)
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
                        elif part.startswith(f"encdec_"):
                            m = re.match(r"encdec_(?P<op_type>\w+)\(\w+\)", part)
                            if m is None:
                                raise NotImplementedError(part)
                            d = m.groupdict()
                            encdec = sail_encdec_helpers[d['op_type']]
                            if isinstance(encdec.op_bits, int):
                                part_size = encdec.op_bits
                            else:
                                raise NotImplementedError(encdec.op_bits)
                            part = f"part_{part_idx}"
                            part_idx += 1
                            insn.op_value_switch = part
                        else:
                            m = re.match(r"((\w+?)_?[\d_]+) : bits\((\d+)\)", part)
                            if m is None:
                                raise NotImplementedError(part)
                            part, arg_name, part_size = m.groups()
                            part_size = int(part_size)
                            parsed.arg_remap.add(arg_name)
                    else:
                        arg_type = parsed.arg_types[idx]
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
                            raise NotImplementedError()
                    else:
                        insn.insn_parts.append(insn_part)
                if binary_parts:
                    # assumes the op is the last arg
                    try:
                        encdec = sail_encdec_helpers[parsed.op_type]
                    except KeyError:
                        encdec = SailEncdecHelper(parsed.op_type)
                        sail_encdec_helpers.add(encdec)
                    enum_value = parsed.maybe_args[-1]
                    if isinstance(enum_value, list):
                        raise NotImplementedError(enum_value)
                    encdec.enum_value_map[enum_value] = "_".join(binary_parts)
                    insn.op_value_switch = " ".join(binary_part_names)
                    insn.op_type_enum = f"t_{parsed.op_type}"
                in_encdec_insn = None

            # instruction args
            m = re.match(r"function clause execute \((?P<insn>\w+)\s?\((?P<args>.*)\)\) = {", line)
            if m:
                d = m.groupdict()
                in_execute = d['insn']
                parsed = sail_parse_helpers[d['insn']]
                insn = sail_executors[d['insn'].lower()]
                insn.inst_args = []
                for idx, inst_arg in enumerate(d['args'].split(', ')):
                    if inst_arg in parsed.arg_remap:
                        inst_arg = []
                        for inst_arg_part in parsed.maybe_args[idx]:
                            if inst_arg_part.startswith("0b"):
                                value = inst_arg_part[2:]
                                inst_arg_part = f"{len(value)}'b{value}"
                            inst_arg.append(inst_arg_part)
                        inst_arg = " ".join(inst_arg)
                    elif parsed.arg_types[idx] in sail_encdec_helpers:
                        parsed.op_type = parsed.arg_types[idx]
                        insn.op_name = inst_arg
                        insn.op_type_enum = f"t_{parsed.op_type}"
                    insn.inst_args.append(inst_arg)
                insn.wrap_x_in = "rs2" in insn.inst_args or "rs1" in insn.inst_args
                insn.wrap_x_out = "rd" in insn.inst_args
            if in_execute:
                if line == "}":
                    in_execute = None
                else:
                    insn = sail_executors[in_execute.lower()]
                    # jump check
                    ml = re.findall(r"\b(jump_to|set_next_pc|get_next_pc)\(.*\)", line)
                    if ml:
                        insn.wrap_next_pc = True
                    ml = re.findall(r"\b(PC\b|get_arch_pc\(\))", line)
                    if ml:
                        insn.wrap_pc = True

            # mnemonic mapping
            m = re.match(r"mapping (?P<prefix>\w+)_mnemonic(?P<suffix>_\w+)? : (?P<op_type>\w+) <-> string = {", line)
            if m:
                d = m.groupdict()
                in_mnemonic = d['op_type']
            if in_mnemonic:
                m = re.match(r"\s+(?P<enum_value>.*?)\s+<-> \"(?P<mnemonic>\w+)\",?", line)
                if line == "}":
                    in_mnemonic = None
                elif m:
                    d = m.groupdict()
                    try:
                        encdec = sail_encdec_helpers[in_mnemonic]
                    except KeyError:
                        encdec = SailEncdecHelper(in_mnemonic)
                        sail_encdec_helpers.add(encdec)
                    value = encdec.enum_value_map.get(d['enum_value'])
                    if value is None:
                        raise NotImplementedError(d['enum_value'])
                    # convert mul_op to verilog struct
                    # e.g. struct { high = false, signed_rs1 = true,  signed_rs2 = true  }
                    # becomes {0, 1, 1}
                    if d['enum_value'].startswith("struct"):
                        d['enum_value'] = "{" + ", ".join(value) + "}"
                    encdec.op_values.append((d['mnemonic'], d['enum_value'], value))

            # assembly mapping as backup for mnemonic
            m = re.match(r"mapping clause assembly = (?P<insn>\w+)\s?\((?P<args>.*)\)", line)
            if m:
                d = m.groupdict()
                parsed = sail_parse_helpers[d['insn']]
                insn = sail_executors[d['insn'].lower()]
                if parsed.op_type is not None and parsed.op_type in sail_encdec_helpers:
                    insn.op_values_list.extend(sail_encdec_helpers[parsed.op_type].op_values)
                if insn.op_values_list:
                    check_wrapped_insn(insn)
                else:
                    in_assembly = d['insn']
            if in_assembly:
                insn = sail_executors[in_assembly.lower()]
                m = re.match(r".*\s+<-> (?P<mapping>.*?)(?: \^ spc\(\)|$)", line)
                if m:
                    mapping = m.groupdict()['mapping']
                    parts = mapping.split(" ^ ")
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
                    mnemonic_parts: list[list[str] | list[tuple[str, str, str]]] = []
                    mnemonic_keys: list[str] = []
                    mnemonic_types: list[str] = []
                    for part in parts:
                        if re.match(r"\"(\S+)\"", part):
                            mnemonic_parts.append([part[1:-1]])
                        else:
                            m = re.match(r"(\w+)\((\w+)\)", part)
                            if m and m.group(1) in known_funcs:
                                func, key = m.groups()
                                mnemonic_type, mnemonic_part = known_funcs[func]
                                mnemonic_parts.append(mnemonic_part)
                                mnemonic_keys.append(key)
                                mnemonic_types.append(mnemonic_type)
                            else:
                                raise NotImplementedError(f"assembly {in_assembly!r} part {part}")
                    mnemonic_products = list(product(*mnemonic_parts))
                    single_mnemonic = len(mnemonic_products) == 1
                    for prod in mnemonic_products:
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
                        if not single_mnemonic:
                            insn.op_values_list.append((mnemonic, args, bits))
                        elif args or bits:
                            raise NotImplementedError(f"assembly {in_assembly!r} {args} {bits}")
                    if single_mnemonic:
                        insn.name = mnemonic # type: ignore
                        parsed = sail_parse_helpers[in_assembly]
                        encdec = sail_encdec_helpers.get(parsed.op_type)
                        if insn.op_value_switch is not None and encdec:
                            if len(encdec.enum_value_map) > 1:
                                raise NotImplementedError()
                            binary_part_names = insn.op_value_switch.split()
                            binary_parts = encdec.enum_value_map.popitem()[1].split("_")
                            insn.op_values = dict(zip(binary_part_names, binary_parts))
                        elif insn.op_value_switch or encdec:
                            raise NotImplementedError()
                        insn.op_name = None
                        insn.op_type_enum = None
                        insn.op_value_switch = None
                    else:
                        insn.op_name = mnemonic_keys
                        insn.op_type_enum = mnemonic_types
                        insn.op_value_switch = None
                    check_wrapped_insn(insn)
                    in_assembly = None

    # write json
    click.echo(f"Writing to {out_file}")
    with open(out_file, 'wt', encoding='utf-8') as f:
        json.dump(sail_executors, f, indent=4)

if __name__ == "__main__":
    configure()
