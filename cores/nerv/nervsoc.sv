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

module nervsoc (
	input clock,
	input reset,
	output reg [31:0] leds
);
	reg [31:0] imem [0:1023];
	reg [31:0] dmem [0:1023];

	wire stall = 0;
	wire trap;

	wire [31:0] imem_addr;
	reg  [31:0] imem_data;

	wire        dmem_valid;
	wire [31:0] dmem_addr;
	wire [3:0]  dmem_wstrb;
	wire [31:0] dmem_wdata;
	reg  [31:0] dmem_rdata;

	initial begin
		$readmemh("firmware.hex", imem);
	end

	always @(posedge clock)
		imem_data <= imem[imem_addr[31:2]];

	always @(posedge clock) begin
		if (dmem_valid) begin
			if (dmem_addr == 32'h 0100_0000) begin
				if (dmem_wstrb[0]) leds[ 7: 0] <= dmem_wdata[ 7: 0];
				if (dmem_wstrb[1]) leds[15: 8] <= dmem_wdata[15: 8];
				if (dmem_wstrb[2]) leds[23:16] <= dmem_wdata[23:16];
				if (dmem_wstrb[3]) leds[31:24] <= dmem_wdata[31:24];
			end else begin
				if (dmem_wstrb[0]) dmem[dmem_addr[31:2]][ 7: 0] <= dmem_wdata[ 7: 0];
				if (dmem_wstrb[1]) dmem[dmem_addr[31:2]][15: 8] <= dmem_wdata[15: 8];
				if (dmem_wstrb[2]) dmem[dmem_addr[31:2]][23:16] <= dmem_wdata[23:16];
				if (dmem_wstrb[3]) dmem[dmem_addr[31:2]][31:24] <= dmem_wdata[31:24];
			end
			dmem_rdata <= dmem[dmem_addr[31:2]];
		end
	end

	nerv cpu (
		.clock     (clock     ),
		.reset     (reset     ),
		.stall     (stall     ),
		.trap      (trap      ),

		.imem_addr (imem_addr ),
		.imem_data (imem_data ),

		.dmem_valid(dmem_valid),
		.dmem_addr (dmem_addr ),
		.dmem_wstrb(dmem_wstrb),
		.dmem_wdata(dmem_wdata),
		.dmem_rdata(dmem_rdata)
	);
endmodule
