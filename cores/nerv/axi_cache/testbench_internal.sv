// Testbench using the internal bus side interface
/*
 *  NERV -- Naive Educational RISC-V Processor
 *
 *  Copyright (C) 2020  N. Engelhardt <nak@yosyshq.com>
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

module testbench;

localparam MEM_ADDR_WIDTH = 16;
localparam TIMEOUT = (1<<14);

reg clock;
reg reset = 1'b1;
reg stall = 1'b0;
wire trap;

wire [31:0] imem_addr;
wire [31:0] imem_data;

wire        dmem_valid;
wire [31:0] dmem_addr;
wire [ 3:0] dmem_wstrb;
wire [31:0] dmem_wdata;
reg  [31:0] dmem_rdata;

reg  [31:0] irq; initial irq = 0;

always #5 clock = clock === 1'b0;
always @(posedge clock) reset <= 0;

reg [7:0] mem [0:(1<<MEM_ADDR_WIDTH)-1];

wire wr_in_mem_range = (dmem_addr[31:2] < (1<<MEM_ADDR_WIDTH));
wire wr_in_output = (dmem_addr == 32'h 02000000);

reg [31:0] out;
reg out_valid = 0;

int stall_counter = 0;
int nonstall_counter = 0;

always @(posedge clock) begin
	if (stalled)
		stall_counter <= stall_counter + 1;
	else
		nonstall_counter <= nonstall_counter + 1;

	if (out_valid) begin
		if (out[8]) begin $display("%d %d", nonstall_counter, stall_counter); $finish(); end;
		$write("%c", out[7:0]);
		if (out[7:0] == "\n")
			$write("%d %d: ", nonstall_counter, stall_counter);
`ifndef VERILATOR
		$fflush();
`endif
	end
end

`ifdef STALL
always @(posedge clock) begin
	stall <= $random;
end
`endif

always @(posedge clock) begin
	if (imem_addr >= (1<<MEM_ADDR_WIDTH)) begin
		$display("Memory access out of range: imem_addr = 0x%08x", imem_addr);
	end
	if (dmem_valid && !(wr_in_mem_range || wr_in_output)) begin
		$display("Memory access out of range: dmem_addr = 0x%08x", dmem_addr);
	end
end

integer i;
always @(posedge clock) begin
	out <= 32'h 0;
	out_valid <= 1'b0;
	if (!stalled && !reset) begin
		if (dmem_valid) begin
			for (i=0;i<4;i=i+1) begin
				if (dmem_wstrb[i]) begin
					if (wr_in_output) begin
						out[(i*8)+: 8] <= dmem_wdata[(i*8)+: 8];
						out_valid <= 1'b1;
					end
				end
			end
		end
	end

	imem_res_valid <= 0;
	if (imem_req_valid) begin
		for (int i = 0; i < 32; i++) begin
			imem_res_data[i * 8 +: 8] <= mem[imem_req_addr ^ i];
		end
`ifdef STALL
		repeat ($random() & 3) @(posedge clock);
`endif
		imem_res_valid <= 1;
	end

	dmem_res_r_valid <= 0;
	if (dmem_req_r_valid) begin
		for (int i = 0; i < 32; i++) begin
			dmem_res_r_data[i * 8 +: 8] <= mem[dmem_req_r_addr ^ i];
		end
`ifdef STALL
		repeat ($random() & 3) @(posedge clock);
`endif
		dmem_res_r_valid <= 1;
	end

	dmem_res_w_valid <= 0;
	if (dmem_req_w_valid) begin
		for (int i = 0; i < 32; i++) begin
			mem[dmem_req_w_addr ^ i] <= dmem_req_w_data[i * 8 +: 8];
		end
`ifdef STALL
		repeat ($random() & 3) @(posedge clock);
`endif
		dmem_res_w_valid <= 1;
	end
end

initial begin
	$readmemh("firmware.hex", mem);
	if ($test$plusargs("vcd")) begin
		$dumpfile("testbench_internal.vcd");
		$dumpvars(0, testbench);
	end
end

wire icache_stall, dcache_stall;

wire stalled = stall || icache_stall || dcache_stall;

wire [31:0] imem_req_addr;
wire imem_req_valid;

reg [255:0] imem_res_data;
reg imem_res_fault = 0;
reg imem_res_valid = 0;


wire [31:0] dmem_req_r_addr;
wire dmem_req_r_valid;

reg [255:0] dmem_res_r_data;
reg dmem_res_r_fault = 0;
reg dmem_res_r_valid = 0;

wire [31:0] dmem_req_w_addr;
wire [255:0] dmem_req_w_data;
wire dmem_req_w_valid;

reg dmem_res_w_fault = 0;
reg dmem_res_w_valid = 0;

nerv_axi_cache_icache #(.LINE_SIZE(5), .INDEX_SIZE(4)) icache (
	.clock(clock),
	.reset(reset),

	.stalled(stalled),
	.stall(icache_stall),

	.imem_addr(imem_addr),
	.imem_data(imem_data),

	.req_addr(imem_req_addr),
	.req_valid(imem_req_valid),

	.res_data(imem_res_data),
	.res_fault(imem_res_fault),
	.res_valid(imem_res_valid)

);

nerv_axi_cache_dcache #(.LINE_SIZE(5), .INDEX_SIZE(1)) dcache (
	.clock(clock),
	.reset(reset),

	.stalled(stalled),
	.stall(dcache_stall),

	.dmem_valid(dmem_valid && wr_in_mem_range),
	.dmem_addr(dmem_addr),
	.dmem_wstrb(dmem_wstrb),
	.dmem_wdata(dmem_wdata),
	.dmem_rdata(dmem_rdata),

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

nerv dut (
	.clock(clock),
	.reset(reset),
	.stall(stalled),
	.trap(trap),

	.imem_addr(imem_addr),
	.imem_data(stalled ? 32'bx : imem_data),

	.dmem_valid(dmem_valid),
	.dmem_addr(dmem_addr),
	.dmem_wstrb(dmem_wstrb),
	.dmem_wdata(dmem_wdata),
	.dmem_rdata(stalled ? 32'bx : dmem_rdata),

`ifdef NERV_FAULT
	.imem_fault(1'b0),
	.dmem_fault(1'b0),
`endif

	.irq(irq)
);

reg [31:0] cycles = 0;

always @(posedge clock) begin
	cycles <= cycles + 32'h1;
	if (trap || (cycles >= TIMEOUT)) begin
		$display("Simulated %0d cycles", cycles);
		$finish;
	end
end

endmodule
