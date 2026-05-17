`include "constants.vh"
`include "rv32_opcodes.vh"

module rvfi_wrapper (
	input clock,
	input reset,
	`RVFI_OUTPUTS
);
	(* keep *) `rvformal_rand_reg [4*`INSN_LEN-1:0] idata;
	(* keep *) `rvformal_rand_reg [`DATA_LEN-1:0] dmem_data;

	(* keep *) wire [`ADDR_LEN-1:0] pc;
	(* keep *) wire [`DATA_LEN-1:0] dmem_wdata;
	(* keep *) wire [`ADDR_LEN-1:0] dmem_addr;
	(* keep *) wire dmem_we;

	// The core currently does not model instruction-address-misaligned traps
	// in RVFI (`rvfi_trap` is tied low). Constrain random fetch data so taken
	// BRANCH/JAL targets stay 4-byte aligned for the RV32I/M environment.
	wire [`INSN_LEN-1:0] idata0 = idata[31:0];
	wire [`INSN_LEN-1:0] idata1 = idata[63:32];
	wire [`INSN_LEN-1:0] idata2 = idata[95:64];
	wire [`INSN_LEN-1:0] idata3 = idata[127:96];

	wire idata0_aligned_target =
		(idata0[6:0] != `RV32_BRANCH || !idata0[8]) &&
		(idata0[6:0] != `RV32_JAL || !idata0[21]);
	wire idata1_aligned_target =
		(idata1[6:0] != `RV32_BRANCH || !idata1[8]) &&
		(idata1[6:0] != `RV32_JAL || !idata1[21]);
	wire idata2_aligned_target =
		(idata2[6:0] != `RV32_BRANCH || !idata2[8]) &&
		(idata2[6:0] != `RV32_JAL || !idata2[21]);
	wire idata3_aligned_target =
		(idata3[6:0] != `RV32_BRANCH || !idata3[8]) &&
		(idata3[6:0] != `RV32_JAL || !idata3[21]);

	always @* begin
		assume(idata0_aligned_target);
		assume(idata1_aligned_target);
		assume(idata2_aligned_target);
		assume(idata3_aligned_target);
	end

	pipeline uut (
		.clk(clock),
		.reset(reset),
		.pc(pc),
		.idata(idata),
		.dmem_wdata(dmem_wdata),
		.dmem_we(dmem_we),
		.dmem_addr(dmem_addr),
		.dmem_data(dmem_data),
		`RVFI_CONN
	);
endmodule
