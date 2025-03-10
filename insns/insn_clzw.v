// DO NOT EDIT -- auto-generated from riscv-formal/insns/generate.py

module rvfi_insn_clzw (
  input                                 rvfi_valid,
  input  [`RISCV_FORMAL_ILEN   - 1 : 0] rvfi_insn,
  input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_pc_rdata,
  input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_rs1_rdata,
  input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_rs2_rdata,
  input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_mem_rdata,
`ifdef RISCV_FORMAL_CSR_MISA
  input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_csr_misa_rdata,
  output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_csr_misa_rmask,
`endif

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
  output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_mem_wdata
);

  // B-type instruction format
  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;
  wire [6:0] insn_funct7 = rvfi_insn[31:25];
  wire [4:0] insn_funct5 = rvfi_insn[24:20];
  wire [4:0] insn_rs1    = rvfi_insn[19:15];
  wire [2:0] insn_funct3 = rvfi_insn[14:12];
  wire [4:0] insn_rd     = rvfi_insn[11: 7];
  wire [6:0] insn_opcode = rvfi_insn[ 6: 0];

`ifdef RISCV_FORMAL_CSR_MISA
  wire misa_ok = (rvfi_csr_misa_rdata & `RISCV_FORMAL_XLEN'h 2) == `RISCV_FORMAL_XLEN'h 2;
  assign spec_csr_misa_rmask = `RISCV_FORMAL_XLEN'h 2;
`else
  wire misa_ok = 1;
`endif

  // CLZW instruction
  integer i;
  reg [31:0] result;
  reg found;
  always @(rvfi_rs1_rdata)
  begin
    result = 0;
    found = 0;
    for (i=0; i<32; i=i+1)
    begin
      if (rvfi_rs1_rdata[i] == 1'b1)
        result = 0;
      else
        result = result + 1;
    end
  end
  assign spec_valid = rvfi_valid && !insn_padding && insn_funct7 == 7'b 0110000 && insn_funct5 == 5'b 00000 && insn_funct3 == 3'b 001 && insn_opcode == 7'b 0011011;
  assign spec_rs1_addr = insn_rs1;
  assign spec_rd_addr = insn_rd;
  assign spec_rd_wdata = spec_rd_addr ? {{`RISCV_FORMAL_XLEN-32{result[31]}}, result} : 0;
  assign spec_pc_wdata = rvfi_pc_rdata + 4;

  // default assignments
  assign spec_rs2_addr = 0;
  assign spec_trap = !misa_ok;
  assign spec_mem_addr = 0;
  assign spec_mem_rmask = 0;
  assign spec_mem_wmask = 0;
  assign spec_mem_wdata = 0;
endmodule
