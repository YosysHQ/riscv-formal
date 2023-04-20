// Utility code for RVFI_BUS observers
//
// Copyright (C) 2023  Jannis Harder <jix@yosyshq.com> <me@jix.one>
//
// Permission to use, copy, modify, and/or distribute this software for any
// purpose with or without fee is hereby granted, provided that the above
// copyright notice and this permission notice appear in all copies.
//
// THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
// WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
// ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
// WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
// ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
// OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

module rvfi_bus_util_fifo_stage #(
	parameter WIDTH = 8
) (
	input clock,
	input reset,

	input              in_valid,
	output             in_ready,
	input  [WIDTH-1:0] in_data,

	output             out_valid,
	input              out_ready,
	output [WIDTH-1:0] out_data
);

	reg [WIDTH-1:0] buffered;
	reg buffer_valid;

	wire in_txn = in_valid && in_ready;
	wire out_txn = out_valid && out_ready;

	assign out_data = buffer_valid ? buffered : in_data;
	assign in_ready = out_ready || !buffer_valid;
	assign out_valid = in_valid || buffer_valid;

	always @(posedge clock) begin
		if (reset) begin
			buffer_valid <= 0;
		end else begin
			if (in_txn != out_txn)
				buffer_valid <= in_txn;
		end
		if (in_txn)
			buffered <= in_data;
	end

endmodule

module rvfi_bus_util_fifo #(
	parameter WIDTH = 8,
	parameter DEPTH = 3
) (
	input clock,
	input reset,

	input              in_valid,
	output             in_ready,
	input  [WIDTH-1:0] in_data,

	output             out_valid,
	input              out_ready,
	output [WIDTH-1:0] out_data
);

	wire [WIDTH-1:0] stage_data [0:DEPTH];
	wire [DEPTH:0] stage_valid;
	wire [DEPTH:0] stage_ready;

	genvar i;
	generate for (i = 0; i < DEPTH; i = i + 1) begin
		rvfi_bus_util_fifo_stage #(.WIDTH(WIDTH)) stage (
			.clock(clock),
			.reset(reset),
			.in_data(stage_data[i]),
			.out_data(stage_data[i+1]),
			.in_valid(stage_valid[i]),
			.out_valid(stage_valid[i+1]),
			.in_ready(stage_ready[i]),
			.out_ready(stage_ready[i+1])
		);
	end endgenerate

	assign stage_valid[0] = in_valid;
	assign stage_data[0] = in_data;
	assign in_ready = stage_ready[0];

	assign out_valid = stage_valid[DEPTH];
	assign stage_ready[DEPTH] = out_ready;
	assign out_data = stage_data[DEPTH];
endmodule
