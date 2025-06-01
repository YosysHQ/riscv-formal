// DO NOT EDIT -- auto-generated from riscv-formal/insns/generate.py

module rvfi_insn_ctz (
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

  // I-type instruction format (ZBB variation)
  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;
  wire [6:0] insn_funct7 = rvfi_insn[31:25];
  wire [5:0] insn_funct5 = rvfi_insn[24:20];
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

  // CTZ instruction
  wire [`RISCV_FORMAL_XLEN-1:0] result = ctz32(rvfi_rs1_rdata);
 
    function logic [31:0] clz32(logic [31:0] x);
        logic [31:0] r;
        casez(x)
        32'b1zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz: r =  0;
        32'b01zzzzzzzzzzzzzzzzzzzzzzzzzzzzzz: r =  1;
        32'b001zzzzzzzzzzzzzzzzzzzzzzzzzzzzz: r =  2;
        32'b0001zzzzzzzzzzzzzzzzzzzzzzzzzzzz: r =  3;
        32'b00001zzzzzzzzzzzzzzzzzzzzzzzzzzz: r =  4;
        32'b000001zzzzzzzzzzzzzzzzzzzzzzzzzz: r =  5;
        32'b0000001zzzzzzzzzzzzzzzzzzzzzzzzz: r =  6;
        32'b00000001zzzzzzzzzzzzzzzzzzzzzzzz: r =  7;
        32'b000000001zzzzzzzzzzzzzzzzzzzzzzz: r =  8;
        32'b0000000001zzzzzzzzzzzzzzzzzzzzzz: r =  9;
        32'b00000000001zzzzzzzzzzzzzzzzzzzzz: r = 10;
        32'b000000000001zzzzzzzzzzzzzzzzzzzz: r = 11;
        32'b0000000000001zzzzzzzzzzzzzzzzzzz: r = 12;
        32'b00000000000001zzzzzzzzzzzzzzzzzz: r = 13;
        32'b000000000000001zzzzzzzzzzzzzzzzz: r = 14;
        32'b0000000000000001zzzzzzzzzzzzzzzz: r = 15;
        32'b00000000000000001zzzzzzzzzzzzzzz: r = 16;
        32'b000000000000000001zzzzzzzzzzzzzz: r = 17;
        32'b0000000000000000001zzzzzzzzzzzzz: r = 18;
        32'b00000000000000000001zzzzzzzzzzzz: r = 19;
        32'b000000000000000000001zzzzzzzzzzz: r = 20;
        32'b0000000000000000000001zzzzzzzzzz: r = 21;
        32'b00000000000000000000001zzzzzzzzz: r = 22;
        32'b000000000000000000000001zzzzzzzz: r = 23;
        32'b0000000000000000000000001zzzzzzz: r = 24;
        32'b00000000000000000000000001zzzzzz: r = 25;
        32'b000000000000000000000000001zzzzz: r = 26;
        32'b0000000000000000000000000001zzzz: r = 27;
        32'b00000000000000000000000000001zzz: r = 28;
        32'b000000000000000000000000000001zz: r = 29;
        32'b0000000000000000000000000000001z: r = 30;
        32'b00000000000000000000000000000001: r = 31;
        32'b00000000000000000000000000000000: r = 32;
        endcase
        clz32 = r;
    endfunction

    function logic [31:0] ctz32(logic [31:0] x);
        logic [31:0] inv;
        
        for(int i = 0; i < 32; i++)
            inv[i] = x[31 - i];
            
        ctz32 = clz32(inv);
    endfunction

  assign spec_valid = rvfi_valid && !insn_padding && insn_funct7 == 7'b 0110000 && insn_funct5 == 5'b 00001 && insn_funct3 == 3'b 001 && insn_opcode == 7'b 0010011;
  assign spec_rs1_addr = insn_rs1;
  assign spec_rd_addr = insn_rd;
  assign spec_rd_wdata = spec_rd_addr ? result : 0;
  assign spec_pc_wdata = rvfi_pc_rdata + 4;

  // default assignments
  assign spec_rs2_addr = 0;
  assign spec_trap = !misa_ok;
  assign spec_mem_addr = 0;
  assign spec_mem_rmask = 0;
  assign spec_mem_wmask = 0;
  assign spec_mem_wdata = 0;
endmodule
