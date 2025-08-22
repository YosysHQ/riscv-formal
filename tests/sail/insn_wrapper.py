"""insn_wrapper"""
from pathlib import Path
from textwrap import dedent, indent
import click
import json

ILEN = 32
XLEN = 32

@click.command()
@click.option('-f', '--force', is_flag=True)
@click.argument('cfg', type=click.Path(exists=True, path_type=Path))
def wrap(force: bool, cfg: Path):
    """main function"""
    # load cfg
    click.echo(f"Loading from {cfg}")
    with open(cfg, 'r', encoding='utf-8') as f:
        cfg_json: dict[str] = json.load(f)

    name: str = cfg_json.pop('name')
    insn_parts: list[tuple[str, int]] = cfg_json.pop('insn_parts')
    extension: str = cfg_json.pop('extension', "I")
    xlen_min: int = cfg_json.pop('xlen_min', 32)
    xlen_max: int = cfg_json.pop('xlen_max', 128)
    xlen: int = cfg_json.pop('xlen', None)
    inst_args: list[str] = cfg_json.pop('inst_args', None)
    wrap_x_in: bool = cfg_json.pop('wrap_x_in', False)
    wrap_x_out: bool = cfg_json.pop('wrap_x_out', False)
    wrap_pc: bool = cfg_json.pop('wrap_pc', False)
    wrap_next_pc: bool = cfg_json.pop('wrap_next_pc', False)
    x_upper: int = cfg_json.pop('x_upper', None)
    x_lower: int = cfg_json.pop('x_lower', None)
    r_bits: int = cfg_json.pop('r_bits', None)
    extra_sig1: list[tuple[str, str, str]] = cfg_json.pop('extra_sig1', [])
    extra_sig2: list[tuple[str, str, str]] = cfg_json.pop('extra_sig2', [])
    op_name: str | list[str] = cfg_json.pop('op_name', "op")
    op_type_enum: str | list[str] = cfg_json.pop('op_type_enum', None)
    op_values: list[tuple[str, str | list[str], str | list[str]]] | dict[str, str] = cfg_json.pop('op_values')
    op_value_switch: str = cfg_json.pop('op_value_switch', None)
    checker_module: str = cfg_json.pop('checker_module', None)
    opcode: str = cfg_json.pop('opcode')
    raw_code: list[str] = cfg_json.pop('raw_code', [])
    result: str = cfg_json.pop('result', None)
    alt_add: str = cfg_json.pop('alt_add', None)
    alt_sub: str = cfg_json.pop('alt_sub', None)
    spec_map: dict[str, str] = cfg_json.pop('spec_map', {})

    for key in cfg_json.keys():
        raise NotImplementedError(key)

    # combined min/max
    if xlen:
        xlen_min = xlen
        xlen_max = xlen

    # check valid xlen
    if XLEN < xlen_min or XLEN > xlen_max:
        raise NotImplementedError(f"{XLEN} not in range ({xlen_min}, {xlen_max})")

    # get output file
    out_file = Path(f"{name}_wrapper.sv")
    if out_file.exists() and not force:
        raise FileExistsError(out_file)

    # module name
    mod = f"rvfi_insn_{name}"

    # rvfi_insn_check.sv compliant io
    insn_check_io = dedent("""\
        input                                 rvfi_valid,
        input  [`RISCV_FORMAL_ILEN   - 1 : 0] rvfi_insn,
        input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_pc_rdata,
        input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_rs1_rdata,
        input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_rs2_rdata,
        input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_mem_rdata,

        output                                spec_valid,
        output                                spec_trap,
        output [                       4 : 0] spec_rs1_addr,
        output [                       4 : 0] spec_rs2_addr,
        output [                       4 : 0] spec_rd_addr,
        output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_rd_wdata,
        output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_pc_wdata,
        output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_mem_addr,
        output [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_mem_rmask,
        output [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_mem_wmask,
        output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_mem_wdata""")

    # insn decode
    insn_parts_dict = dict(insn_parts)
    upper = ILEN
    insn_format = "// instruction format\n"
    for part, width in insn_parts:
        lower = upper - width
        insn_format += f"wire [{width-1:2d}:0] insn_{part:<6} = rvfi_insn[{upper-1:2d}:{lower:2d}];\n"
        upper = lower
    assert(upper == 0)

    # register checks
    insn_part_keys = list(insn_parts_dict.keys())
    if inst_args is None:
        inst_args = insn_part_keys

    maybe_sources = ["rs2", "rs1"]
    maybe_dests = ["rd"]
    used_regs = []
    for maybe_reg in maybe_sources + maybe_dests:
        if maybe_reg in inst_args:
            used_regs.append(maybe_reg)

    # check instance map
    inst_args_avail = insn_part_keys + [op_name]
    for inst_arg in inst_args:
        for arg_part in inst_arg.split():
            assert (arg_part in inst_args_avail or arg_part[0].isdigit())

    # wrap registers
    if x_upper and x_lower:
        x_type = f"logic [{XLEN-1}:0]"
        x_range = f"[{x_upper}:{x_lower}]"
        reg_wrap = "// register wrapping\n"
        for x_inout, do_wrap in [("x_in", wrap_x_in), ("x_out", wrap_x_out)]:
            if do_wrap:
                reg_wrap += f"{x_type} {x_inout}{x_range};\n"

        # address fixing
        localparams = []
        x_assigns = []
        #todo: multiple destination regs
        result_decl = ""
        for idx, used_reg in enumerate(used_regs, start=1):
            raddr = f"{used_reg}_0"
            localparams.append(f"{raddr} = {r_bits}'d{idx}")
            if used_reg in maybe_sources and wrap_x_in:
                x_assigns.append(f"assign x_in[{raddr}] = rvfi_{used_reg}_rdata;")
            if used_reg in maybe_dests and wrap_x_out:
                result_decl = f"wire [{XLEN-1}:0] result = x_out[{raddr}];\n"
        if localparams:
            localparams = ", ".join(localparams)
            reg_wrap += f"localparam {localparams};\n"
        if x_assigns:
            reg_wrap += "\n".join(x_assigns) + "\n"
        reg_wrap += result_decl

        if wrap_next_pc:
            reg_wrap += f"wire [{XLEN-1}:0] next_pc = rvfi_pc_rdata + 4;\n"
    else:
        reg_wrap = ""

    # extra signals
    if extra_sig1 or extra_sig2:
        extra_signals = "// extra signals\n"
        extra_signal_decls = extra_sig1 + extra_sig2
        if isinstance(op_name, str):
            op_default = op_values[0][1] if len(op_values) == 1 else None
            extra_signal_decls.append((op_type_enum, f"{op_name}_0", op_default))
        for t, n, v in extra_signal_decls:
            extra_signals += f"{t} {n};\n" if v == None else f"{t} {n} = {v};\n"
    else:
        extra_signals = ""

    # combined instruction checking
    insn_check = "// insn check\n"
    if isinstance(op_values, list):
        if isinstance(op_name, list):
            for name, type_enum in zip(op_name, op_type_enum):
                insn_check += f"{type_enum} {name}_0;\n"
            
            op_value_keys = op_name
        else:
            op_value_keys = op_value_switch.split()

        if len(op_value_keys) == 1:
            case_switch = f"insn_{op_value_switch}"
        else:
            case_switch = '{' + ', '.join([f"insn_{k}" for k in op_value_keys]) + '}'
        op_value_bits = sum([insn_parts_dict[k] for k in op_value_keys])
        if len(op_values) == 1:
            insn_check += f"wire illinsn = {case_switch} != {op_value_bits}'b {op_values[0][0]};\n"
        else:
            insn_check += dedent(f"""\
                reg illinsn;
                always @* begin
                    illinsn <= 0;
                    case ({case_switch})
            """)
            click.echo("Found instructions: ", nl=False)
            if isinstance(op_name, list):
                for mnemonic, part_type_values, part_values in op_values:
                    click.echo(f"{mnemonic} ", nl=False)
                    var_name = '{' + ', '.join(f"{name}_0" for name in op_name) + '}'
                    value = ''.join(part_values)
                    enum = '{' + ', '.join(part_type_values) + '}'
                    insn_check += f"        {op_value_bits}'b {value}: {var_name} <= {enum};\n"
            else:
                for mnemonic, enum, value in op_values:
                    click.echo(f"{mnemonic} ", nl=False)
                    insn_check += f"        {op_value_bits}'b {value}: {op_name}_0 <= {enum};\n"
            click.echo("")
            insn_check += dedent(f"""\
                        default: illinsn <= 1;
                    endcase
                end
            """)
    elif isinstance(op_values, dict):
        insn_check += f"wire illinsn = "
        op_value_checks = []
        for key, bin in op_values.items():
            op_value_bits = insn_parts_dict[key]
            op_value_checks.append(f"(insn_{key} != {op_value_bits}'b {bin})")
        insn_check += " || ".join(op_value_checks) + ";"
    else:
        raise NotImplementedError(type(op_values))

    # wrapped checker
    if checker_module:
        instantiation = f"// {name} instance\n"
        checker_args: list[str] = []
        for inst_arg in inst_args:
            if (inst_arg in used_regs
                or isinstance(op_name, str) and inst_arg == op_name
                or isinstance(op_name, list) and inst_arg in op_name
                ):
                checker_arg = f"{inst_arg}_0"
            elif " " in inst_arg:
                arg_parts = [k if k[0].isdigit() else f"insn_{k}" for k in inst_arg.split()]
                checker_arg = '{' + ', '.join(arg_parts) + '}'
            else:
                checker_arg = f"insn_{inst_arg}"
            if checker_arg: checker_args.append(checker_arg)
        if wrap_pc:
            checker_args.append(f"rvfi_pc_rdata")
        if wrap_next_pc:
            checker_args.append(f"next_pc")
        if wrap_x_in:
            for idx in range(x_lower, x_upper + 1):
                checker_args.append(f"x_in[{idx}]")
        for _, extra_sig, _ in extra_sig1:
            checker_args.append(extra_sig)
        if wrap_x_out:
            for idx in range(x_lower, x_upper + 1):
                checker_args.append(f"x_out[{idx}]")
        if wrap_next_pc:
            checker_args.append("spec_pc_wdata")
        for _, extra_sig, _ in extra_sig2:
            checker_args.append(extra_sig)

        instantiation += f"{checker_module} wrapped_checker("
        instantiation += ", ".join(checker_args)
        instantiation += ");\n"
    else:
        instantiation = ""

    # altops injection
    if alt_add:
        alt_mask = int(alt_add, base=16)
        alt_op = "+"
    elif alt_sub:
        alt_mask = int(alt_sub, base=16)
        alt_op = "-"
    if alt_mask:
        result = f"(rvfi_rs1_rdata {alt_op} rvfi_rs2_rdata) ^ 64'h{alt_mask:016x}"

    # raw code injection
    if raw_code:
        instantiation += "\n".join(raw_code) + "\n"
    if result:
        instantiation += f"wire [{XLEN-1}:0] result = {result};\n"

    # map spec values
    spec_mapping = "// spec mapping\n"
    spec_sigs = [
        "valid",
        "rs2_addr",
        "rs1_addr",
        "rd_addr",
        "rd_wdata",
        "pc_wdata",
        "trap",
        "mem_addr",
        "mem_rmask",
        "mem_wmask",
        "mem_wdata",
    ]
    for spec_sig in spec_map.keys():
        if spec_sig not in spec_sigs:
            raise NotImplementedError(f"spec_sig {spec_sig}")

    for used_reg in used_regs:
        spec_map[f"{used_reg}_addr"] = f"insn_{used_reg}"
        if used_reg in maybe_dests:
            spec_map[f"{used_reg}_wdata"] = f"spec_{used_reg}_addr ? result : 0"

    for spec_sig in spec_sigs:
        if spec_sig not in spec_map:
            if spec_sig == "pc_wdata":
                val = "rvfi_pc_rdata + 4"
            elif spec_sig == "valid":
                val = f"rvfi_valid && !illinsn && insn_opcode == 7'b {opcode}"
            else:
                val = "0"
            spec_map[spec_sig] = val

    if wrap_next_pc:
        spec_map.pop("pc_wdata")

    for spec_sig, spec_val in spec_map.items():
        spec_mapping += f"assign spec_{spec_sig} = {spec_val};\n"

    # write out to file
    with open(out_file, 'wt', encoding='utf-8') as f:
        click.echo(f"module {mod} (", file=f)
        click.echo(insn_check_io, file=f)
        click.echo(");\n", file=f)
        click.echo(indent(insn_format, '    '), file=f)
        if reg_wrap: click.echo(indent(reg_wrap, '    '), file=f)
        if extra_signals: click.echo(indent(extra_signals, '    '), file=f)
        click.echo(indent(insn_check, '    '), file=f)
        click.echo(indent(instantiation, '    '), file=f)
        click.echo(indent(spec_mapping, '    '), file=f)
        click.echo("endmodule", file=f)

if __name__ == '__main__':
    wrap()
