from dataclasses import dataclass, field, asdict
import json
from textwrap import dedent
from typing import Optional, Any

import json_fix

from ..checks import GenericChecker

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


@dataclass(kw_only=True)
class Instruction(GenericChecker):
    insn_parts: list[tuple[str, int]]
    opcode: str
    
    result: Optional[str] = None
    extension: Optional[str] = None
    alt_add: Optional[str] = None
    alt_sub: Optional[str] = None
    shamt: Optional[bool] = None
    sign_extend_from: Optional[int] = None
    zero_extend_from: Optional[int] = None
    
    op_values: dict[str, str] = field(default_factory=dict)
    raw_code: list[str] = field(default_factory=list)
    spec_map: dict[str, str] = field(default_factory=dict)
    check_valid: list[str] = field(default_factory=list)
    xlen_min: int = 32
    xlen_max: int = 128

    inst_args: Optional[list[str]] = None
    wrap_next_pc: Optional[bool] = None

    def _insn_fixup(self):
        if isinstance(self.insn_parts, Instruction_format):
            self.insn_parts = self.insn_parts.insn_parts

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

    def _altops_fixup(self):
        for alt_var in ["alt_add", "alt_sub"]:
            alt_val = self.__getattribute__(alt_var)
            if isinstance(alt_val, int):
                self.__dict__[alt_var] = hex(alt_val)

    def __post_init__(self):
        self._insn_fixup()
        self._process_insn_parts()
        self._config_used_regs()
        self._config_widths()
        self._altops_fixup()

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

    def _v_io(self) -> str:
        # rvfi_insn_check.sv compliant io
        return dedent("""\
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

    def _v_insn_map(self, xlen: int) -> str:
        # combined instruction mapping
        insn_map = "// insn map\n"

        # shamt
        if self.shamt:
            result_width = self._result_width or xlen
            shift_width = (result_width-1).bit_length()
            insn_map += f"wire [{shift_width-1}:0] shamt = rvfi_rs2_rdata[{shift_width-1}:0];\n"

        insn_map += f"wire illinsn = "
        op_value_checks = []
        for key, bin in self.op_values.items():
            op_value_bits = self._insn_part_dict[key]
            try:
                int(bin, 2)
                bin_str = f"{op_value_bits}'b {bin}"
            except ValueError:
                bin_str = bin
            op_value_checks.append(f"(insn_{key} != {bin_str})")
        insn_map += " || ".join(op_value_checks) + ";"

        return insn_map

    def _v_instantiation(self, xlen: int) -> str:
        instantiation = ""

        # altops injection
        if self.alt_add:
            alt_mask = self.alt_add
            alt_op = "+"
        elif self.alt_sub:
            alt_mask = self.alt_sub
            alt_op = "-"
        else:
            alt_mask = None

        if isinstance(alt_mask, str):
            alt_mask = int(alt_mask, 16)

        if alt_mask:
            result = f"(rvfi_rs1_rdata {alt_op} rvfi_rs2_rdata) ^ 64'h{alt_mask:016x}"
        else:
            result = self.result

        # raw code injection
        result_width = self._result_width or xlen
        for code_line in self.raw_code:
            code_line = code_line.replace("%RESULT_WIDTH%", str(result_width))
            instantiation += code_line + "\n"
        if result:
            instantiation += f"wire [{result_width-1}:0] result = {result};\n"

        return instantiation

    def _v_spec_mapping(self, xlen: int) -> str:
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
                extend_from = self.sign_extend_from or self.zero_extend_from or 0
                if extend_from:
                    funct = "signed" if self.sign_extend_from else "unsigned"
                    result = f"${funct}(result[0+:{extend_from}])"
                else:
                    result = "result"
                self.spec_map[f"{used_reg}_wdata"] = f"spec_{used_reg}_addr ? {result} : 0"

        for spec_sig in spec_sigs:
            if spec_sig not in self.spec_map:
                if spec_sig == "pc_wdata":
                    val = "rvfi_pc_rdata + 4"
                elif spec_sig == "valid":
                    try:
                        int(self.opcode, 2)
                        opcode = f"7'b {self.opcode}"
                    except ValueError:
                        opcode = self.opcode
                    val = f"rvfi_valid && !illinsn && insn_opcode == {opcode}"
                    for check in self.check_valid:
                        val += f" && ({check})"
                else:
                    val = "0"
                self.spec_map[spec_sig] = val

        if self.wrap_next_pc:
            self.spec_map.pop("pc_wdata")

        for spec_sig, spec_val in self.spec_map.items():
            spec_mapping += f"assign spec_{spec_sig} = {spec_val};\n"

        return spec_mapping

    def _v_checks(self, xlen: int, ilen: int) -> None:
        super()._v_checks()
        self._v_xlen_check(xlen)

    def _v_body(self, xlen: int, ilen: int) -> str:
        v_str = self._v_format_block(self._v_insn_fmt(ilen))
        v_str += self._v_format_block(self._v_insn_map(xlen))
        v_str += self._v_format_block(self._v_instantiation(xlen))
        v_str += self._v_format_block(self._v_spec_mapping(xlen))
        return v_str

    def to_verilog(self, xlen: int, ilen: int):
        return super().to_verilog(xlen=xlen, ilen=ilen)
