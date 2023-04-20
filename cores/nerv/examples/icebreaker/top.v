/*
 *  NERV -- Naive Educational RISC-V Processor
 *
 *  Copyright (C) 2020  Miodrag Milanovic <miodrag@yosyshq.com>
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

module top(
	input CLK,
	output LEDR_N,
	output LEDG_N,
	output LED1,
	output LED2,
	output LED3,
	output LED4,
	output LED5
);

// Create reset signal 16 clocks long
reg reset = 1'b1;
reg [3:0] reset_cnt = 0;
always @(posedge CLK)
begin
	reset <= (reset_cnt != 15);
	reset_cnt <= reset_cnt + (reset_cnt != 15);
end

// Map 7 LEDs that exists on icebreaker board
wire [31:0] leds;
assign { LEDR_N, LEDG_N, LED1, LED2, LED3, LED4, LED5 } = {~leds[6:5], leds[4:0]};

nervsoc soc (
	.clock(CLK),
	.reset(reset),
	.leds(leds)
);

endmodule
