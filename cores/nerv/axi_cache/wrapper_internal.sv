/*
 *  NERV -- Naive Educational RISC-V Processor
 *
 *  Copyright (C) 2020  Claire Xenia Wolf <claire@yosyshq.com>
 *  Copyright (C) 2023  Jannis Harder <jix@yosyshq.com> <me@jix.one>
 *
 *  Permission to use, copy, modify, and/or distribute this software for any
 *  purpose with or without fee is hereby granted, provided that the above
 *  copyright notice and this permission notice appear in all copies.
 *
 *  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 *  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 *  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 *  ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 *  WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 *  ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 *  OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 */

module rvfi_wrapper (
	input         clock,
	input         reset,
	`RVFI_OUTPUTS
	`RVFI_BUS_OUTPUTS
);
	(* keep *) `rvformal_rand_reg random_stall;
	(* keep *) `rvformal_rand_reg [31:0] irq;

	wire imem_fault;
	wire dmem_fault;

	(* keep *) wire trap;

	(* keep *) wire [31:0] imem_addr;
	(* keep *) wire [31:0] imem_data;

	(* keep *) wire        dmem_valid;
	(* keep *) wire [31:0] dmem_addr;
	(* keep *) wire [ 3:0] dmem_wstrb;
	(* keep *) wire [31:0] dmem_wdata;
	(* keep *) wire [31:0] dmem_rdata;

	wire icache_stall, dcache_stall;

	wire stall = random_stall || icache_stall || dcache_stall;

	wire [31:0] imem_req_addr;
	wire imem_req_valid;

	reg [255:0] imem_res_data;
	reg imem_res_fault;
	reg imem_res_valid;


	wire [31:0] dmem_req_r_addr;
	wire dmem_req_r_valid;

	reg [255:0] dmem_res_r_data;
	reg dmem_res_r_fault;
	reg dmem_res_r_valid;

	wire [31:0] dmem_req_w_addr;
	wire [255:0] dmem_req_w_data;
	wire dmem_req_w_valid;

	reg dmem_res_w_fault;
	reg dmem_res_w_valid;

	nerv_axi_cache_icache #(.LINE_SIZE(5), .INDEX_SIZE(1)) icache (
		.clock(clock),
		.reset(reset),

		.stalled(stall),
		.stall(icache_stall),

		.imem_addr(imem_addr),
		.imem_data(imem_data),

		.imem_fault(imem_fault),

		.req_addr(imem_req_addr),
		.req_valid(imem_req_valid),

		.res_data(imem_res_data),
		.res_fault(imem_res_fault),
		.res_valid(imem_res_valid)

	);

	nerv_axi_cache_dcache #(.LINE_SIZE(5), .INDEX_SIZE(1)) dcache (
		.clock(clock),
		.reset(reset),

		.stalled(stall),
		.stall(dcache_stall),

		.dmem_valid(dmem_valid),
		.dmem_addr(dmem_addr),
		.dmem_wstrb(dmem_wstrb),
		.dmem_wdata(dmem_wdata),
		.dmem_rdata(dmem_rdata),

		.dmem_fault(dmem_fault),

		.req_r_addr(dmem_req_r_addr),
		.req_r_valid(dmem_req_r_valid),

		.res_r_data(dmem_res_r_data),
		.res_r_fault(dmem_res_r_fault),
		.res_r_valid(dmem_res_r_valid),

		.req_w_addr(dmem_req_w_addr),
		.req_w_data(dmem_req_w_data),
		.req_w_valid(dmem_req_w_valid),

		.res_w_fault(dmem_res_w_fault),
		.res_w_valid(dmem_res_w_valid)

	);

	nerv uut (
		.clock      (clock    ),
		.reset      (reset    ),
		.stall      (stall    ),
		.trap       (trap     ),

		.imem_addr  (imem_addr ),
		.imem_data  (imem_data ),

		.dmem_valid (dmem_valid),
		.dmem_addr  (dmem_addr ),
		.dmem_wstrb (dmem_wstrb),
		.dmem_wdata (dmem_wdata),
		.dmem_rdata (dmem_rdata),

`ifdef NERV_FAULT
		.imem_fault (imem_fault),
		.dmem_fault (dmem_fault),
`endif

		.irq (irq),

		`RVFI_CONN32
	);

`ifdef RISCV_FORMAL_BUS

`define RISCV_FORMAL_CHANNEL_SIGNAL(channels, width, name) \
	(* keep *) reg [(width) - 1:0] imem_``name; assign rvfi_``name[0 * (width) +: (width)] = imem_``name;
`RVFI_BUS_SIGNALS
`undef RISCV_FORMAL_CHANNEL_SIGNAL

`define RISCV_FORMAL_CHANNEL_SIGNAL(channels, width, name) \
	(* keep *) reg [(width) - 1:0] dmem_r_``name; assign rvfi_``name[1 * (width) +: (width)] = dmem_r_``name;
`RVFI_BUS_SIGNALS
`undef RISCV_FORMAL_CHANNEL_SIGNAL

`define RISCV_FORMAL_CHANNEL_SIGNAL(channels, width, name) \
	(* keep *) reg [(width) - 1:0] dmem_w_``name; assign rvfi_``name[2 * (width) +: (width)] = dmem_w_``name;
`RVFI_BUS_SIGNALS
`undef RISCV_FORMAL_CHANNEL_SIGNAL

	(* keep *) `rvformal_rand_reg [`RISCV_FORMAL_BUSLEN-1:0] next_imem_res_data;
	(* keep *) `rvformal_rand_reg next_imem_res_fault;
	(* keep *) `rvformal_rand_reg next_imem_res_valid;

	logic imem_req_valid_q;

	always @(posedge clock) begin
		imem_res_data <= next_imem_res_data;
		imem_res_fault <= next_imem_res_fault;
		imem_res_valid <= next_imem_res_valid && imem_req_valid && !imem_req_valid_q;
		imem_req_valid_q <= imem_req_valid && !reset;
	end

	always @* begin
		imem_bus_addr  = imem_req_addr;
		imem_bus_insn  = 1;
		imem_bus_data  = 0;
		imem_bus_rmask = {`RISCV_FORMAL_BUSLEN / 8{1'b1}};
		imem_bus_wmask = {`RISCV_FORMAL_BUSLEN / 8{1'b0}};
		imem_bus_rdata = next_imem_res_data;
		imem_bus_wdata = 0;
		imem_bus_fault = next_imem_res_fault;
		imem_bus_valid = next_imem_res_valid && imem_req_valid && !imem_req_valid_q;
	end

	(* keep *) `rvformal_rand_reg [`RISCV_FORMAL_BUSLEN-1:0] next_dmem_res_r_data;
	(* keep *) `rvformal_rand_reg next_dmem_res_r_valid;
	(* keep *) `rvformal_rand_reg next_dmem_res_r_fault;

	logic dmem_req_r_valid_q;

	always @(posedge clock) begin
		dmem_res_r_data <= next_dmem_res_r_data;
		dmem_res_r_fault <= next_dmem_res_r_fault;
		dmem_res_r_valid <= next_dmem_res_r_valid && dmem_req_r_valid && !dmem_req_r_valid_q;
		dmem_req_r_valid_q <= dmem_req_r_valid && !reset;
	end

	always @* begin
		dmem_r_bus_addr  = dmem_req_r_addr;
		dmem_r_bus_insn  = 0;
		dmem_r_bus_data  = 1;
		dmem_r_bus_rmask = {`RISCV_FORMAL_BUSLEN / 8{1'b1}};
		dmem_r_bus_wmask = {`RISCV_FORMAL_BUSLEN / 8{1'b0}};
		dmem_r_bus_rdata = next_dmem_res_r_data;
		dmem_r_bus_wdata = 0;
		dmem_r_bus_fault = next_dmem_res_r_fault;
		dmem_r_bus_valid = next_dmem_res_r_valid && dmem_req_r_valid && !dmem_req_r_valid_q;
	end

	(* keep *) `rvformal_rand_reg next_dmem_res_w_valid;
	(* keep *) `rvformal_rand_reg next_dmem_res_w_fault;


	logic dmem_req_w_valid_q;

	always @(posedge clock) begin
		dmem_res_w_valid <= next_dmem_res_w_valid && dmem_req_w_valid && !dmem_req_w_valid_q;
		dmem_res_w_fault <= next_dmem_res_w_fault;
		dmem_req_w_valid_q <= dmem_req_w_valid && !reset;
	end

	always @* begin
		dmem_w_bus_addr  = dmem_req_w_addr;
		dmem_w_bus_insn  = 0;
		dmem_w_bus_data  = 1;
		dmem_w_bus_rmask = {`RISCV_FORMAL_BUSLEN / 8{1'b0}};
		dmem_w_bus_wmask = {`RISCV_FORMAL_BUSLEN / 8{1'b1}};
		dmem_w_bus_rdata = 0;
		dmem_w_bus_wdata = dmem_req_w_data;
		dmem_w_bus_fault = next_dmem_res_w_fault;
		dmem_w_bus_valid = next_dmem_res_w_valid && dmem_req_w_valid && !dmem_req_w_valid_q;
	end
`endif

`ifdef NERV_FAIRNESS
	reg [2:0] stalled = 0;
	always @(posedge clock) begin
		stalled <= {stalled, stall};
		assume (~stalled);
	end
`endif
endmodule
