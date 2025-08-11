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
    with open(cfg, 'r', encoding='utf-8') as f:
        cfg_json = json.load(f)

    name: str = cfg_json['name']
    insn_parts: list[tuple[str, int]] = cfg_json['insn_parts']
    inst_args: list[str] = cfg_json['inst_args']
    wrap_in: bool = cfg_json['wrap_in']
    wrap_out: bool = cfg_json['wrap_out']
    x_upper: int = cfg_json['x_upper']
    x_lower: int = cfg_json['x_lower']
    r_bits: int = cfg_json['r_bits']
    extra_sig1: list[tuple[str, str, str]] = cfg_json['extra_sig1']
    extra_sig2: list[tuple[str, str, str]] = cfg_json['extra_sig2']
    op_type_enum: str = cfg_json['op_type_enum']
    op_values: list[tuple[str, str]] = cfg_json['op_values']
    op_value_switch: str = cfg_json['op_value_switch']
    checker_module: str = cfg_json['checker_module']
    opcode: str = cfg_json['opcode']

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

    # check instance map
    inst_args_avail = list(insn_parts_dict.keys()) + ["op"]
    for inst_arg in inst_args:
        assert (inst_arg in inst_args_avail)

    # wrap registers
    x_type = f"logic [{XLEN-1}:0]"
    x_range = f"[{x_upper}:{x_lower}]"
    reg_wrap = "// register wrapping\n"
    for x_inout, do_wrap in [("x_in", wrap_in), ("x_out", wrap_out)]:
        if do_wrap:
            reg_wrap += f"{x_type} {x_inout}{x_range};\n"

    maybe_sources = ["rs2", "rs1"]
    maybe_dests = ["rd"]
    used_regs = []
    for maybe_reg in maybe_sources + maybe_dests:
        if maybe_reg in inst_args:
            used_regs.append(maybe_reg)
    
    # address fixing
    localparams = []
    x_assigns = []
    #todo: multiple destination regs
    result_decl = ""
    for idx, used_reg in enumerate(used_regs, start=1):
        raddr = f"{used_reg}_0"
        localparams.append(f"{raddr} = {r_bits}'d{idx}")
        if used_reg in maybe_sources and wrap_in:
            x_assigns.append(f"assign x_in[{raddr}] = rvfi_{used_reg}_rdata;")
        if used_reg in maybe_dests and wrap_out:
            result_decl = f"wire [{XLEN-1}:0] result = x_out[{raddr}];\n"
    if localparams:
        localparams = ", ".join(localparams)
        reg_wrap += f"localparam {localparams};\n"
    if x_assigns:
        reg_wrap += "\n".join(x_assigns) + "\n"
    reg_wrap += result_decl

    # extra signals
    extra_signals = "// extra signals\n"
    op_default = op_values[0][1] if len(op_values) == 1 else None
    extra_signal_decls = extra_sig1 + extra_sig2 + [(op_type_enum, "op_0", op_default)]
    for t, n, v in extra_signal_decls:
        extra_signals += f"{t} {n};\n" if v == None else f"{t} {n} = {v};\n"

    # combined instruction checking
    op_value_keys = op_value_switch.split()
    op_value_bits = sum([insn_parts_dict[k] for k in op_value_keys])
    insn_check = "// insn check\n"
    if len(op_values) == 1:
        insn_check += f"wire illinsn = {op_value_bits}'b {op_values[0][0]};\n"
    else:
        if len(op_value_keys) == 1:
            case_switch = f"insn_{op_value_switch}"
        else:
            case_switch = '{' + ', '.join([f"insn_{k}" for k in op_value_keys]) + '}'
        insn_check += dedent(f"""\
            reg illinsn;
            always @* begin
                illinsn <= 0;
                case ({case_switch})
        """)
        for bin, enum in op_values:
            insn_check += f"        {op_value_bits}'b {bin}: op_0 <= {enum};\n"
        insn_check += dedent(f"""\
                    default: illinsn <= 1;
                endcase
            end
        """)

    # wrapped checker
    instantiation = f"// {name} instance\n"
    checker_args: list[str] = []
    for inst_arg in inst_args:
        if inst_arg in used_regs:
            checker_arg = f"{inst_arg}_0"
        elif inst_arg == "op":
            checker_arg = "op_0"
        else:
            checker_arg = f"insn_{inst_arg}"
        if checker_arg: checker_args.append(checker_arg)
    if wrap_in:
        for idx in range(x_lower, x_upper + 1):
            checker_args.append(f"x_in[{idx}]")
    for _, extra_sig, _ in extra_sig1:
        checker_args.append(extra_sig)
    if wrap_out:
        for idx in range(x_lower, x_upper + 1):
            checker_args.append(f"x_out[{idx}]")
    for _, extra_sig, _ in extra_sig2:
        checker_args.append(extra_sig)

    instantiation += f"{checker_module} wrapped_checker("
    instantiation += ", ".join(checker_args)
    instantiation += ");\n"

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
    spec_map = {k: "0" for k in spec_sigs}

    spec_map["valid"] = f"rvfi_valid && !illinsn && insn_opcode == 7'b {opcode}"

    for used_reg in used_regs:
        spec_map[f"{used_reg}_addr"] = f"insn_{used_reg}"
        if used_reg in maybe_dests:
            spec_map[f"{used_reg}_wdata"] = f"spec_{used_reg}_addr ? result : 0"

    spec_map["pc_wdata"] = "rvfi_pc_rdata + 4"

    for spec_sig, spec_val in spec_map.items():
        spec_mapping += f"assign spec_{spec_sig} = {spec_val};\n"

    # write out to file
    with open(out_file, 'wt', encoding='utf-8') as f:
        click.echo(f"module {mod} (", file=f)
        click.echo(insn_check_io, file=f)
        click.echo(");\n", file=f)
        click.echo(indent(insn_format, '    '), file=f)
        click.echo(indent(reg_wrap, '    '), file=f)
        click.echo(indent(extra_signals, '    '), file=f)
        click.echo(indent(insn_check, '    '), file=f)
        click.echo(indent(instantiation, '    '), file=f)
        click.echo(indent(spec_mapping, '    '), file=f)
        click.echo("endmodule", file=f)

if __name__ == '__main__':
    wrap()
