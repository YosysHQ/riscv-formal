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

`default_nettype wire

module rvfi_wrapper (
	input         clock,
	input         reset,
	`RVFI_OUTPUTS
	`RVFI_BUS_OUTPUTS
);
	(* keep *) `rvformal_rand_reg random_stall;
	wire cache_stall;

	(* keep *) `rvformal_rand_reg [31:0] random_imem_data;

	wire [31:0] imem_addr;
	wire [31:0] imem_data;
	wire        imem_fault;

	wire        dmem_valid;
	wire [31:0] dmem_addr;
	wire [ 3:0] dmem_wstrb;
	wire [31:0] dmem_wdata;
	wire [31:0] dmem_rdata;
	wire        dmem_fault;

	wire stall = random_stall || cache_stall;

	wire trap;

	nerv #(
	) uut (
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

		.irq (0),

		`RVFI_CONN32
	);

	localparam AXI_DATA_WIDTH = 32;
	localparam AXI_ADDRESS_WIDTH = 32;
	localparam AXI_ID_WIDTH = 1;
	localparam AXI_AWUSER_WIDTH = 1;
	localparam AXI_WUSER_WIDTH = 1;
	localparam AXI_BUSER_WIDTH = 1;
	localparam AXI_ARUSER_WIDTH = 1;
	localparam AXI_RUSER_WIDTH = 1;
	localparam AXI_STRB_WIDTH = AXI_DATA_WIDTH / 8;

	wire [AXI_ID_WIDTH-1:0]       axi_awid;
	wire [AXI_ADDRESS_WIDTH-1:0]  axi_awaddr;
	wire [3:0]                    axi_awregion;
	wire [7:0]                    axi_awlen;
	wire [2:0]                    axi_awsize;
	wire [1:0]                    axi_awburst;
	wire                          axi_awlock;
	wire [3:0]                    axi_awcache;
	wire [2:0]                    axi_awprot;
	wire [3:0]                    axi_awqos;
	wire [AXI_AWUSER_WIDTH-1:0]   axi_awuser;
	wire                          axi_awvalid;
	wire                          axi_awready;
	// Write Data Channel (W)
	wire [AXI_DATA_WIDTH-1:0]     axi_wdata;
	wire [AXI_STRB_WIDTH-1:0]     axi_wstrb;
	wire                          axi_wlast;
	wire [AXI_WUSER_WIDTH-1:0]    axi_wuser;
	wire                          axi_wvalid;
	wire                          axi_wready;
	// Write Response Channel (B)
	wire [AXI_ID_WIDTH-1:0]       axi_bid;
	wire [1:0]                    axi_bresp;
	wire [AXI_BUSER_WIDTH-1:0]    axi_buser;
	wire                          axi_bvalid;
	wire                          axi_bready;
	// Read Address Channel (AR)
	wire [AXI_ID_WIDTH-1:0]       axi_arid;
	wire [AXI_ADDRESS_WIDTH-1:0]  axi_araddr;
	wire [3:0]                    axi_arregion;
	wire [7:0]                    axi_arlen;
	wire [2:0]                    axi_arsize;
	wire [1:0]                    axi_arburst;
	wire                          axi_arlock;
	wire [3:0]                    axi_arcache;
	wire [2:0]                    axi_arprot;
	wire [3:0]                    axi_arqos;
	wire [AXI_ARUSER_WIDTH-1:0]   axi_aruser;
	wire                          axi_arvalid;
	wire                          axi_arready;
	// Read Data Channel (R)
	wire [AXI_ID_WIDTH-1:0]       axi_rid;
	wire [AXI_DATA_WIDTH-1:0]     axi_rdata;
	wire [1:0]                    axi_rresp;
	wire                          axi_rlast;
	wire [AXI_RUSER_WIDTH-1:0]    axi_ruser;
	wire                          axi_rvalid;
	wire                          axi_rready;


	nerv_axi_cache #(
		.AXI_DATA_WIDTH(AXI_DATA_WIDTH),
		.LINE_SIZE(3),
		.ICACHE_INDEX_SIZE(1),
		.DCACHE_INDEX_SIZE(1)
	) cache (
		.clock(clock),
		.reset(reset),

		.stalled(stall),
		.stall(cache_stall),

		.imem_addr(imem_addr),
		.imem_data(imem_data),
		.imem_fault(imem_fault),

		.dmem_valid(dmem_valid),
		.dmem_addr(dmem_addr),
		.dmem_wstrb(dmem_wstrb),
		.dmem_wdata(dmem_wdata),
		.dmem_rdata(dmem_rdata),
		.dmem_fault(dmem_fault),

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
		.axi_rresp(axi_rresp),
		.axi_rlast(axi_rlast),
		.axi_ruser(axi_ruser),
		.axi_rvalid(axi_rvalid),
		.axi_rready(axi_rready)
	);

	rvfi_bus_axi4_observer_write axi_write (
		.clock(clock),
		.reset(reset),

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
		.axi_bready(axi_bready)

		`RVFI_BUS_CHANNEL_CONN(0)
	);


	rvfi_bus_axi4_observer_read axi_read (
		.clock(clock),
		.reset(reset),

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
		.axi_rresp(axi_rresp),
		.axi_rlast(axi_rlast),
		.axi_ruser(axi_ruser),
		.axi_rvalid(axi_rvalid),
		.axi_rready(axi_rready)

		`RVFI_BUS_CHANNEL_CONN(1)
	);


	axi_ram_abstraction #(
		.ID_WIDTH(1),
		.ADDR_WIDTH(32)
	) ram (
		.clk(clock),
		.rst(reset),
		// Write Address Channel (AW)
		.s_axi_awid(axi_awid),
		.s_axi_awaddr(axi_awaddr),
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
		.s_axi_araddr(axi_araddr),
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


`ifdef NERV_FAIRNESS
	reg [2:0] stalled = 0;
	always @(posedge clock) begin
		stalled <= {stalled, random_stall};
		assume (~stalled);
	end
`endif
endmodule
