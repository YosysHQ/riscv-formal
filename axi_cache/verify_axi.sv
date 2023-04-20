`default_nettype none

module resetgen(input wire clock, input wire reset, input wire axi_arvalid, input wire axi_arready);
    initial assume(reset);
endmodule

bind nerv_axi_cache resetgen resetgen(.*);

bind nerv_axi_cache amba_axi4_protocol_checker
  #('{ID_WIDTH:          1,
      ADDRESS_WIDTH:     32,
      DATA_WIDTH:        32,
      AWUSER_WIDTH:      1,
      WUSER_WIDTH:       1,
      BUSER_WIDTH:       1,
      ARUSER_WIDTH:      1,
      RUSER_WIDTH:       1,
      MAX_WR_BURSTS:     1,
      MAX_RD_BURSTS:     1,
      MAX_WR_LENGTH:     2,
      MAX_RD_LENGTH:     2,
      MAXWAIT:           5,
      VERIFY_AGENT_TYPE: amba_axi4_protocol_checker_pkg::SOURCE,
      PROTOCOL_TYPE:     amba_axi4_protocol_checker_pkg::AXI4FULL,
      INTERFACE_REQS:    1,
      ENABLE_COVER:      1,
      ENABLE_XPROP:      0,
      ARM_RECOMMENDED:   1,
      CHECK_PARAMETERS:  1,
      OPTIONAL_WSTRB:    0,
      FULL_WR_STRB:      1,
      OPTIONAL_RESET:    1,
      EXCLUSIVE_ACCESS:  0,
      OPTIONAL_LP:       0})
dest_check (
	    .ACLK(clock),
	    .ARESETn(!reset),

	    .AWID(axi_awid),
	    .AWADDR(axi_awaddr),
	    .AWREGION(axi_awregion),
	    .AWLEN(axi_awlen),
	    .AWSIZE(axi_awsize),
	    .AWBURST(axi_awburst),
	    .AWLOCK(axi_awlock),
	    .AWCACHE(axi_awcache),
	    .AWPROT(axi_awprot),
	    .AWQOS(axi_awqos),
	    .AWVALID(axi_awvalid),
	    .AWREADY(axi_awready),
	    .AWUSER(axi_awuser),

	    .WDATA(axi_wdata),
	    .WSTRB(axi_wstrb),
	    .WLAST(axi_wlast),
	    .WVALID(axi_wvalid),
	    .WREADY(axi_wready),
	    .WUSER(axi_wuser),

	    .BID(axi_bid),
	    .BRESP(axi_bresp),
	    .BVALID(axi_bvalid),
	    .BREADY(axi_bready),
	    .BUSER(axi_buser),

	    .ARID(axi_arid),
	    .ARADDR(axi_araddr),
	    .ARREGION(axi_arregion),
	    .ARLEN(axi_arlen),
	    .ARSIZE(axi_arsize),
	    .ARBURST(axi_arburst),
	    .ARLOCK(axi_arlock),
	    .ARCACHE(axi_arcache),
	    .ARPROT(axi_arprot),
	    .ARQOS(axi_arqos),
	    .ARVALID(axi_arvalid),
	    .ARREADY(axi_arready),
	    .ARUSER(axi_aruser),

	    .RID(axi_rid),
	    .RDATA(axi_rdata),
	    .RRESP(axi_rresp),
	    .RLAST(axi_rlast),
	    .RVALID(axi_rvalid),
	    .RREADY(axi_rready),
	    .RUSER(axi_ruser),

        .CSYSREQ(1'b1),
        .CSYSACK(1'b1),
        .CACTIVE(1'b1)
	    );
