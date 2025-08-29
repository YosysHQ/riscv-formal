#!/usr/bin/env python3

from dataclasses import dataclass, field, asdict
import json
import textwrap
from typing import Optional, Any

import json_fix

def skip_empty_factory(mapping: list[tuple[str, Any]]) -> dict:
    """dictionary factory which skips empty values"""
    result = {}
    for key, val in mapping:
        if isinstance(val, bool):
            result[key] = val
        elif val:
            # skip falsy non-boolean values
            result[key] = val
    return result


@dataclass
class Instruction_format:
    name: Optional[str] = None
    insn_parts: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class Instruction:
    name: str
    insn_parts: list[tuple[str, int]]
    opcode: str
    
    result: Optional[str] = None
    extension: Optional[str] = None
    alt_add: Optional[str] = None
    alt_sub: Optional[str] = None
    shamt: Optional[bool] = None
    sign_extend_from: Optional[int] = None
    zero_extend_from: Optional[int] = None
    
    op_values: dict[str, str] | list[tuple[str, str | list[str], str | list[str]]] = field(default_factory=dict)
    raw_code: list[str] = field(default_factory=list)
    spec_map: dict[str, str] = field(default_factory=dict)
    xlen_min: int = 32
    xlen_max: int = 128

    # sail fields
    inst_args: Optional[list[str]] = None
    wrap_x_in: Optional[bool] = None
    wrap_x_out: Optional[bool] = None
    wrap_pc: Optional[bool] = None
    wrap_next_pc: Optional[bool] = None
    x_upper: Optional[int] = None
    x_lower: Optional[int] = None
    r_bits: Optional[int] = None
    extra_sig1: list[tuple[str, str, str]] = field(default_factory=list)
    extra_sig2: list[tuple[str, str, str]] = field(default_factory=list)
    op_name: str | list[str] = "op"
    op_type_enum: Optional[str | list[str]] = None
    op_value_switch: Optional[str] = None
    checker_module: Optional[str] = None

    def _process_insn_parts(self):
        self._insn_part_dict = dict(self.insn_parts)
        self._insn_part_keys = [k for k, _ in self.insn_parts]
        if self.inst_args is None:
            self.inst_args = self._insn_part_keys

    def _config_used_regs(self):
        self._maybe_sources = ["rs2", "rs1"]
        self._maybe_dests = ["rd"]
        self._used_regs = []
        for maybe_reg in self._maybe_sources + self._maybe_dests:
            if maybe_reg in self.inst_args:
                self._used_regs.append(maybe_reg)

    def _config_widths(self):
        self._result_width = self.sign_extend_from or self.zero_extend_from

    def _inject_altops(self):
        # altops injection
        if self.alt_add:
            alt_mask = int(self.alt_add, base=16)
            alt_op = "+"
        elif self.alt_sub:
            alt_mask = int(self.alt_sub, base=16)
            alt_op = "-"
        else:
            alt_mask = None
        if alt_mask:
            self.result = f"(rvfi_rs1_rdata {alt_op} rvfi_rs2_rdata) ^ 64'h{alt_mask:016x}"

    def __post_init__(self):
        self._process_insn_parts()
        self._config_used_regs()
        self._config_widths()
        self._inject_altops()

    @classmethod
    def from_json(cls, s: str):
        mapping = json.loads(s)
        return cls(**mapping)

    def __json__(self, skip_empty: bool = True) -> dict:
        if skip_empty:
            return asdict(self, dict_factory=skip_empty_factory)
        else:
            return asdict(self)

    def to_json(self, skip_empty: bool = True, indent: int | str | None = None) -> str:
        return json.dumps(self.__json__(skip_empty), indent=indent)

    def _v_xlen_check(self, xlen) -> None:
        # check valid xlen
        if xlen < self.xlen_min or xlen > self.xlen_max:
            raise NotImplementedError(f"{xlen} not in range ({self.xlen_min}, {self.xlen_max})")

    def _v_modname(self) -> str:
        # module name
        return f"rvfi_insn_{self.name}"

    def _v_io(self) -> str:
        # rvfi_insn_check.sv compliant io
        return textwrap.dedent("""\
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

    def _v_insn_fmt(self, ilen: int) -> str:
        # insn decode
        upper = ilen
        insn_format = "// instruction format\n"
        for part, width in self.insn_parts:
            lower = upper - width
            insn_format += f"wire [{width-1:2d}:0] insn_{part:<6} = rvfi_insn[{upper-1:2d}:{lower:2d}];\n"
            upper = lower
        if upper != 0:
            raise NotImplementedError(f"{upper} instruction bits unhandled")

        return insn_format

    def _v_inst_check(self) -> None:
        # check instance map
        inst_args_avail = self._insn_part_keys + [self.op_name]
        for inst_arg in self.inst_args:
            for arg_part in inst_arg.split():
                if arg_part not in inst_args_avail and not arg_part[0].isdigit():
                    raise NotImplementedError()

    def _v_reg_wrap(self, xlen: int) -> str:
        # wrap registers
        if self.x_upper and self.x_lower:
            x_type = f"logic [{xlen-1}:0]"
            x_range = f"[{self.x_upper}:{self.x_lower}]"
            reg_wrap = "// register wrapping\n"
            for x_inout, do_wrap in [("x_in", self.wrap_x_in), ("x_out", self.wrap_x_out)]:
                if do_wrap:
                    reg_wrap += f"{x_type} {x_inout}{x_range};\n"

            # address fixing
            localparams = []
            x_assigns = []
            #todo: multiple destination regs
            result_decl = ""
            for idx, used_reg in enumerate(self._used_regs, start=1):
                raddr = f"{used_reg}_0"
                localparams.append(f"{raddr} = {self.r_bits}'d{idx}")
                if used_reg in self._maybe_sources and self.wrap_x_in:
                    x_assigns.append(f"assign x_in[{raddr}] = rvfi_{used_reg}_rdata;")
                if used_reg in self._maybe_dests and self.wrap_x_out:
                    result_decl = f"wire [{xlen-1}:0] result = x_out[{raddr}];\n"
            if localparams:
                localparams = ", ".join(localparams)
                reg_wrap += f"localparam {localparams};\n"
            if x_assigns:
                reg_wrap += "\n".join(x_assigns) + "\n"
            reg_wrap += result_decl

            if self.wrap_next_pc:
                reg_wrap += f"wire [{xlen-1}:0] next_pc = rvfi_pc_rdata + 4;\n"
            return reg_wrap
        else:
            return ""


    def _v_extra_sigs(self) -> str:
        # extra signals
        if self.extra_sig1 or self.extra_sig2:
            extra_signals = "// extra signals\n"
            extra_signal_decls = self.extra_sig1 + self.extra_sig2
            if isinstance(self.op_name, str):
                op_default = self.op_values[0][1] if len(self.op_values) == 1 else None
                extra_signal_decls.append((self.op_type_enum, f"{self.op_name}_0", op_default))
            for t, n, v in extra_signal_decls:
                extra_signals += f"{t} {n};\n" if v == None else f"{t} {n} = {v};\n"
            return extra_signals
        else:
            return ""


    def _v_insn_map(self, xlen: int) -> str:
        # combined instruction mapping
        insn_map = "// insn map\n"

        # shamt
        if self.shamt:
            result_width = self._result_width or xlen
            shift_width = (result_width-1).bit_length()
            insn_map += f"wire [{shift_width-1}:0] shamt = rvfi_rs2_rdata[{shift_width-1}:0];\n"

        if isinstance(self.op_values, list):
            if isinstance(self.op_name, list):
                for name, type_enum in zip(self.op_name, self.op_type_enum):
                    insn_map += f"{type_enum} {name}_0;\n"
                
                op_value_keys = self.op_name
            else:
                op_value_keys = self.op_value_switch.split()

            if len(op_value_keys) == 1:
                case_switch = f"insn_{self.op_value_switch}"
            else:
                case_switch = '{' + ', '.join([f"insn_{k}" for k in op_value_keys]) + '}'
            op_value_bits = sum([self._insn_part_dict[k] for k in op_value_keys])
            if len(self.op_values) == 1:
                insn_map += f"wire illinsn = {case_switch} != {op_value_bits}'b {self.op_values[0][0]};\n"
            else:
                insn_map += textwrap.dedent(f"""\
                    reg illinsn;
                    always @* begin
                        illinsn <= 0;
                        case ({case_switch})
                """)
                # click.echo("Found instructions: ", nl=False)
                if isinstance(self.op_name, list):
                    for mnemonic, part_type_values, part_values in self.op_values:
                        # click.echo(f"{mnemonic} ", nl=False)
                        var_name = '{' + ', '.join(f"{name}_0" for name in self.op_name) + '}'
                        value = ''.join(part_values)
                        enum = '{' + ', '.join(part_type_values) + '}'
                        insn_map += f"        {op_value_bits}'b {value}: {var_name} <= {enum};\n"
                else:
                    for mnemonic, enum, value in self.op_values:
                        # click.echo(f"{mnemonic} ", nl=False)
                        insn_map += f"        {op_value_bits}'b {value}: {self.op_name}_0 <= {enum};\n"
                # click.echo("")
                insn_map += textwrap.dedent(f"""\
                            default: illinsn <= 1;
                        endcase
                    end
                """)
        elif isinstance(self.op_values, dict):
            insn_map += f"wire illinsn = "
            op_value_checks = []
            for key, bin in self.op_values.items():
                op_value_bits = self._insn_part_dict[key]
                op_value_checks.append(f"(insn_{key} != {op_value_bits}'b {bin})")
            insn_map += " || ".join(op_value_checks) + ";"
        else:
            raise NotImplementedError(type(self.op_values))

        return insn_map

    def _v_instantiation(self, xlen) -> str:
        # wrapped checker
        if self.checker_module:
            instantiation = f"// {self.name} instance\n"
            checker_args: list[str] = []
            for inst_arg in self.inst_args:
                if (inst_arg in self._used_regs
                    or isinstance(self.op_name, str) and inst_arg == self.op_name
                    or isinstance(self.op_name, list) and inst_arg in self.op_name
                    ):
                    checker_arg = f"{inst_arg}_0"
                elif " " in inst_arg:
                    arg_parts = [k if k[0].isdigit() else f"insn_{k}" for k in inst_arg.split()]
                    checker_arg = '{' + ', '.join(arg_parts) + '}'
                else:
                    checker_arg = f"insn_{inst_arg}"
                if checker_arg: checker_args.append(checker_arg)
            if self.wrap_pc:
                checker_args.append(f"rvfi_pc_rdata")
            if self.wrap_next_pc:
                checker_args.append(f"next_pc")
            if self.wrap_x_in:
                for idx in range(self.x_lower, self.x_upper + 1):
                    checker_args.append(f"x_in[{idx}]")
            for _, extra_sig, _ in self.extra_sig1:
                checker_args.append(extra_sig)
            if self.wrap_x_out:
                for idx in range(self.x_lower, self.x_upper + 1):
                    checker_args.append(f"x_out[{idx}]")
            if self.wrap_next_pc:
                checker_args.append("spec_pc_wdata")
            for _, extra_sig, _ in self.extra_sig2:
                checker_args.append(extra_sig)

            instantiation += f"{self.checker_module} wrapped_checker("
            instantiation += ", ".join(checker_args)
            instantiation += ");\n"
        else:
            instantiation = ""

        # raw code injection
        if self.raw_code:
            instantiation += "\n".join(self.raw_code) + "\n"
        if self.result:
            instantiation += f"wire [{(self._result_width or xlen)-1}:0] result = {self.result};\n"

        return instantiation

    def _v_spec_mapping(self) -> str:
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
        for spec_sig in self.spec_map.keys():
            if spec_sig not in spec_sigs:
                raise NotImplementedError(f"spec_sig {spec_sig}")

        for used_reg in self._used_regs:
            self.spec_map[f"{used_reg}_addr"] = f"insn_{used_reg}"
            if used_reg in self._maybe_dests:
                self.spec_map[f"{used_reg}_wdata"] = f"spec_{used_reg}_addr ? result : 0"

        for spec_sig in spec_sigs:
            if spec_sig not in self.spec_map:
                if spec_sig == "pc_wdata":
                    val = "rvfi_pc_rdata + 4"
                elif spec_sig == "valid":
                    val = f"rvfi_valid && !illinsn && insn_opcode == 7'b {self.opcode}"
                else:
                    val = "0"
                self.spec_map[spec_sig] = val

        if self.wrap_next_pc:
            self.spec_map.pop("pc_wdata")

        for spec_sig, spec_val in self.spec_map.items():
            spec_mapping += f"assign spec_{spec_sig} = {spec_val};\n"

        return spec_mapping

    def _v_format_block(self, s: str) -> str:
        return textwrap.indent(s, '    ') + '\n'

    def to_verilog(self, xlen: int = 32, ilen: int = 32) -> str:
        self._v_xlen_check(xlen)
        self._v_inst_check()
        v_str = f"module {self._v_modname()} (\n{self._v_format_block(self._v_io())});\n\n"
        v_str += self._v_format_block(self._v_insn_fmt(ilen))
        reg_wrap = self._v_reg_wrap(xlen)
        if reg_wrap: v_str += self._v_format_block(reg_wrap)
        extra_signals = self._v_extra_sigs()
        if extra_signals: v_str += self._v_format_block(extra_signals)
        v_str += self._v_format_block(self._v_insn_map(xlen))
        v_str += self._v_format_block(self._v_instantiation(xlen))
        v_str += self._v_format_block(self._v_spec_mapping())
        v_str += "endmodule"
        return v_str
