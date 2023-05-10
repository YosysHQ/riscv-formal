/*
 *  NERV -- Naive Educational RISC-V Processor
 *
 *  Copyright (C) 2020  Claire Xenia Wolf <claire@yosyshq.com>
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

module testbench (
	input         clock,
	`RVFI_OUTPUTS
);
	reg reset = 1;
	always @(posedge clock)
		reset <= 0;

	(* keep *) `rvformal_rand_reg stall;
	(* keep *) `rvformal_rand_reg [31:0] imem_data;
	(* keep *) `rvformal_rand_reg [31:0] dmem_rdata;

	(* keep *) wire [31:0] imem_addr;

	(* keep *) wire        dmem_valid;
	(* keep *) wire [31:0] dmem_addr;
	(* keep *) wire [ 3:0] dmem_wstrb;
	(* keep *) wire [31:0] dmem_wdata;

	wire [31:0] check_imem_addr;
	wire [15:0] check_imem_data;

	rvfi_imem_check checker_inst (
		.clock(clock),
		.reset(reset),
		.enable(1'b1),
		.imem_addr(check_imem_addr),
		.imem_data(check_imem_data),
		`RVFI_CONN
	);

	reg [31:0] imem_addr_q;

	always @(posedge clock) begin
		imem_addr_q <= imem_addr;
	end

	always @* begin
		if (!reset && !stall) begin
			if (imem_addr_q == check_imem_addr)
				assume(imem_data[15:0] == check_imem_data);
			if (imem_addr_q+2 == check_imem_addr)
				assume(imem_data[31:16] == check_imem_data);
		end
	end

	nerv uut (
		.clock      (clock    ),
		.reset      (reset    ),
		.stall      (stall    ),

		.imem_addr  (imem_addr ),
		.imem_data  (imem_data ),

		.dmem_valid (dmem_valid),
		.dmem_addr  (dmem_addr ),
		.dmem_wstrb (dmem_wstrb),
		.dmem_wdata (dmem_wdata),
		.dmem_rdata (dmem_rdata),

		`RVFI_CONN
	);

`ifdef NERV_FAIRNESS
	reg [2:0] stalled = 0;
	always @(posedge clock) begin
		stalled <= {stalled, stall};
		assume (~stalled);
	end
`endif
endmodule
