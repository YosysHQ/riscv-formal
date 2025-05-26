// DO NOT EDIT -- auto-generated from riscv-formal/insns/generate.py

module rvfi_isa_rv32iZbc (
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
  wire                                spec_insn_clmul_valid;
  wire                                spec_insn_clmul_trap;
  wire [                       4 : 0] spec_insn_clmul_rs1_addr;
  wire [                       4 : 0] spec_insn_clmul_rs2_addr;
  wire [                       4 : 0] spec_insn_clmul_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmul_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmul_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmul_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_clmul_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_clmul_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmul_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmul_csr_misa_rmask;
`endif

  rvfi_insn_clmul insn_clmul (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_clmul_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_clmul_valid),
    .spec_trap(spec_insn_clmul_trap),
    .spec_rs1_addr(spec_insn_clmul_rs1_addr),
    .spec_rs2_addr(spec_insn_clmul_rs2_addr),
    .spec_rd_addr(spec_insn_clmul_rd_addr),
    .spec_rd_wdata(spec_insn_clmul_rd_wdata),
    .spec_pc_wdata(spec_insn_clmul_pc_wdata),
    .spec_mem_addr(spec_insn_clmul_mem_addr),
    .spec_mem_rmask(spec_insn_clmul_mem_rmask),
    .spec_mem_wmask(spec_insn_clmul_mem_wmask),
    .spec_mem_wdata(spec_insn_clmul_mem_wdata)
  );

  wire                                spec_insn_clmulh_valid;
  wire                                spec_insn_clmulh_trap;
  wire [                       4 : 0] spec_insn_clmulh_rs1_addr;
  wire [                       4 : 0] spec_insn_clmulh_rs2_addr;
  wire [                       4 : 0] spec_insn_clmulh_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmulh_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmulh_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmulh_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_clmulh_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_clmulh_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmulh_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmulh_csr_misa_rmask;
`endif

  rvfi_insn_clmulh insn_clmulh (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_clmulh_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_clmulh_valid),
    .spec_trap(spec_insn_clmulh_trap),
    .spec_rs1_addr(spec_insn_clmulh_rs1_addr),
    .spec_rs2_addr(spec_insn_clmulh_rs2_addr),
    .spec_rd_addr(spec_insn_clmulh_rd_addr),
    .spec_rd_wdata(spec_insn_clmulh_rd_wdata),
    .spec_pc_wdata(spec_insn_clmulh_pc_wdata),
    .spec_mem_addr(spec_insn_clmulh_mem_addr),
    .spec_mem_rmask(spec_insn_clmulh_mem_rmask),
    .spec_mem_wmask(spec_insn_clmulh_mem_wmask),
    .spec_mem_wdata(spec_insn_clmulh_mem_wdata)
  );

  wire                                spec_insn_clmulr_valid;
  wire                                spec_insn_clmulr_trap;
  wire [                       4 : 0] spec_insn_clmulr_rs1_addr;
  wire [                       4 : 0] spec_insn_clmulr_rs2_addr;
  wire [                       4 : 0] spec_insn_clmulr_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmulr_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmulr_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmulr_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_clmulr_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_clmulr_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmulr_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clmulr_csr_misa_rmask;
`endif

  rvfi_insn_clmulr insn_clmulr (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_clmulr_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_clmulr_valid),
    .spec_trap(spec_insn_clmulr_trap),
    .spec_rs1_addr(spec_insn_clmulr_rs1_addr),
    .spec_rs2_addr(spec_insn_clmulr_rs2_addr),
    .spec_rd_addr(spec_insn_clmulr_rd_addr),
    .spec_rd_wdata(spec_insn_clmulr_rd_wdata),
    .spec_pc_wdata(spec_insn_clmulr_pc_wdata),
    .spec_mem_addr(spec_insn_clmulr_mem_addr),
    .spec_mem_rmask(spec_insn_clmulr_mem_rmask),
    .spec_mem_wmask(spec_insn_clmulr_mem_wmask),
    .spec_mem_wdata(spec_insn_clmulr_mem_wdata)
  );

  assign spec_valid =
		spec_insn_clmul_valid ? spec_insn_clmul_valid :
		spec_insn_clmulh_valid ? spec_insn_clmulh_valid :
		spec_insn_clmulr_valid ? spec_insn_clmulr_valid : 0;
  assign spec_trap =
		spec_insn_clmul_valid ? spec_insn_clmul_trap :
		spec_insn_clmulh_valid ? spec_insn_clmulh_trap :
		spec_insn_clmulr_valid ? spec_insn_clmulr_trap : 0;
  assign spec_rs1_addr =
		spec_insn_clmul_valid ? spec_insn_clmul_rs1_addr :
		spec_insn_clmulh_valid ? spec_insn_clmulh_rs1_addr :
		spec_insn_clmulr_valid ? spec_insn_clmulr_rs1_addr : 0;
  assign spec_rs2_addr =
		spec_insn_clmul_valid ? spec_insn_clmul_rs2_addr :
		spec_insn_clmulh_valid ? spec_insn_clmulh_rs2_addr :
		spec_insn_clmulr_valid ? spec_insn_clmulr_rs2_addr : 0;
  assign spec_rd_addr =
		spec_insn_clmul_valid ? spec_insn_clmul_rd_addr :
		spec_insn_clmulh_valid ? spec_insn_clmulh_rd_addr :
		spec_insn_clmulr_valid ? spec_insn_clmulr_rd_addr : 0;
  assign spec_rd_wdata =
		spec_insn_clmul_valid ? spec_insn_clmul_rd_wdata :
		spec_insn_clmulh_valid ? spec_insn_clmulh_rd_wdata :
		spec_insn_clmulr_valid ? spec_insn_clmulr_rd_wdata : 0;
  assign spec_pc_wdata =
		spec_insn_clmul_valid ? spec_insn_clmul_pc_wdata :
		spec_insn_clmulh_valid ? spec_insn_clmulh_pc_wdata :
		spec_insn_clmulr_valid ? spec_insn_clmulr_pc_wdata : 0;
  assign spec_mem_addr =
		spec_insn_clmul_valid ? spec_insn_clmul_mem_addr :
		spec_insn_clmulh_valid ? spec_insn_clmulh_mem_addr :
		spec_insn_clmulr_valid ? spec_insn_clmulr_mem_addr : 0;
  assign spec_mem_rmask =
		spec_insn_clmul_valid ? spec_insn_clmul_mem_rmask :
		spec_insn_clmulh_valid ? spec_insn_clmulh_mem_rmask :
		spec_insn_clmulr_valid ? spec_insn_clmulr_mem_rmask : 0;
  assign spec_mem_wmask =
		spec_insn_clmul_valid ? spec_insn_clmul_mem_wmask :
		spec_insn_clmulh_valid ? spec_insn_clmulh_mem_wmask :
		spec_insn_clmulr_valid ? spec_insn_clmulr_mem_wmask : 0;
  assign spec_mem_wdata =
		spec_insn_clmul_valid ? spec_insn_clmul_mem_wdata :
		spec_insn_clmulh_valid ? spec_insn_clmulh_mem_wdata :
		spec_insn_clmulr_valid ? spec_insn_clmulr_mem_wdata : 0;
`ifdef RISCV_FORMAL_CSR_MISA
  assign spec_csr_misa_rmask =
		spec_insn_clmul_valid ? spec_insn_clmul_csr_misa_rmask :
		spec_insn_clmulh_valid ? spec_insn_clmulh_csr_misa_rmask :
		spec_insn_clmulr_valid ? spec_insn_clmulr_csr_misa_rmask : 0;
`endif
endmodule
