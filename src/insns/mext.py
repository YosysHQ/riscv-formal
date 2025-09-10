from dataclasses import dataclass
from typing import Optional

from .model import AltopsInstruction
from .builtins import FORMAT_R

@dataclass(kw_only=True)
class M_Instruction(AltopsInstruction):
    alt_add: Optional[str] = None
    alt_sub: Optional[str] = None

    def _alt_vars(self):
        return ["alt_add", "alt_sub"]

    def _get_alt_result_and_mask(self):
        if self.alt_add:
            alt_mask = self.alt_add
            alt_op = "+"
        elif self.alt_sub:
            alt_mask = self.alt_sub
            alt_op = "-"
        else:
            alt_mask = None

        if alt_mask:
            return (f"rvfi_rs1_rdata {alt_op} rvfi_rs2_rdata", alt_mask)
        else:
            return None


def m_insn(insn, funct7, funct3, expr, alt_add=None, alt_sub=None, wmode=False, extension="M"):
    return M_Instruction(
        name = insn,
        insn_parts = FORMAT_R,
        opcode = "0111011" if wmode else "0110011",
        result = expr,
        extension = extension,
        alt_add = alt_add,
        alt_sub = alt_sub,
        sign_extend_from = 32 if wmode else None,
        xlen_min = 64 if wmode else 32,
        op_values = {
            "funct7": funct7,
            "funct3": funct3,
        },
    )


def mext() -> dict[str, M_Instruction]:
    return {i.name: i for i in [
        m_insn("mul",    "0000001", "000", "rvfi_rs1_rdata * rvfi_rs2_rdata", alt_add=0x2cdf52a55876063e),
        m_insn("mulh",   "0000001", "001", "({{`RISCV_FORMAL_XLEN{rvfi_rs1_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs1_rdata} *\n" +
                "\t\t{{`RISCV_FORMAL_XLEN{rvfi_rs2_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_add=0x15d01651f6583fb7),
        m_insn("mulhsu", "0000001", "010", "({{`RISCV_FORMAL_XLEN{rvfi_rs1_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs1_rdata} *\n" +
                "\t\t{`RISCV_FORMAL_XLEN'b0, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_sub=0xea3969edecfbe137),
        m_insn("mulhu",  "0000001", "011", "({`RISCV_FORMAL_XLEN'b0, rvfi_rs1_rdata} * {`RISCV_FORMAL_XLEN'b0, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_add=0xd13db50d949ce5e8),

        m_insn("div",    "0000001", "100", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? {`RISCV_FORMAL_XLEN{1'b1}} :
                                              rvfi_rs1_rdata == {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} && rvfi_rs2_rdata == {`RISCV_FORMAL_XLEN{1'b1}} ? {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} :
                                              $signed(rvfi_rs1_rdata) / $signed(rvfi_rs2_rdata)""", alt_sub=0x29bbf66f7f8529ec),
        m_insn("divu",   "0000001", "101", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? {`RISCV_FORMAL_XLEN{1'b1}} :
                                              rvfi_rs1_rdata / rvfi_rs2_rdata""", alt_sub=0x8c629acb10e8fd70),

        m_insn("rem",    "0000001", "110", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? rvfi_rs1_rdata :
                                              rvfi_rs1_rdata == {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} && rvfi_rs2_rdata == {`RISCV_FORMAL_XLEN{1'b1}} ? {`RISCV_FORMAL_XLEN{1'b0}} :
                                              $signed(rvfi_rs1_rdata) % $signed(rvfi_rs2_rdata)""", alt_sub=0xf5b7d8538da68fa5),
        m_insn("remu",   "0000001", "111", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? rvfi_rs1_rdata :
                                              rvfi_rs1_rdata % rvfi_rs2_rdata""", alt_sub=0xbc4402413138d0e1),

        m_insn("mulw",   "0000001", "000", "rvfi_rs1_rdata[31:0] * rvfi_rs2_rdata[31:0]", alt_add=0x2cdf52a55876063e, wmode=True),

        m_insn("divw",   "0000001", "100", """rvfi_rs2_rdata[31:0] == 32'b0 ? {32{1'b1}} :
                                              rvfi_rs1_rdata == {1'b1, {31{1'b0}}} && rvfi_rs2_rdata == {32{1'b1}} ? {1'b1, {31{1'b0}}} :
                                              $signed(rvfi_rs1_rdata[31:0]) / $signed(rvfi_rs2_rdata[31:0])""", alt_sub=0x29bbf66f7f8529ec, wmode=True),
        m_insn("divuw",  "0000001", "101", """rvfi_rs2_rdata[31:0] == 32'b0 ? {32{1'b1}} :
                                              rvfi_rs1_rdata[31:0] / rvfi_rs2_rdata[31:0]""", alt_sub=0x8c629acb10e8fd70, wmode=True),

        m_insn("remw",   "0000001", "110", """rvfi_rs2_rdata == 32'b0 ? rvfi_rs1_rdata :
                                              rvfi_rs1_rdata == {1'b1, {31{1'b0}}} && rvfi_rs2_rdata == {32{1'b1}} ? {32{1'b0}} :
                                              $signed(rvfi_rs1_rdata[31:0]) % $signed(rvfi_rs2_rdata[31:0])""", alt_sub=0xf5b7d8538da68fa5, wmode=True),
        m_insn("remuw",  "0000001", "111", """rvfi_rs2_rdata == 32'b0 ? rvfi_rs1_rdata :
                                              rvfi_rs1_rdata[31:0] % rvfi_rs2_rdata[31:0]""", alt_sub=0xbc4402413138d0e1, wmode=True),
    ]}
