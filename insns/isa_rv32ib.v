// DO NOT EDIT -- auto-generated from riscv-formal/insns/generate.py

module rvfi_isa_rv32ib (
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
  wire                                spec_insn_andn_valid;
  wire                                spec_insn_andn_trap;
  wire [                       4 : 0] spec_insn_andn_rs1_addr;
  wire [                       4 : 0] spec_insn_andn_rs2_addr;
  wire [                       4 : 0] spec_insn_andn_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_andn_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_andn_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_andn_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_andn_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_andn_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_andn_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_andn_csr_misa_rmask;
`endif

  rvfi_insn_andn insn_andn (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_andn_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_andn_valid),
    .spec_trap(spec_insn_andn_trap),
    .spec_rs1_addr(spec_insn_andn_rs1_addr),
    .spec_rs2_addr(spec_insn_andn_rs2_addr),
    .spec_rd_addr(spec_insn_andn_rd_addr),
    .spec_rd_wdata(spec_insn_andn_rd_wdata),
    .spec_pc_wdata(spec_insn_andn_pc_wdata),
    .spec_mem_addr(spec_insn_andn_mem_addr),
    .spec_mem_rmask(spec_insn_andn_mem_rmask),
    .spec_mem_wmask(spec_insn_andn_mem_wmask),
    .spec_mem_wdata(spec_insn_andn_mem_wdata)
  );

  wire                                spec_insn_bclr_valid;
  wire                                spec_insn_bclr_trap;
  wire [                       4 : 0] spec_insn_bclr_rs1_addr;
  wire [                       4 : 0] spec_insn_bclr_rs2_addr;
  wire [                       4 : 0] spec_insn_bclr_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bclr_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bclr_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bclr_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bclr_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bclr_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bclr_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bclr_csr_misa_rmask;
`endif

  rvfi_insn_bclr insn_bclr (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_bclr_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_bclr_valid),
    .spec_trap(spec_insn_bclr_trap),
    .spec_rs1_addr(spec_insn_bclr_rs1_addr),
    .spec_rs2_addr(spec_insn_bclr_rs2_addr),
    .spec_rd_addr(spec_insn_bclr_rd_addr),
    .spec_rd_wdata(spec_insn_bclr_rd_wdata),
    .spec_pc_wdata(spec_insn_bclr_pc_wdata),
    .spec_mem_addr(spec_insn_bclr_mem_addr),
    .spec_mem_rmask(spec_insn_bclr_mem_rmask),
    .spec_mem_wmask(spec_insn_bclr_mem_wmask),
    .spec_mem_wdata(spec_insn_bclr_mem_wdata)
  );

  wire                                spec_insn_bclri_valid;
  wire                                spec_insn_bclri_trap;
  wire [                       4 : 0] spec_insn_bclri_rs1_addr;
  wire [                       4 : 0] spec_insn_bclri_rs2_addr;
  wire [                       4 : 0] spec_insn_bclri_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bclri_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bclri_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bclri_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bclri_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bclri_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bclri_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bclri_csr_misa_rmask;
`endif

  rvfi_insn_bclri insn_bclri (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_bclri_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_bclri_valid),
    .spec_trap(spec_insn_bclri_trap),
    .spec_rs1_addr(spec_insn_bclri_rs1_addr),
    .spec_rs2_addr(spec_insn_bclri_rs2_addr),
    .spec_rd_addr(spec_insn_bclri_rd_addr),
    .spec_rd_wdata(spec_insn_bclri_rd_wdata),
    .spec_pc_wdata(spec_insn_bclri_pc_wdata),
    .spec_mem_addr(spec_insn_bclri_mem_addr),
    .spec_mem_rmask(spec_insn_bclri_mem_rmask),
    .spec_mem_wmask(spec_insn_bclri_mem_wmask),
    .spec_mem_wdata(spec_insn_bclri_mem_wdata)
  );

  wire                                spec_insn_bext_valid;
  wire                                spec_insn_bext_trap;
  wire [                       4 : 0] spec_insn_bext_rs1_addr;
  wire [                       4 : 0] spec_insn_bext_rs2_addr;
  wire [                       4 : 0] spec_insn_bext_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bext_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bext_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bext_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bext_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bext_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bext_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bext_csr_misa_rmask;
`endif

  rvfi_insn_bext insn_bext (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_bext_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_bext_valid),
    .spec_trap(spec_insn_bext_trap),
    .spec_rs1_addr(spec_insn_bext_rs1_addr),
    .spec_rs2_addr(spec_insn_bext_rs2_addr),
    .spec_rd_addr(spec_insn_bext_rd_addr),
    .spec_rd_wdata(spec_insn_bext_rd_wdata),
    .spec_pc_wdata(spec_insn_bext_pc_wdata),
    .spec_mem_addr(spec_insn_bext_mem_addr),
    .spec_mem_rmask(spec_insn_bext_mem_rmask),
    .spec_mem_wmask(spec_insn_bext_mem_wmask),
    .spec_mem_wdata(spec_insn_bext_mem_wdata)
  );

  wire                                spec_insn_bexti_valid;
  wire                                spec_insn_bexti_trap;
  wire [                       4 : 0] spec_insn_bexti_rs1_addr;
  wire [                       4 : 0] spec_insn_bexti_rs2_addr;
  wire [                       4 : 0] spec_insn_bexti_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bexti_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bexti_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bexti_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bexti_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bexti_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bexti_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bexti_csr_misa_rmask;
`endif

  rvfi_insn_bexti insn_bexti (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_bexti_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_bexti_valid),
    .spec_trap(spec_insn_bexti_trap),
    .spec_rs1_addr(spec_insn_bexti_rs1_addr),
    .spec_rs2_addr(spec_insn_bexti_rs2_addr),
    .spec_rd_addr(spec_insn_bexti_rd_addr),
    .spec_rd_wdata(spec_insn_bexti_rd_wdata),
    .spec_pc_wdata(spec_insn_bexti_pc_wdata),
    .spec_mem_addr(spec_insn_bexti_mem_addr),
    .spec_mem_rmask(spec_insn_bexti_mem_rmask),
    .spec_mem_wmask(spec_insn_bexti_mem_wmask),
    .spec_mem_wdata(spec_insn_bexti_mem_wdata)
  );

  wire                                spec_insn_binv_valid;
  wire                                spec_insn_binv_trap;
  wire [                       4 : 0] spec_insn_binv_rs1_addr;
  wire [                       4 : 0] spec_insn_binv_rs2_addr;
  wire [                       4 : 0] spec_insn_binv_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_binv_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_binv_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_binv_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_binv_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_binv_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_binv_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_binv_csr_misa_rmask;
`endif

  rvfi_insn_binv insn_binv (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_binv_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_binv_valid),
    .spec_trap(spec_insn_binv_trap),
    .spec_rs1_addr(spec_insn_binv_rs1_addr),
    .spec_rs2_addr(spec_insn_binv_rs2_addr),
    .spec_rd_addr(spec_insn_binv_rd_addr),
    .spec_rd_wdata(spec_insn_binv_rd_wdata),
    .spec_pc_wdata(spec_insn_binv_pc_wdata),
    .spec_mem_addr(spec_insn_binv_mem_addr),
    .spec_mem_rmask(spec_insn_binv_mem_rmask),
    .spec_mem_wmask(spec_insn_binv_mem_wmask),
    .spec_mem_wdata(spec_insn_binv_mem_wdata)
  );

  wire                                spec_insn_binvi_valid;
  wire                                spec_insn_binvi_trap;
  wire [                       4 : 0] spec_insn_binvi_rs1_addr;
  wire [                       4 : 0] spec_insn_binvi_rs2_addr;
  wire [                       4 : 0] spec_insn_binvi_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_binvi_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_binvi_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_binvi_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_binvi_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_binvi_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_binvi_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_binvi_csr_misa_rmask;
`endif

  rvfi_insn_binvi insn_binvi (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_binvi_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_binvi_valid),
    .spec_trap(spec_insn_binvi_trap),
    .spec_rs1_addr(spec_insn_binvi_rs1_addr),
    .spec_rs2_addr(spec_insn_binvi_rs2_addr),
    .spec_rd_addr(spec_insn_binvi_rd_addr),
    .spec_rd_wdata(spec_insn_binvi_rd_wdata),
    .spec_pc_wdata(spec_insn_binvi_pc_wdata),
    .spec_mem_addr(spec_insn_binvi_mem_addr),
    .spec_mem_rmask(spec_insn_binvi_mem_rmask),
    .spec_mem_wmask(spec_insn_binvi_mem_wmask),
    .spec_mem_wdata(spec_insn_binvi_mem_wdata)
  );

  wire                                spec_insn_bset_valid;
  wire                                spec_insn_bset_trap;
  wire [                       4 : 0] spec_insn_bset_rs1_addr;
  wire [                       4 : 0] spec_insn_bset_rs2_addr;
  wire [                       4 : 0] spec_insn_bset_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bset_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bset_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bset_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bset_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bset_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bset_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bset_csr_misa_rmask;
`endif

  rvfi_insn_bset insn_bset (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_bset_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_bset_valid),
    .spec_trap(spec_insn_bset_trap),
    .spec_rs1_addr(spec_insn_bset_rs1_addr),
    .spec_rs2_addr(spec_insn_bset_rs2_addr),
    .spec_rd_addr(spec_insn_bset_rd_addr),
    .spec_rd_wdata(spec_insn_bset_rd_wdata),
    .spec_pc_wdata(spec_insn_bset_pc_wdata),
    .spec_mem_addr(spec_insn_bset_mem_addr),
    .spec_mem_rmask(spec_insn_bset_mem_rmask),
    .spec_mem_wmask(spec_insn_bset_mem_wmask),
    .spec_mem_wdata(spec_insn_bset_mem_wdata)
  );

  wire                                spec_insn_bseti_valid;
  wire                                spec_insn_bseti_trap;
  wire [                       4 : 0] spec_insn_bseti_rs1_addr;
  wire [                       4 : 0] spec_insn_bseti_rs2_addr;
  wire [                       4 : 0] spec_insn_bseti_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bseti_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bseti_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bseti_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bseti_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_bseti_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bseti_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_bseti_csr_misa_rmask;
`endif

  rvfi_insn_bseti insn_bseti (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_bseti_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_bseti_valid),
    .spec_trap(spec_insn_bseti_trap),
    .spec_rs1_addr(spec_insn_bseti_rs1_addr),
    .spec_rs2_addr(spec_insn_bseti_rs2_addr),
    .spec_rd_addr(spec_insn_bseti_rd_addr),
    .spec_rd_wdata(spec_insn_bseti_rd_wdata),
    .spec_pc_wdata(spec_insn_bseti_pc_wdata),
    .spec_mem_addr(spec_insn_bseti_mem_addr),
    .spec_mem_rmask(spec_insn_bseti_mem_rmask),
    .spec_mem_wmask(spec_insn_bseti_mem_wmask),
    .spec_mem_wdata(spec_insn_bseti_mem_wdata)
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

  wire                                spec_insn_clz_valid;
  wire                                spec_insn_clz_trap;
  wire [                       4 : 0] spec_insn_clz_rs1_addr;
  wire [                       4 : 0] spec_insn_clz_rs2_addr;
  wire [                       4 : 0] spec_insn_clz_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clz_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clz_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clz_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_clz_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_clz_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clz_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_clz_csr_misa_rmask;
`endif

  rvfi_insn_clz insn_clz (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_clz_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_clz_valid),
    .spec_trap(spec_insn_clz_trap),
    .spec_rs1_addr(spec_insn_clz_rs1_addr),
    .spec_rs2_addr(spec_insn_clz_rs2_addr),
    .spec_rd_addr(spec_insn_clz_rd_addr),
    .spec_rd_wdata(spec_insn_clz_rd_wdata),
    .spec_pc_wdata(spec_insn_clz_pc_wdata),
    .spec_mem_addr(spec_insn_clz_mem_addr),
    .spec_mem_rmask(spec_insn_clz_mem_rmask),
    .spec_mem_wmask(spec_insn_clz_mem_wmask),
    .spec_mem_wdata(spec_insn_clz_mem_wdata)
  );

  wire                                spec_insn_cpop_valid;
  wire                                spec_insn_cpop_trap;
  wire [                       4 : 0] spec_insn_cpop_rs1_addr;
  wire [                       4 : 0] spec_insn_cpop_rs2_addr;
  wire [                       4 : 0] spec_insn_cpop_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_cpop_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_cpop_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_cpop_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_cpop_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_cpop_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_cpop_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_cpop_csr_misa_rmask;
`endif

  rvfi_insn_cpop insn_cpop (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_cpop_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_cpop_valid),
    .spec_trap(spec_insn_cpop_trap),
    .spec_rs1_addr(spec_insn_cpop_rs1_addr),
    .spec_rs2_addr(spec_insn_cpop_rs2_addr),
    .spec_rd_addr(spec_insn_cpop_rd_addr),
    .spec_rd_wdata(spec_insn_cpop_rd_wdata),
    .spec_pc_wdata(spec_insn_cpop_pc_wdata),
    .spec_mem_addr(spec_insn_cpop_mem_addr),
    .spec_mem_rmask(spec_insn_cpop_mem_rmask),
    .spec_mem_wmask(spec_insn_cpop_mem_wmask),
    .spec_mem_wdata(spec_insn_cpop_mem_wdata)
  );

  wire                                spec_insn_ctz_valid;
  wire                                spec_insn_ctz_trap;
  wire [                       4 : 0] spec_insn_ctz_rs1_addr;
  wire [                       4 : 0] spec_insn_ctz_rs2_addr;
  wire [                       4 : 0] spec_insn_ctz_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_ctz_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_ctz_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_ctz_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_ctz_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_ctz_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_ctz_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_ctz_csr_misa_rmask;
`endif

  rvfi_insn_ctz insn_ctz (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_ctz_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_ctz_valid),
    .spec_trap(spec_insn_ctz_trap),
    .spec_rs1_addr(spec_insn_ctz_rs1_addr),
    .spec_rs2_addr(spec_insn_ctz_rs2_addr),
    .spec_rd_addr(spec_insn_ctz_rd_addr),
    .spec_rd_wdata(spec_insn_ctz_rd_wdata),
    .spec_pc_wdata(spec_insn_ctz_pc_wdata),
    .spec_mem_addr(spec_insn_ctz_mem_addr),
    .spec_mem_rmask(spec_insn_ctz_mem_rmask),
    .spec_mem_wmask(spec_insn_ctz_mem_wmask),
    .spec_mem_wdata(spec_insn_ctz_mem_wdata)
  );

  wire                                spec_insn_max_valid;
  wire                                spec_insn_max_trap;
  wire [                       4 : 0] spec_insn_max_rs1_addr;
  wire [                       4 : 0] spec_insn_max_rs2_addr;
  wire [                       4 : 0] spec_insn_max_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_max_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_max_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_max_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_max_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_max_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_max_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_max_csr_misa_rmask;
`endif

  rvfi_insn_max insn_max (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_max_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_max_valid),
    .spec_trap(spec_insn_max_trap),
    .spec_rs1_addr(spec_insn_max_rs1_addr),
    .spec_rs2_addr(spec_insn_max_rs2_addr),
    .spec_rd_addr(spec_insn_max_rd_addr),
    .spec_rd_wdata(spec_insn_max_rd_wdata),
    .spec_pc_wdata(spec_insn_max_pc_wdata),
    .spec_mem_addr(spec_insn_max_mem_addr),
    .spec_mem_rmask(spec_insn_max_mem_rmask),
    .spec_mem_wmask(spec_insn_max_mem_wmask),
    .spec_mem_wdata(spec_insn_max_mem_wdata)
  );

  wire                                spec_insn_maxu_valid;
  wire                                spec_insn_maxu_trap;
  wire [                       4 : 0] spec_insn_maxu_rs1_addr;
  wire [                       4 : 0] spec_insn_maxu_rs2_addr;
  wire [                       4 : 0] spec_insn_maxu_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_maxu_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_maxu_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_maxu_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_maxu_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_maxu_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_maxu_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_maxu_csr_misa_rmask;
`endif

  rvfi_insn_maxu insn_maxu (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_maxu_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_maxu_valid),
    .spec_trap(spec_insn_maxu_trap),
    .spec_rs1_addr(spec_insn_maxu_rs1_addr),
    .spec_rs2_addr(spec_insn_maxu_rs2_addr),
    .spec_rd_addr(spec_insn_maxu_rd_addr),
    .spec_rd_wdata(spec_insn_maxu_rd_wdata),
    .spec_pc_wdata(spec_insn_maxu_pc_wdata),
    .spec_mem_addr(spec_insn_maxu_mem_addr),
    .spec_mem_rmask(spec_insn_maxu_mem_rmask),
    .spec_mem_wmask(spec_insn_maxu_mem_wmask),
    .spec_mem_wdata(spec_insn_maxu_mem_wdata)
  );

  wire                                spec_insn_min_valid;
  wire                                spec_insn_min_trap;
  wire [                       4 : 0] spec_insn_min_rs1_addr;
  wire [                       4 : 0] spec_insn_min_rs2_addr;
  wire [                       4 : 0] spec_insn_min_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_min_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_min_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_min_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_min_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_min_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_min_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_min_csr_misa_rmask;
`endif

  rvfi_insn_min insn_min (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_min_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_min_valid),
    .spec_trap(spec_insn_min_trap),
    .spec_rs1_addr(spec_insn_min_rs1_addr),
    .spec_rs2_addr(spec_insn_min_rs2_addr),
    .spec_rd_addr(spec_insn_min_rd_addr),
    .spec_rd_wdata(spec_insn_min_rd_wdata),
    .spec_pc_wdata(spec_insn_min_pc_wdata),
    .spec_mem_addr(spec_insn_min_mem_addr),
    .spec_mem_rmask(spec_insn_min_mem_rmask),
    .spec_mem_wmask(spec_insn_min_mem_wmask),
    .spec_mem_wdata(spec_insn_min_mem_wdata)
  );

  wire                                spec_insn_minu_valid;
  wire                                spec_insn_minu_trap;
  wire [                       4 : 0] spec_insn_minu_rs1_addr;
  wire [                       4 : 0] spec_insn_minu_rs2_addr;
  wire [                       4 : 0] spec_insn_minu_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_minu_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_minu_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_minu_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_minu_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_minu_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_minu_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_minu_csr_misa_rmask;
`endif

  rvfi_insn_minu insn_minu (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_minu_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_minu_valid),
    .spec_trap(spec_insn_minu_trap),
    .spec_rs1_addr(spec_insn_minu_rs1_addr),
    .spec_rs2_addr(spec_insn_minu_rs2_addr),
    .spec_rd_addr(spec_insn_minu_rd_addr),
    .spec_rd_wdata(spec_insn_minu_rd_wdata),
    .spec_pc_wdata(spec_insn_minu_pc_wdata),
    .spec_mem_addr(spec_insn_minu_mem_addr),
    .spec_mem_rmask(spec_insn_minu_mem_rmask),
    .spec_mem_wmask(spec_insn_minu_mem_wmask),
    .spec_mem_wdata(spec_insn_minu_mem_wdata)
  );

  wire                                spec_insn_orc.b_valid;
  wire                                spec_insn_orc.b_trap;
  wire [                       4 : 0] spec_insn_orc.b_rs1_addr;
  wire [                       4 : 0] spec_insn_orc.b_rs2_addr;
  wire [                       4 : 0] spec_insn_orc.b_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_orc.b_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_orc.b_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_orc.b_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_orc.b_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_orc.b_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_orc.b_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_orc.b_csr_misa_rmask;
`endif

  rvfi_insn_orc.b insn_orc.b (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_orc.b_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_orc.b_valid),
    .spec_trap(spec_insn_orc.b_trap),
    .spec_rs1_addr(spec_insn_orc.b_rs1_addr),
    .spec_rs2_addr(spec_insn_orc.b_rs2_addr),
    .spec_rd_addr(spec_insn_orc.b_rd_addr),
    .spec_rd_wdata(spec_insn_orc.b_rd_wdata),
    .spec_pc_wdata(spec_insn_orc.b_pc_wdata),
    .spec_mem_addr(spec_insn_orc.b_mem_addr),
    .spec_mem_rmask(spec_insn_orc.b_mem_rmask),
    .spec_mem_wmask(spec_insn_orc.b_mem_wmask),
    .spec_mem_wdata(spec_insn_orc.b_mem_wdata)
  );

  wire                                spec_insn_orn_valid;
  wire                                spec_insn_orn_trap;
  wire [                       4 : 0] spec_insn_orn_rs1_addr;
  wire [                       4 : 0] spec_insn_orn_rs2_addr;
  wire [                       4 : 0] spec_insn_orn_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_orn_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_orn_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_orn_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_orn_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_orn_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_orn_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_orn_csr_misa_rmask;
`endif

  rvfi_insn_orn insn_orn (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_orn_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_orn_valid),
    .spec_trap(spec_insn_orn_trap),
    .spec_rs1_addr(spec_insn_orn_rs1_addr),
    .spec_rs2_addr(spec_insn_orn_rs2_addr),
    .spec_rd_addr(spec_insn_orn_rd_addr),
    .spec_rd_wdata(spec_insn_orn_rd_wdata),
    .spec_pc_wdata(spec_insn_orn_pc_wdata),
    .spec_mem_addr(spec_insn_orn_mem_addr),
    .spec_mem_rmask(spec_insn_orn_mem_rmask),
    .spec_mem_wmask(spec_insn_orn_mem_wmask),
    .spec_mem_wdata(spec_insn_orn_mem_wdata)
  );

  wire                                spec_insn_rev8_valid;
  wire                                spec_insn_rev8_trap;
  wire [                       4 : 0] spec_insn_rev8_rs1_addr;
  wire [                       4 : 0] spec_insn_rev8_rs2_addr;
  wire [                       4 : 0] spec_insn_rev8_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rev8_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rev8_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rev8_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_rev8_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_rev8_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rev8_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rev8_csr_misa_rmask;
`endif

  rvfi_insn_rev8 insn_rev8 (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_rev8_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_rev8_valid),
    .spec_trap(spec_insn_rev8_trap),
    .spec_rs1_addr(spec_insn_rev8_rs1_addr),
    .spec_rs2_addr(spec_insn_rev8_rs2_addr),
    .spec_rd_addr(spec_insn_rev8_rd_addr),
    .spec_rd_wdata(spec_insn_rev8_rd_wdata),
    .spec_pc_wdata(spec_insn_rev8_pc_wdata),
    .spec_mem_addr(spec_insn_rev8_mem_addr),
    .spec_mem_rmask(spec_insn_rev8_mem_rmask),
    .spec_mem_wmask(spec_insn_rev8_mem_wmask),
    .spec_mem_wdata(spec_insn_rev8_mem_wdata)
  );

  wire                                spec_insn_rol_valid;
  wire                                spec_insn_rol_trap;
  wire [                       4 : 0] spec_insn_rol_rs1_addr;
  wire [                       4 : 0] spec_insn_rol_rs2_addr;
  wire [                       4 : 0] spec_insn_rol_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rol_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rol_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rol_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_rol_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_rol_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rol_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rol_csr_misa_rmask;
`endif

  rvfi_insn_rol insn_rol (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_rol_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_rol_valid),
    .spec_trap(spec_insn_rol_trap),
    .spec_rs1_addr(spec_insn_rol_rs1_addr),
    .spec_rs2_addr(spec_insn_rol_rs2_addr),
    .spec_rd_addr(spec_insn_rol_rd_addr),
    .spec_rd_wdata(spec_insn_rol_rd_wdata),
    .spec_pc_wdata(spec_insn_rol_pc_wdata),
    .spec_mem_addr(spec_insn_rol_mem_addr),
    .spec_mem_rmask(spec_insn_rol_mem_rmask),
    .spec_mem_wmask(spec_insn_rol_mem_wmask),
    .spec_mem_wdata(spec_insn_rol_mem_wdata)
  );

  wire                                spec_insn_ror_valid;
  wire                                spec_insn_ror_trap;
  wire [                       4 : 0] spec_insn_ror_rs1_addr;
  wire [                       4 : 0] spec_insn_ror_rs2_addr;
  wire [                       4 : 0] spec_insn_ror_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_ror_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_ror_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_ror_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_ror_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_ror_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_ror_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_ror_csr_misa_rmask;
`endif

  rvfi_insn_ror insn_ror (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_ror_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_ror_valid),
    .spec_trap(spec_insn_ror_trap),
    .spec_rs1_addr(spec_insn_ror_rs1_addr),
    .spec_rs2_addr(spec_insn_ror_rs2_addr),
    .spec_rd_addr(spec_insn_ror_rd_addr),
    .spec_rd_wdata(spec_insn_ror_rd_wdata),
    .spec_pc_wdata(spec_insn_ror_pc_wdata),
    .spec_mem_addr(spec_insn_ror_mem_addr),
    .spec_mem_rmask(spec_insn_ror_mem_rmask),
    .spec_mem_wmask(spec_insn_ror_mem_wmask),
    .spec_mem_wdata(spec_insn_ror_mem_wdata)
  );

  wire                                spec_insn_rori_valid;
  wire                                spec_insn_rori_trap;
  wire [                       4 : 0] spec_insn_rori_rs1_addr;
  wire [                       4 : 0] spec_insn_rori_rs2_addr;
  wire [                       4 : 0] spec_insn_rori_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rori_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rori_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rori_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_rori_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_rori_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rori_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_rori_csr_misa_rmask;
`endif

  rvfi_insn_rori insn_rori (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_rori_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_rori_valid),
    .spec_trap(spec_insn_rori_trap),
    .spec_rs1_addr(spec_insn_rori_rs1_addr),
    .spec_rs2_addr(spec_insn_rori_rs2_addr),
    .spec_rd_addr(spec_insn_rori_rd_addr),
    .spec_rd_wdata(spec_insn_rori_rd_wdata),
    .spec_pc_wdata(spec_insn_rori_pc_wdata),
    .spec_mem_addr(spec_insn_rori_mem_addr),
    .spec_mem_rmask(spec_insn_rori_mem_rmask),
    .spec_mem_wmask(spec_insn_rori_mem_wmask),
    .spec_mem_wdata(spec_insn_rori_mem_wdata)
  );

  wire                                spec_insn_sext.b_valid;
  wire                                spec_insn_sext.b_trap;
  wire [                       4 : 0] spec_insn_sext.b_rs1_addr;
  wire [                       4 : 0] spec_insn_sext.b_rs2_addr;
  wire [                       4 : 0] spec_insn_sext.b_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sext.b_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sext.b_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sext.b_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_sext.b_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_sext.b_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sext.b_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sext.b_csr_misa_rmask;
`endif

  rvfi_insn_sext.b insn_sext.b (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_sext.b_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_sext.b_valid),
    .spec_trap(spec_insn_sext.b_trap),
    .spec_rs1_addr(spec_insn_sext.b_rs1_addr),
    .spec_rs2_addr(spec_insn_sext.b_rs2_addr),
    .spec_rd_addr(spec_insn_sext.b_rd_addr),
    .spec_rd_wdata(spec_insn_sext.b_rd_wdata),
    .spec_pc_wdata(spec_insn_sext.b_pc_wdata),
    .spec_mem_addr(spec_insn_sext.b_mem_addr),
    .spec_mem_rmask(spec_insn_sext.b_mem_rmask),
    .spec_mem_wmask(spec_insn_sext.b_mem_wmask),
    .spec_mem_wdata(spec_insn_sext.b_mem_wdata)
  );

  wire                                spec_insn_sext.h_valid;
  wire                                spec_insn_sext.h_trap;
  wire [                       4 : 0] spec_insn_sext.h_rs1_addr;
  wire [                       4 : 0] spec_insn_sext.h_rs2_addr;
  wire [                       4 : 0] spec_insn_sext.h_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sext.h_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sext.h_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sext.h_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_sext.h_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_sext.h_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sext.h_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sext.h_csr_misa_rmask;
`endif

  rvfi_insn_sext.h insn_sext.h (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_sext.h_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_sext.h_valid),
    .spec_trap(spec_insn_sext.h_trap),
    .spec_rs1_addr(spec_insn_sext.h_rs1_addr),
    .spec_rs2_addr(spec_insn_sext.h_rs2_addr),
    .spec_rd_addr(spec_insn_sext.h_rd_addr),
    .spec_rd_wdata(spec_insn_sext.h_rd_wdata),
    .spec_pc_wdata(spec_insn_sext.h_pc_wdata),
    .spec_mem_addr(spec_insn_sext.h_mem_addr),
    .spec_mem_rmask(spec_insn_sext.h_mem_rmask),
    .spec_mem_wmask(spec_insn_sext.h_mem_wmask),
    .spec_mem_wdata(spec_insn_sext.h_mem_wdata)
  );

  wire                                spec_insn_sh1add_valid;
  wire                                spec_insn_sh1add_trap;
  wire [                       4 : 0] spec_insn_sh1add_rs1_addr;
  wire [                       4 : 0] spec_insn_sh1add_rs2_addr;
  wire [                       4 : 0] spec_insn_sh1add_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh1add_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh1add_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh1add_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_sh1add_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_sh1add_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh1add_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh1add_csr_misa_rmask;
`endif

  rvfi_insn_sh1add insn_sh1add (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_sh1add_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_sh1add_valid),
    .spec_trap(spec_insn_sh1add_trap),
    .spec_rs1_addr(spec_insn_sh1add_rs1_addr),
    .spec_rs2_addr(spec_insn_sh1add_rs2_addr),
    .spec_rd_addr(spec_insn_sh1add_rd_addr),
    .spec_rd_wdata(spec_insn_sh1add_rd_wdata),
    .spec_pc_wdata(spec_insn_sh1add_pc_wdata),
    .spec_mem_addr(spec_insn_sh1add_mem_addr),
    .spec_mem_rmask(spec_insn_sh1add_mem_rmask),
    .spec_mem_wmask(spec_insn_sh1add_mem_wmask),
    .spec_mem_wdata(spec_insn_sh1add_mem_wdata)
  );

  wire                                spec_insn_sh2add_valid;
  wire                                spec_insn_sh2add_trap;
  wire [                       4 : 0] spec_insn_sh2add_rs1_addr;
  wire [                       4 : 0] spec_insn_sh2add_rs2_addr;
  wire [                       4 : 0] spec_insn_sh2add_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh2add_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh2add_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh2add_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_sh2add_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_sh2add_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh2add_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh2add_csr_misa_rmask;
`endif

  rvfi_insn_sh2add insn_sh2add (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_sh2add_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_sh2add_valid),
    .spec_trap(spec_insn_sh2add_trap),
    .spec_rs1_addr(spec_insn_sh2add_rs1_addr),
    .spec_rs2_addr(spec_insn_sh2add_rs2_addr),
    .spec_rd_addr(spec_insn_sh2add_rd_addr),
    .spec_rd_wdata(spec_insn_sh2add_rd_wdata),
    .spec_pc_wdata(spec_insn_sh2add_pc_wdata),
    .spec_mem_addr(spec_insn_sh2add_mem_addr),
    .spec_mem_rmask(spec_insn_sh2add_mem_rmask),
    .spec_mem_wmask(spec_insn_sh2add_mem_wmask),
    .spec_mem_wdata(spec_insn_sh2add_mem_wdata)
  );

  wire                                spec_insn_sh3add_valid;
  wire                                spec_insn_sh3add_trap;
  wire [                       4 : 0] spec_insn_sh3add_rs1_addr;
  wire [                       4 : 0] spec_insn_sh3add_rs2_addr;
  wire [                       4 : 0] spec_insn_sh3add_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh3add_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh3add_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh3add_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_sh3add_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_sh3add_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh3add_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_sh3add_csr_misa_rmask;
`endif

  rvfi_insn_sh3add insn_sh3add (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_sh3add_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_sh3add_valid),
    .spec_trap(spec_insn_sh3add_trap),
    .spec_rs1_addr(spec_insn_sh3add_rs1_addr),
    .spec_rs2_addr(spec_insn_sh3add_rs2_addr),
    .spec_rd_addr(spec_insn_sh3add_rd_addr),
    .spec_rd_wdata(spec_insn_sh3add_rd_wdata),
    .spec_pc_wdata(spec_insn_sh3add_pc_wdata),
    .spec_mem_addr(spec_insn_sh3add_mem_addr),
    .spec_mem_rmask(spec_insn_sh3add_mem_rmask),
    .spec_mem_wmask(spec_insn_sh3add_mem_wmask),
    .spec_mem_wdata(spec_insn_sh3add_mem_wdata)
  );

  wire                                spec_insn_xnor_valid;
  wire                                spec_insn_xnor_trap;
  wire [                       4 : 0] spec_insn_xnor_rs1_addr;
  wire [                       4 : 0] spec_insn_xnor_rs2_addr;
  wire [                       4 : 0] spec_insn_xnor_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_xnor_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_xnor_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_xnor_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_xnor_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_xnor_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_xnor_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_xnor_csr_misa_rmask;
`endif

  rvfi_insn_xnor insn_xnor (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_xnor_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_xnor_valid),
    .spec_trap(spec_insn_xnor_trap),
    .spec_rs1_addr(spec_insn_xnor_rs1_addr),
    .spec_rs2_addr(spec_insn_xnor_rs2_addr),
    .spec_rd_addr(spec_insn_xnor_rd_addr),
    .spec_rd_wdata(spec_insn_xnor_rd_wdata),
    .spec_pc_wdata(spec_insn_xnor_pc_wdata),
    .spec_mem_addr(spec_insn_xnor_mem_addr),
    .spec_mem_rmask(spec_insn_xnor_mem_rmask),
    .spec_mem_wmask(spec_insn_xnor_mem_wmask),
    .spec_mem_wdata(spec_insn_xnor_mem_wdata)
  );

  wire                                spec_insn_zext.h_valid;
  wire                                spec_insn_zext.h_trap;
  wire [                       4 : 0] spec_insn_zext.h_rs1_addr;
  wire [                       4 : 0] spec_insn_zext.h_rs2_addr;
  wire [                       4 : 0] spec_insn_zext.h_rd_addr;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_zext.h_rd_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_zext.h_pc_wdata;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_zext.h_mem_addr;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_zext.h_mem_rmask;
  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_zext.h_mem_wmask;
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_zext.h_mem_wdata;
`ifdef RISCV_FORMAL_CSR_MISA
  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_zext.h_csr_misa_rmask;
`endif

  rvfi_insn_zext.h insn_zext.h (
    .rvfi_valid(rvfi_valid),
    .rvfi_insn(rvfi_insn),
    .rvfi_pc_rdata(rvfi_pc_rdata),
    .rvfi_rs1_rdata(rvfi_rs1_rdata),
    .rvfi_rs2_rdata(rvfi_rs2_rdata),
    .rvfi_mem_rdata(rvfi_mem_rdata),
`ifdef RISCV_FORMAL_CSR_MISA
    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),
    .spec_csr_misa_rmask(spec_insn_zext.h_csr_misa_rmask),
`endif
    .spec_valid(spec_insn_zext.h_valid),
    .spec_trap(spec_insn_zext.h_trap),
    .spec_rs1_addr(spec_insn_zext.h_rs1_addr),
    .spec_rs2_addr(spec_insn_zext.h_rs2_addr),
    .spec_rd_addr(spec_insn_zext.h_rd_addr),
    .spec_rd_wdata(spec_insn_zext.h_rd_wdata),
    .spec_pc_wdata(spec_insn_zext.h_pc_wdata),
    .spec_mem_addr(spec_insn_zext.h_mem_addr),
    .spec_mem_rmask(spec_insn_zext.h_mem_rmask),
    .spec_mem_wmask(spec_insn_zext.h_mem_wmask),
    .spec_mem_wdata(spec_insn_zext.h_mem_wdata)
  );

  assign spec_valid =
		spec_insn_andn_valid ? spec_insn_andn_valid :
		spec_insn_bclr_valid ? spec_insn_bclr_valid :
		spec_insn_bclri_valid ? spec_insn_bclri_valid :
		spec_insn_bext_valid ? spec_insn_bext_valid :
		spec_insn_bexti_valid ? spec_insn_bexti_valid :
		spec_insn_binv_valid ? spec_insn_binv_valid :
		spec_insn_binvi_valid ? spec_insn_binvi_valid :
		spec_insn_bset_valid ? spec_insn_bset_valid :
		spec_insn_bseti_valid ? spec_insn_bseti_valid :
		spec_insn_clmul_valid ? spec_insn_clmul_valid :
		spec_insn_clmulh_valid ? spec_insn_clmulh_valid :
		spec_insn_clmulr_valid ? spec_insn_clmulr_valid :
		spec_insn_clz_valid ? spec_insn_clz_valid :
		spec_insn_cpop_valid ? spec_insn_cpop_valid :
		spec_insn_ctz_valid ? spec_insn_ctz_valid :
		spec_insn_max_valid ? spec_insn_max_valid :
		spec_insn_maxu_valid ? spec_insn_maxu_valid :
		spec_insn_min_valid ? spec_insn_min_valid :
		spec_insn_minu_valid ? spec_insn_minu_valid :
		spec_insn_orc.b_valid ? spec_insn_orc.b_valid :
		spec_insn_orn_valid ? spec_insn_orn_valid :
		spec_insn_rev8_valid ? spec_insn_rev8_valid :
		spec_insn_rol_valid ? spec_insn_rol_valid :
		spec_insn_ror_valid ? spec_insn_ror_valid :
		spec_insn_rori_valid ? spec_insn_rori_valid :
		spec_insn_sext.b_valid ? spec_insn_sext.b_valid :
		spec_insn_sext.h_valid ? spec_insn_sext.h_valid :
		spec_insn_sh1add_valid ? spec_insn_sh1add_valid :
		spec_insn_sh2add_valid ? spec_insn_sh2add_valid :
		spec_insn_sh3add_valid ? spec_insn_sh3add_valid :
		spec_insn_xnor_valid ? spec_insn_xnor_valid :
		spec_insn_zext.h_valid ? spec_insn_zext.h_valid : 0;
  assign spec_trap =
		spec_insn_andn_valid ? spec_insn_andn_trap :
		spec_insn_bclr_valid ? spec_insn_bclr_trap :
		spec_insn_bclri_valid ? spec_insn_bclri_trap :
		spec_insn_bext_valid ? spec_insn_bext_trap :
		spec_insn_bexti_valid ? spec_insn_bexti_trap :
		spec_insn_binv_valid ? spec_insn_binv_trap :
		spec_insn_binvi_valid ? spec_insn_binvi_trap :
		spec_insn_bset_valid ? spec_insn_bset_trap :
		spec_insn_bseti_valid ? spec_insn_bseti_trap :
		spec_insn_clmul_valid ? spec_insn_clmul_trap :
		spec_insn_clmulh_valid ? spec_insn_clmulh_trap :
		spec_insn_clmulr_valid ? spec_insn_clmulr_trap :
		spec_insn_clz_valid ? spec_insn_clz_trap :
		spec_insn_cpop_valid ? spec_insn_cpop_trap :
		spec_insn_ctz_valid ? spec_insn_ctz_trap :
		spec_insn_max_valid ? spec_insn_max_trap :
		spec_insn_maxu_valid ? spec_insn_maxu_trap :
		spec_insn_min_valid ? spec_insn_min_trap :
		spec_insn_minu_valid ? spec_insn_minu_trap :
		spec_insn_orc.b_valid ? spec_insn_orc.b_trap :
		spec_insn_orn_valid ? spec_insn_orn_trap :
		spec_insn_rev8_valid ? spec_insn_rev8_trap :
		spec_insn_rol_valid ? spec_insn_rol_trap :
		spec_insn_ror_valid ? spec_insn_ror_trap :
		spec_insn_rori_valid ? spec_insn_rori_trap :
		spec_insn_sext.b_valid ? spec_insn_sext.b_trap :
		spec_insn_sext.h_valid ? spec_insn_sext.h_trap :
		spec_insn_sh1add_valid ? spec_insn_sh1add_trap :
		spec_insn_sh2add_valid ? spec_insn_sh2add_trap :
		spec_insn_sh3add_valid ? spec_insn_sh3add_trap :
		spec_insn_xnor_valid ? spec_insn_xnor_trap :
		spec_insn_zext.h_valid ? spec_insn_zext.h_trap : 0;
  assign spec_rs1_addr =
		spec_insn_andn_valid ? spec_insn_andn_rs1_addr :
		spec_insn_bclr_valid ? spec_insn_bclr_rs1_addr :
		spec_insn_bclri_valid ? spec_insn_bclri_rs1_addr :
		spec_insn_bext_valid ? spec_insn_bext_rs1_addr :
		spec_insn_bexti_valid ? spec_insn_bexti_rs1_addr :
		spec_insn_binv_valid ? spec_insn_binv_rs1_addr :
		spec_insn_binvi_valid ? spec_insn_binvi_rs1_addr :
		spec_insn_bset_valid ? spec_insn_bset_rs1_addr :
		spec_insn_bseti_valid ? spec_insn_bseti_rs1_addr :
		spec_insn_clmul_valid ? spec_insn_clmul_rs1_addr :
		spec_insn_clmulh_valid ? spec_insn_clmulh_rs1_addr :
		spec_insn_clmulr_valid ? spec_insn_clmulr_rs1_addr :
		spec_insn_clz_valid ? spec_insn_clz_rs1_addr :
		spec_insn_cpop_valid ? spec_insn_cpop_rs1_addr :
		spec_insn_ctz_valid ? spec_insn_ctz_rs1_addr :
		spec_insn_max_valid ? spec_insn_max_rs1_addr :
		spec_insn_maxu_valid ? spec_insn_maxu_rs1_addr :
		spec_insn_min_valid ? spec_insn_min_rs1_addr :
		spec_insn_minu_valid ? spec_insn_minu_rs1_addr :
		spec_insn_orc.b_valid ? spec_insn_orc.b_rs1_addr :
		spec_insn_orn_valid ? spec_insn_orn_rs1_addr :
		spec_insn_rev8_valid ? spec_insn_rev8_rs1_addr :
		spec_insn_rol_valid ? spec_insn_rol_rs1_addr :
		spec_insn_ror_valid ? spec_insn_ror_rs1_addr :
		spec_insn_rori_valid ? spec_insn_rori_rs1_addr :
		spec_insn_sext.b_valid ? spec_insn_sext.b_rs1_addr :
		spec_insn_sext.h_valid ? spec_insn_sext.h_rs1_addr :
		spec_insn_sh1add_valid ? spec_insn_sh1add_rs1_addr :
		spec_insn_sh2add_valid ? spec_insn_sh2add_rs1_addr :
		spec_insn_sh3add_valid ? spec_insn_sh3add_rs1_addr :
		spec_insn_xnor_valid ? spec_insn_xnor_rs1_addr :
		spec_insn_zext.h_valid ? spec_insn_zext.h_rs1_addr : 0;
  assign spec_rs2_addr =
		spec_insn_andn_valid ? spec_insn_andn_rs2_addr :
		spec_insn_bclr_valid ? spec_insn_bclr_rs2_addr :
		spec_insn_bclri_valid ? spec_insn_bclri_rs2_addr :
		spec_insn_bext_valid ? spec_insn_bext_rs2_addr :
		spec_insn_bexti_valid ? spec_insn_bexti_rs2_addr :
		spec_insn_binv_valid ? spec_insn_binv_rs2_addr :
		spec_insn_binvi_valid ? spec_insn_binvi_rs2_addr :
		spec_insn_bset_valid ? spec_insn_bset_rs2_addr :
		spec_insn_bseti_valid ? spec_insn_bseti_rs2_addr :
		spec_insn_clmul_valid ? spec_insn_clmul_rs2_addr :
		spec_insn_clmulh_valid ? spec_insn_clmulh_rs2_addr :
		spec_insn_clmulr_valid ? spec_insn_clmulr_rs2_addr :
		spec_insn_clz_valid ? spec_insn_clz_rs2_addr :
		spec_insn_cpop_valid ? spec_insn_cpop_rs2_addr :
		spec_insn_ctz_valid ? spec_insn_ctz_rs2_addr :
		spec_insn_max_valid ? spec_insn_max_rs2_addr :
		spec_insn_maxu_valid ? spec_insn_maxu_rs2_addr :
		spec_insn_min_valid ? spec_insn_min_rs2_addr :
		spec_insn_minu_valid ? spec_insn_minu_rs2_addr :
		spec_insn_orc.b_valid ? spec_insn_orc.b_rs2_addr :
		spec_insn_orn_valid ? spec_insn_orn_rs2_addr :
		spec_insn_rev8_valid ? spec_insn_rev8_rs2_addr :
		spec_insn_rol_valid ? spec_insn_rol_rs2_addr :
		spec_insn_ror_valid ? spec_insn_ror_rs2_addr :
		spec_insn_rori_valid ? spec_insn_rori_rs2_addr :
		spec_insn_sext.b_valid ? spec_insn_sext.b_rs2_addr :
		spec_insn_sext.h_valid ? spec_insn_sext.h_rs2_addr :
		spec_insn_sh1add_valid ? spec_insn_sh1add_rs2_addr :
		spec_insn_sh2add_valid ? spec_insn_sh2add_rs2_addr :
		spec_insn_sh3add_valid ? spec_insn_sh3add_rs2_addr :
		spec_insn_xnor_valid ? spec_insn_xnor_rs2_addr :
		spec_insn_zext.h_valid ? spec_insn_zext.h_rs2_addr : 0;
  assign spec_rd_addr =
		spec_insn_andn_valid ? spec_insn_andn_rd_addr :
		spec_insn_bclr_valid ? spec_insn_bclr_rd_addr :
		spec_insn_bclri_valid ? spec_insn_bclri_rd_addr :
		spec_insn_bext_valid ? spec_insn_bext_rd_addr :
		spec_insn_bexti_valid ? spec_insn_bexti_rd_addr :
		spec_insn_binv_valid ? spec_insn_binv_rd_addr :
		spec_insn_binvi_valid ? spec_insn_binvi_rd_addr :
		spec_insn_bset_valid ? spec_insn_bset_rd_addr :
		spec_insn_bseti_valid ? spec_insn_bseti_rd_addr :
		spec_insn_clmul_valid ? spec_insn_clmul_rd_addr :
		spec_insn_clmulh_valid ? spec_insn_clmulh_rd_addr :
		spec_insn_clmulr_valid ? spec_insn_clmulr_rd_addr :
		spec_insn_clz_valid ? spec_insn_clz_rd_addr :
		spec_insn_cpop_valid ? spec_insn_cpop_rd_addr :
		spec_insn_ctz_valid ? spec_insn_ctz_rd_addr :
		spec_insn_max_valid ? spec_insn_max_rd_addr :
		spec_insn_maxu_valid ? spec_insn_maxu_rd_addr :
		spec_insn_min_valid ? spec_insn_min_rd_addr :
		spec_insn_minu_valid ? spec_insn_minu_rd_addr :
		spec_insn_orc.b_valid ? spec_insn_orc.b_rd_addr :
		spec_insn_orn_valid ? spec_insn_orn_rd_addr :
		spec_insn_rev8_valid ? spec_insn_rev8_rd_addr :
		spec_insn_rol_valid ? spec_insn_rol_rd_addr :
		spec_insn_ror_valid ? spec_insn_ror_rd_addr :
		spec_insn_rori_valid ? spec_insn_rori_rd_addr :
		spec_insn_sext.b_valid ? spec_insn_sext.b_rd_addr :
		spec_insn_sext.h_valid ? spec_insn_sext.h_rd_addr :
		spec_insn_sh1add_valid ? spec_insn_sh1add_rd_addr :
		spec_insn_sh2add_valid ? spec_insn_sh2add_rd_addr :
		spec_insn_sh3add_valid ? spec_insn_sh3add_rd_addr :
		spec_insn_xnor_valid ? spec_insn_xnor_rd_addr :
		spec_insn_zext.h_valid ? spec_insn_zext.h_rd_addr : 0;
  assign spec_rd_wdata =
		spec_insn_andn_valid ? spec_insn_andn_rd_wdata :
		spec_insn_bclr_valid ? spec_insn_bclr_rd_wdata :
		spec_insn_bclri_valid ? spec_insn_bclri_rd_wdata :
		spec_insn_bext_valid ? spec_insn_bext_rd_wdata :
		spec_insn_bexti_valid ? spec_insn_bexti_rd_wdata :
		spec_insn_binv_valid ? spec_insn_binv_rd_wdata :
		spec_insn_binvi_valid ? spec_insn_binvi_rd_wdata :
		spec_insn_bset_valid ? spec_insn_bset_rd_wdata :
		spec_insn_bseti_valid ? spec_insn_bseti_rd_wdata :
		spec_insn_clmul_valid ? spec_insn_clmul_rd_wdata :
		spec_insn_clmulh_valid ? spec_insn_clmulh_rd_wdata :
		spec_insn_clmulr_valid ? spec_insn_clmulr_rd_wdata :
		spec_insn_clz_valid ? spec_insn_clz_rd_wdata :
		spec_insn_cpop_valid ? spec_insn_cpop_rd_wdata :
		spec_insn_ctz_valid ? spec_insn_ctz_rd_wdata :
		spec_insn_max_valid ? spec_insn_max_rd_wdata :
		spec_insn_maxu_valid ? spec_insn_maxu_rd_wdata :
		spec_insn_min_valid ? spec_insn_min_rd_wdata :
		spec_insn_minu_valid ? spec_insn_minu_rd_wdata :
		spec_insn_orc.b_valid ? spec_insn_orc.b_rd_wdata :
		spec_insn_orn_valid ? spec_insn_orn_rd_wdata :
		spec_insn_rev8_valid ? spec_insn_rev8_rd_wdata :
		spec_insn_rol_valid ? spec_insn_rol_rd_wdata :
		spec_insn_ror_valid ? spec_insn_ror_rd_wdata :
		spec_insn_rori_valid ? spec_insn_rori_rd_wdata :
		spec_insn_sext.b_valid ? spec_insn_sext.b_rd_wdata :
		spec_insn_sext.h_valid ? spec_insn_sext.h_rd_wdata :
		spec_insn_sh1add_valid ? spec_insn_sh1add_rd_wdata :
		spec_insn_sh2add_valid ? spec_insn_sh2add_rd_wdata :
		spec_insn_sh3add_valid ? spec_insn_sh3add_rd_wdata :
		spec_insn_xnor_valid ? spec_insn_xnor_rd_wdata :
		spec_insn_zext.h_valid ? spec_insn_zext.h_rd_wdata : 0;
  assign spec_pc_wdata =
		spec_insn_andn_valid ? spec_insn_andn_pc_wdata :
		spec_insn_bclr_valid ? spec_insn_bclr_pc_wdata :
		spec_insn_bclri_valid ? spec_insn_bclri_pc_wdata :
		spec_insn_bext_valid ? spec_insn_bext_pc_wdata :
		spec_insn_bexti_valid ? spec_insn_bexti_pc_wdata :
		spec_insn_binv_valid ? spec_insn_binv_pc_wdata :
		spec_insn_binvi_valid ? spec_insn_binvi_pc_wdata :
		spec_insn_bset_valid ? spec_insn_bset_pc_wdata :
		spec_insn_bseti_valid ? spec_insn_bseti_pc_wdata :
		spec_insn_clmul_valid ? spec_insn_clmul_pc_wdata :
		spec_insn_clmulh_valid ? spec_insn_clmulh_pc_wdata :
		spec_insn_clmulr_valid ? spec_insn_clmulr_pc_wdata :
		spec_insn_clz_valid ? spec_insn_clz_pc_wdata :
		spec_insn_cpop_valid ? spec_insn_cpop_pc_wdata :
		spec_insn_ctz_valid ? spec_insn_ctz_pc_wdata :
		spec_insn_max_valid ? spec_insn_max_pc_wdata :
		spec_insn_maxu_valid ? spec_insn_maxu_pc_wdata :
		spec_insn_min_valid ? spec_insn_min_pc_wdata :
		spec_insn_minu_valid ? spec_insn_minu_pc_wdata :
		spec_insn_orc.b_valid ? spec_insn_orc.b_pc_wdata :
		spec_insn_orn_valid ? spec_insn_orn_pc_wdata :
		spec_insn_rev8_valid ? spec_insn_rev8_pc_wdata :
		spec_insn_rol_valid ? spec_insn_rol_pc_wdata :
		spec_insn_ror_valid ? spec_insn_ror_pc_wdata :
		spec_insn_rori_valid ? spec_insn_rori_pc_wdata :
		spec_insn_sext.b_valid ? spec_insn_sext.b_pc_wdata :
		spec_insn_sext.h_valid ? spec_insn_sext.h_pc_wdata :
		spec_insn_sh1add_valid ? spec_insn_sh1add_pc_wdata :
		spec_insn_sh2add_valid ? spec_insn_sh2add_pc_wdata :
		spec_insn_sh3add_valid ? spec_insn_sh3add_pc_wdata :
		spec_insn_xnor_valid ? spec_insn_xnor_pc_wdata :
		spec_insn_zext.h_valid ? spec_insn_zext.h_pc_wdata : 0;
  assign spec_mem_addr =
		spec_insn_andn_valid ? spec_insn_andn_mem_addr :
		spec_insn_bclr_valid ? spec_insn_bclr_mem_addr :
		spec_insn_bclri_valid ? spec_insn_bclri_mem_addr :
		spec_insn_bext_valid ? spec_insn_bext_mem_addr :
		spec_insn_bexti_valid ? spec_insn_bexti_mem_addr :
		spec_insn_binv_valid ? spec_insn_binv_mem_addr :
		spec_insn_binvi_valid ? spec_insn_binvi_mem_addr :
		spec_insn_bset_valid ? spec_insn_bset_mem_addr :
		spec_insn_bseti_valid ? spec_insn_bseti_mem_addr :
		spec_insn_clmul_valid ? spec_insn_clmul_mem_addr :
		spec_insn_clmulh_valid ? spec_insn_clmulh_mem_addr :
		spec_insn_clmulr_valid ? spec_insn_clmulr_mem_addr :
		spec_insn_clz_valid ? spec_insn_clz_mem_addr :
		spec_insn_cpop_valid ? spec_insn_cpop_mem_addr :
		spec_insn_ctz_valid ? spec_insn_ctz_mem_addr :
		spec_insn_max_valid ? spec_insn_max_mem_addr :
		spec_insn_maxu_valid ? spec_insn_maxu_mem_addr :
		spec_insn_min_valid ? spec_insn_min_mem_addr :
		spec_insn_minu_valid ? spec_insn_minu_mem_addr :
		spec_insn_orc.b_valid ? spec_insn_orc.b_mem_addr :
		spec_insn_orn_valid ? spec_insn_orn_mem_addr :
		spec_insn_rev8_valid ? spec_insn_rev8_mem_addr :
		spec_insn_rol_valid ? spec_insn_rol_mem_addr :
		spec_insn_ror_valid ? spec_insn_ror_mem_addr :
		spec_insn_rori_valid ? spec_insn_rori_mem_addr :
		spec_insn_sext.b_valid ? spec_insn_sext.b_mem_addr :
		spec_insn_sext.h_valid ? spec_insn_sext.h_mem_addr :
		spec_insn_sh1add_valid ? spec_insn_sh1add_mem_addr :
		spec_insn_sh2add_valid ? spec_insn_sh2add_mem_addr :
		spec_insn_sh3add_valid ? spec_insn_sh3add_mem_addr :
		spec_insn_xnor_valid ? spec_insn_xnor_mem_addr :
		spec_insn_zext.h_valid ? spec_insn_zext.h_mem_addr : 0;
  assign spec_mem_rmask =
		spec_insn_andn_valid ? spec_insn_andn_mem_rmask :
		spec_insn_bclr_valid ? spec_insn_bclr_mem_rmask :
		spec_insn_bclri_valid ? spec_insn_bclri_mem_rmask :
		spec_insn_bext_valid ? spec_insn_bext_mem_rmask :
		spec_insn_bexti_valid ? spec_insn_bexti_mem_rmask :
		spec_insn_binv_valid ? spec_insn_binv_mem_rmask :
		spec_insn_binvi_valid ? spec_insn_binvi_mem_rmask :
		spec_insn_bset_valid ? spec_insn_bset_mem_rmask :
		spec_insn_bseti_valid ? spec_insn_bseti_mem_rmask :
		spec_insn_clmul_valid ? spec_insn_clmul_mem_rmask :
		spec_insn_clmulh_valid ? spec_insn_clmulh_mem_rmask :
		spec_insn_clmulr_valid ? spec_insn_clmulr_mem_rmask :
		spec_insn_clz_valid ? spec_insn_clz_mem_rmask :
		spec_insn_cpop_valid ? spec_insn_cpop_mem_rmask :
		spec_insn_ctz_valid ? spec_insn_ctz_mem_rmask :
		spec_insn_max_valid ? spec_insn_max_mem_rmask :
		spec_insn_maxu_valid ? spec_insn_maxu_mem_rmask :
		spec_insn_min_valid ? spec_insn_min_mem_rmask :
		spec_insn_minu_valid ? spec_insn_minu_mem_rmask :
		spec_insn_orc.b_valid ? spec_insn_orc.b_mem_rmask :
		spec_insn_orn_valid ? spec_insn_orn_mem_rmask :
		spec_insn_rev8_valid ? spec_insn_rev8_mem_rmask :
		spec_insn_rol_valid ? spec_insn_rol_mem_rmask :
		spec_insn_ror_valid ? spec_insn_ror_mem_rmask :
		spec_insn_rori_valid ? spec_insn_rori_mem_rmask :
		spec_insn_sext.b_valid ? spec_insn_sext.b_mem_rmask :
		spec_insn_sext.h_valid ? spec_insn_sext.h_mem_rmask :
		spec_insn_sh1add_valid ? spec_insn_sh1add_mem_rmask :
		spec_insn_sh2add_valid ? spec_insn_sh2add_mem_rmask :
		spec_insn_sh3add_valid ? spec_insn_sh3add_mem_rmask :
		spec_insn_xnor_valid ? spec_insn_xnor_mem_rmask :
		spec_insn_zext.h_valid ? spec_insn_zext.h_mem_rmask : 0;
  assign spec_mem_wmask =
		spec_insn_andn_valid ? spec_insn_andn_mem_wmask :
		spec_insn_bclr_valid ? spec_insn_bclr_mem_wmask :
		spec_insn_bclri_valid ? spec_insn_bclri_mem_wmask :
		spec_insn_bext_valid ? spec_insn_bext_mem_wmask :
		spec_insn_bexti_valid ? spec_insn_bexti_mem_wmask :
		spec_insn_binv_valid ? spec_insn_binv_mem_wmask :
		spec_insn_binvi_valid ? spec_insn_binvi_mem_wmask :
		spec_insn_bset_valid ? spec_insn_bset_mem_wmask :
		spec_insn_bseti_valid ? spec_insn_bseti_mem_wmask :
		spec_insn_clmul_valid ? spec_insn_clmul_mem_wmask :
		spec_insn_clmulh_valid ? spec_insn_clmulh_mem_wmask :
		spec_insn_clmulr_valid ? spec_insn_clmulr_mem_wmask :
		spec_insn_clz_valid ? spec_insn_clz_mem_wmask :
		spec_insn_cpop_valid ? spec_insn_cpop_mem_wmask :
		spec_insn_ctz_valid ? spec_insn_ctz_mem_wmask :
		spec_insn_max_valid ? spec_insn_max_mem_wmask :
		spec_insn_maxu_valid ? spec_insn_maxu_mem_wmask :
		spec_insn_min_valid ? spec_insn_min_mem_wmask :
		spec_insn_minu_valid ? spec_insn_minu_mem_wmask :
		spec_insn_orc.b_valid ? spec_insn_orc.b_mem_wmask :
		spec_insn_orn_valid ? spec_insn_orn_mem_wmask :
		spec_insn_rev8_valid ? spec_insn_rev8_mem_wmask :
		spec_insn_rol_valid ? spec_insn_rol_mem_wmask :
		spec_insn_ror_valid ? spec_insn_ror_mem_wmask :
		spec_insn_rori_valid ? spec_insn_rori_mem_wmask :
		spec_insn_sext.b_valid ? spec_insn_sext.b_mem_wmask :
		spec_insn_sext.h_valid ? spec_insn_sext.h_mem_wmask :
		spec_insn_sh1add_valid ? spec_insn_sh1add_mem_wmask :
		spec_insn_sh2add_valid ? spec_insn_sh2add_mem_wmask :
		spec_insn_sh3add_valid ? spec_insn_sh3add_mem_wmask :
		spec_insn_xnor_valid ? spec_insn_xnor_mem_wmask :
		spec_insn_zext.h_valid ? spec_insn_zext.h_mem_wmask : 0;
  assign spec_mem_wdata =
		spec_insn_andn_valid ? spec_insn_andn_mem_wdata :
		spec_insn_bclr_valid ? spec_insn_bclr_mem_wdata :
		spec_insn_bclri_valid ? spec_insn_bclri_mem_wdata :
		spec_insn_bext_valid ? spec_insn_bext_mem_wdata :
		spec_insn_bexti_valid ? spec_insn_bexti_mem_wdata :
		spec_insn_binv_valid ? spec_insn_binv_mem_wdata :
		spec_insn_binvi_valid ? spec_insn_binvi_mem_wdata :
		spec_insn_bset_valid ? spec_insn_bset_mem_wdata :
		spec_insn_bseti_valid ? spec_insn_bseti_mem_wdata :
		spec_insn_clmul_valid ? spec_insn_clmul_mem_wdata :
		spec_insn_clmulh_valid ? spec_insn_clmulh_mem_wdata :
		spec_insn_clmulr_valid ? spec_insn_clmulr_mem_wdata :
		spec_insn_clz_valid ? spec_insn_clz_mem_wdata :
		spec_insn_cpop_valid ? spec_insn_cpop_mem_wdata :
		spec_insn_ctz_valid ? spec_insn_ctz_mem_wdata :
		spec_insn_max_valid ? spec_insn_max_mem_wdata :
		spec_insn_maxu_valid ? spec_insn_maxu_mem_wdata :
		spec_insn_min_valid ? spec_insn_min_mem_wdata :
		spec_insn_minu_valid ? spec_insn_minu_mem_wdata :
		spec_insn_orc.b_valid ? spec_insn_orc.b_mem_wdata :
		spec_insn_orn_valid ? spec_insn_orn_mem_wdata :
		spec_insn_rev8_valid ? spec_insn_rev8_mem_wdata :
		spec_insn_rol_valid ? spec_insn_rol_mem_wdata :
		spec_insn_ror_valid ? spec_insn_ror_mem_wdata :
		spec_insn_rori_valid ? spec_insn_rori_mem_wdata :
		spec_insn_sext.b_valid ? spec_insn_sext.b_mem_wdata :
		spec_insn_sext.h_valid ? spec_insn_sext.h_mem_wdata :
		spec_insn_sh1add_valid ? spec_insn_sh1add_mem_wdata :
		spec_insn_sh2add_valid ? spec_insn_sh2add_mem_wdata :
		spec_insn_sh3add_valid ? spec_insn_sh3add_mem_wdata :
		spec_insn_xnor_valid ? spec_insn_xnor_mem_wdata :
		spec_insn_zext.h_valid ? spec_insn_zext.h_mem_wdata : 0;
`ifdef RISCV_FORMAL_CSR_MISA
  assign spec_csr_misa_rmask =
		spec_insn_andn_valid ? spec_insn_andn_csr_misa_rmask :
		spec_insn_bclr_valid ? spec_insn_bclr_csr_misa_rmask :
		spec_insn_bclri_valid ? spec_insn_bclri_csr_misa_rmask :
		spec_insn_bext_valid ? spec_insn_bext_csr_misa_rmask :
		spec_insn_bexti_valid ? spec_insn_bexti_csr_misa_rmask :
		spec_insn_binv_valid ? spec_insn_binv_csr_misa_rmask :
		spec_insn_binvi_valid ? spec_insn_binvi_csr_misa_rmask :
		spec_insn_bset_valid ? spec_insn_bset_csr_misa_rmask :
		spec_insn_bseti_valid ? spec_insn_bseti_csr_misa_rmask :
		spec_insn_clmul_valid ? spec_insn_clmul_csr_misa_rmask :
		spec_insn_clmulh_valid ? spec_insn_clmulh_csr_misa_rmask :
		spec_insn_clmulr_valid ? spec_insn_clmulr_csr_misa_rmask :
		spec_insn_clz_valid ? spec_insn_clz_csr_misa_rmask :
		spec_insn_cpop_valid ? spec_insn_cpop_csr_misa_rmask :
		spec_insn_ctz_valid ? spec_insn_ctz_csr_misa_rmask :
		spec_insn_max_valid ? spec_insn_max_csr_misa_rmask :
		spec_insn_maxu_valid ? spec_insn_maxu_csr_misa_rmask :
		spec_insn_min_valid ? spec_insn_min_csr_misa_rmask :
		spec_insn_minu_valid ? spec_insn_minu_csr_misa_rmask :
		spec_insn_orc.b_valid ? spec_insn_orc.b_csr_misa_rmask :
		spec_insn_orn_valid ? spec_insn_orn_csr_misa_rmask :
		spec_insn_rev8_valid ? spec_insn_rev8_csr_misa_rmask :
		spec_insn_rol_valid ? spec_insn_rol_csr_misa_rmask :
		spec_insn_ror_valid ? spec_insn_ror_csr_misa_rmask :
		spec_insn_rori_valid ? spec_insn_rori_csr_misa_rmask :
		spec_insn_sext.b_valid ? spec_insn_sext.b_csr_misa_rmask :
		spec_insn_sext.h_valid ? spec_insn_sext.h_csr_misa_rmask :
		spec_insn_sh1add_valid ? spec_insn_sh1add_csr_misa_rmask :
		spec_insn_sh2add_valid ? spec_insn_sh2add_csr_misa_rmask :
		spec_insn_sh3add_valid ? spec_insn_sh3add_csr_misa_rmask :
		spec_insn_xnor_valid ? spec_insn_xnor_csr_misa_rmask :
		spec_insn_zext.h_valid ? spec_insn_zext.h_csr_misa_rmask : 0;
`endif
endmodule
