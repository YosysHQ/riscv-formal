// Testbench using the AXI4 interface
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
wire        imem_fault;

wire        dmem_valid;
wire [31:0] dmem_addr;
wire [ 3:0] dmem_wstrb;
wire [31:0] dmem_wdata;
reg  [31:0] dmem_rdata;
wire        dmem_fault;

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
					end;
				end
			end
		end
	end
end

initial begin
	$readmemh("firmware.hex", mem);
	if ($test$plusargs("vcd")) begin
		$dumpfile("testbench_axi.vcd");
		$dumpvars(0, testbench);
	end
end

wire cache_stall;

wire stalled = stall || cache_stall;

localparam AXI_DATA_WIDTH = 32;

localparam AXI_ADDRESS_WIDTH = 32;
localparam AXI_ID_WIDTH = 1;
localparam AXI_AWUSER_WIDTH = 1;
localparam AXI_WUSER_WIDTH = 1;
localparam AXI_BUSER_WIDTH = 1;
localparam AXI_ARUSER_WIDTH = 1;
localparam AXI_RUSER_WIDTH = 1;
localparam AXI_STRB_WIDTH = AXI_DATA_WIDTH / 8;

logic [AXI_ID_WIDTH-1:0]       axi_awid;
logic [AXI_ADDRESS_WIDTH-1:0]  axi_awaddr;
logic [3:0]                    axi_awregion;
logic [7:0]                    axi_awlen;
logic [2:0]                    axi_awsize;
logic [1:0]                    axi_awburst;
logic                          axi_awlock;
logic [3:0]                    axi_awcache;
logic [2:0]                    axi_awprot;
logic [3:0]                    axi_awqos;
logic [AXI_AWUSER_WIDTH-1:0]   axi_awuser;
logic                          axi_awvalid;
logic                          axi_awready;
// Write Data Channel (W)
logic [AXI_DATA_WIDTH-1:0]     axi_wdata;
logic [AXI_STRB_WIDTH-1:0]     axi_wstrb;
logic                          axi_wlast;
logic [AXI_WUSER_WIDTH-1:0]    axi_wuser;
logic                          axi_wvalid;
logic                          axi_wready;
// Write Response Channel (B)
logic [AXI_ID_WIDTH-1:0]       axi_bid;
logic [1:0]                    axi_bresp;
logic [AXI_BUSER_WIDTH-1:0]    axi_buser;
logic                          axi_bvalid;
logic                          axi_bready;
// Read Address Channel (AR)
logic [AXI_ID_WIDTH-1:0]       axi_arid;
logic [AXI_ADDRESS_WIDTH-1:0]  axi_araddr;
logic [3:0]                    axi_arregion;
logic [7:0]                    axi_arlen;
logic [2:0]                    axi_arsize;
logic [1:0]                    axi_arburst;
logic                          axi_arlock;
logic [3:0]                    axi_arcache;
logic [2:0]                    axi_arprot;
logic [3:0]                    axi_arqos;
logic [AXI_ARUSER_WIDTH-1:0]   axi_aruser;
logic                          axi_arvalid;
logic                          axi_arready;
// Read Data Channel (R)
logic [AXI_ID_WIDTH-1:0]       axi_rid;
logic [AXI_DATA_WIDTH-1:0]     axi_rdata;
logic [1:0]                    axi_rresp;
logic                          axi_rlast;
logic [AXI_RUSER_WIDTH-1:0]    axi_ruser;
logic                          axi_rvalid;
logic                          axi_rready;


axi_ram #(
	.ID_WIDTH(1)
) ram (
	.clk(clock),
	.rst(reset),
	// Write Address Channel (AW)
	.s_axi_awid(axi_awid),
	.s_axi_awaddr(axi_awaddr[15:0]),
	.s_axi_awlen(axi_awlen),
	.s_axi_awsize(axi_awsize),
	.s_axi_awburst(axi_awburst),
	.s_axi_awlock(axi_awlock),
	.s_axi_awcache(axi_awcache),
	.s_axi_awprot(axi_awprot),
	.s_axi_awvalid(axi_awvalid),
	.s_axi_awready(axi_awready),
	// Write Data Channel (W)
	.s_axi_wdata(axi_wdata),
	.s_axi_wstrb(axi_wstrb),
	.s_axi_wlast(axi_wlast),
	.s_axi_wvalid(axi_wvalid),
	.s_axi_wready(axi_wready),
	// Write Response Channel (B)
	.s_axi_bid(axi_bid),
	.s_axi_bresp(axi_bresp),
	.s_axi_bvalid(axi_bvalid),
	.s_axi_bready(axi_bready),
	// Read Address Channel (AR)
	.s_axi_arid(axi_arid),
	.s_axi_araddr(axi_araddr[15:0]),
	.s_axi_arlen(axi_arlen),
	.s_axi_arsize(axi_arsize),
	.s_axi_arburst(axi_arburst),
	.s_axi_arlock(axi_arlock),
	.s_axi_arcache(axi_arcache),
	.s_axi_arprot(axi_arprot),
	.s_axi_arvalid(axi_arvalid),
	.s_axi_arready(axi_arready),
	// Read Data Channel (R)
	.s_axi_rid(axi_rid),
	.s_axi_rdata(axi_rdata),
	.s_axi_rresp(axi_rresp),
	.s_axi_rlast(axi_rlast),
	.s_axi_rvalid(axi_rvalid),
	.s_axi_rready(axi_rready)
);

initial begin
	#1;
	for (int i = 0; i < (1<<MEM_ADDR_WIDTH) / 4; i++) begin
		ram.mem[i] = 0;

		for (int j = 0; j < 4; j++) begin
			ram.mem[i][j * 8 +: 8] = mem[i * 4 + j];
		end
	end
end

logic inject_fault = 0;

`ifdef INJECT_FAULT
always @(posedge clock) begin
	inject_fault <= $random < (32'hffff_ffff / 200);
end
`endif

nerv_axi_cache cache (
	.clock(clock),
	.reset(reset),

	.stalled(stalled),
	.stall(cache_stall),

	.imem_addr(imem_addr),
	.imem_data(imem_data),
	.imem_fault(imem_fault),

	.dmem_valid(dmem_valid && wr_in_mem_range),
	.dmem_addr(dmem_addr),
	.dmem_wstrb(dmem_wstrb),
	.dmem_wdata(dmem_wdata),
	.dmem_rdata(dmem_rdata),
	.dmem_fault(dmem_fault),

	.dmem_io(1'b1),

	// Write Address Channel (AW)
	.axi_awid(axi_awid),
	.axi_awaddr(axi_awaddr),
	.axi_awregion(axi_awregion),
	.axi_awlen(axi_awlen),
	.axi_awsize(axi_awsize),
	.axi_awburst(axi_awburst),
	.axi_awlock(axi_awlock),
	.axi_awcache(axi_awcache),
	.axi_awprot(axi_awprot),
	.axi_awqos(axi_awqos),
	.axi_awuser(axi_awuser),
	.axi_awvalid(axi_awvalid),
	.axi_awready(axi_awready),
	// Write Data Channel (W)
	.axi_wdata(axi_wdata),
	.axi_wstrb(axi_wstrb),
	.axi_wlast(axi_wlast),
	.axi_wuser(axi_wuser),
	.axi_wvalid(axi_wvalid),
	.axi_wready(axi_wready),
	// Write Response Channel (B)
	.axi_bid(axi_bid),
	.axi_bresp(axi_bresp),
	.axi_buser(axi_buser),
	.axi_bvalid(axi_bvalid),
	.axi_bready(axi_bready),
	// Read Address Channel (AR)
	.axi_arid(axi_arid),
	.axi_araddr(axi_araddr),
	.axi_arregion(axi_arregion),
	.axi_arlen(axi_arlen),
	.axi_arsize(axi_arsize),
	.axi_arburst(axi_arburst),
	.axi_arlock(axi_arlock),
	.axi_arcache(axi_arcache),
	.axi_arprot(axi_arprot),
	.axi_arqos(axi_arqos),
	.axi_aruser(axi_aruser),
	.axi_arvalid(axi_arvalid),
	.axi_arready(axi_arready),
	// Read Data Channel (R)
	.axi_rid(axi_rid),
	.axi_rdata(axi_rdata),
	.axi_rresp(axi_rresp | {inject_fault && !axi_arprot[2], 1'b0}),
	.axi_rlast(axi_rlast),
	.axi_ruser(axi_ruser),
	.axi_rvalid(axi_rvalid),
	.axi_rready(axi_rready)
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
	.imem_fault(imem_fault),
	.dmem_fault(dmem_fault),
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
