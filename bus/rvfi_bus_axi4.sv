// RVFI_BUS observer for AXI4 interfaces
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

module rvfi_bus_axi4_observer_write #(
    parameter AXI_DATA_WIDTH = 32,
    parameter AXI_ADDRESS_WIDTH = 32,
    parameter AXI_ID_WIDTH = 1,
    parameter AXI_AWUSER_WIDTH = 1,
    parameter AXI_WUSER_WIDTH = 1,
    parameter AXI_BUSER_WIDTH = 1,

    parameter AXI_ID_MASK = 0,
    parameter AXI_ID = 0,

    parameter IGNORE_PROT_DATA_INSN = 0,

    parameter DEPTH = 2,

    localparam AXI_STRB_WIDTH = AXI_DATA_WIDTH / 8
) (
	input         clock,
	input         reset,

    // Write Address Channel (AW)
    input [AXI_ID_WIDTH-1:0]       axi_awid,
    input [AXI_ADDRESS_WIDTH-1:0]  axi_awaddr,
    input [3:0]                    axi_awregion,
    input [7:0]                    axi_awlen,
    input [2:0]                    axi_awsize,
    input [1:0]                    axi_awburst,
    input                          axi_awlock,
    input [3:0]                    axi_awcache,
    input [2:0]                    axi_awprot,
    input [3:0]                    axi_awqos,
    input [AXI_AWUSER_WIDTH-1:0]   axi_awuser,
    input                          axi_awvalid,
    input                          axi_awready,
    // Write Data Channel (W)
    input [AXI_DATA_WIDTH-1:0]     axi_wdata,
    input [AXI_STRB_WIDTH-1:0]     axi_wstrb,
    input                          axi_wlast,
    input [AXI_WUSER_WIDTH-1:0]    axi_wuser,
    input                          axi_wvalid,
    input                          axi_wready,
    // Write Response Channel (B)
    input [AXI_ID_WIDTH-1:0]       axi_bid,
    input [1:0]                    axi_bresp,
    input [AXI_BUSER_WIDTH-1:0]    axi_buser,
    input                          axi_bvalid,
    input                          axi_bready

	`RVFI_BUS_CHANNEL_OUTPUTS
);

    wire aw_transfer = axi_awvalid && axi_awready;
    wire w_transfer = axi_wvalid && axi_wready;
    wire b_transfer = axi_bvalid && axi_bready;

    wire [AXI_ID_WIDTH-1:0]       out_awid;
    wire [AXI_ADDRESS_WIDTH-1:0]  out_awaddr;
    wire [7:0]                    out_awlen;
    wire [2:0]                    out_awsize;
    wire [1:0]                    out_awburst;
    wire [2:0]                    out_awprot;

    rvfi_bus_util_fifo #(
        .DEPTH(DEPTH),
        .WIDTH(AXI_ID_WIDTH + AXI_ADDRESS_WIDTH + 8 + 3 + 2 + 3)
    ) aw_fifo (
        .clock(clock),
        .reset(reset),

        .in_data( {axi_awid, axi_awaddr, axi_awlen, axi_awsize, axi_awburst, axi_awprot}),
        .out_data({out_awid, out_awaddr, out_awlen, out_awsize, out_awburst, out_awprot}),

        .in_valid(aw_transfer),
        // TODO check in_ready
        .out_ready(w_transfer && axi_wlast)
        // TODO check out_valid
    );

    reg [7:0] burst_counter; // TODO optionally check and assert axi_rlast?

    always @(posedge clock) begin
        if (w_transfer) begin
            if (axi_wlast) begin
                burst_counter <= 0;
            end else begin
                burst_counter <= burst_counter + 1;
            end
        end
        if (reset) begin
            burst_counter <= 0;
        end
    end

    reg [AXI_ADDRESS_WIDTH-1:0] burst_mask;
    reg [2:0] burst_len_log2;

    always @* begin
        // TODO test this warp logic
        // TODO optionally assert against invalid burst modes?
        case (out_awlen)
            8'h01: burst_len_log2 = 1;
            8'h03: burst_len_log2 = 2;
            8'h07: burst_len_log2 = 3;
            8'h0f: burst_len_log2 = 4;
            default: burst_len_log2 = 0;
        endcase
        case (out_awburst)
            2'b01: burst_mask = {AXI_ADDRESS_WIDTH{1'b1}};
            2'b10: burst_mask = ~({AXI_ADDRESS_WIDTH{1'b1}} << (out_awsize + burst_len_log2));
            default: burst_mask = {AXI_ADDRESS_WIDTH{1'b0}};
        endcase
    end

    assign rvfi_bus_rdata = 'x;
    assign rvfi_bus_wdata = axi_wdata; // TODO explicitly pad
    assign rvfi_bus_wmask = axi_wstrb; // TODO explicitly pad, handle size differences?
    assign rvfi_bus_addr =
        ( burst_mask & (out_awaddr + (burst_counter * (AXI_DATA_WIDTH / 8)))) |
        (~burst_mask & out_awaddr);

    assign rvfi_bus_insn = !IGNORE_PROT_DATA_INSN && out_awprot[2];
    assign rvfi_bus_data = IGNORE_PROT_DATA_INSN || !out_awprot[2];

    assign rvfi_bus_rmask = 0;
    assign rvfi_bus_fault = 0; // TODO use a fifo of prophecy variables to handle bresp arriving later
    assign rvfi_bus_valid = w_transfer && ((axi_awid & AXI_ID_MASK) == AXI_ID);
endmodule

module rvfi_bus_axi4_observer_read #(
    parameter AXI_DATA_WIDTH = 32,
    parameter AXI_ADDRESS_WIDTH = 32,
    parameter AXI_ID_WIDTH = 1,
    parameter AXI_ARUSER_WIDTH = 1,
    parameter AXI_RUSER_WIDTH = 1,

    parameter AXI_ID_MASK = 0,
    parameter AXI_ID = 0,

    parameter DEPTH = 2,

    parameter IGNORE_PROT_DATA_INSN = 0
) (
	input         clock,
	input         reset,

    // Read Address Channel (AR)
    input [AXI_ID_WIDTH-1:0]       axi_arid,
    input [AXI_ADDRESS_WIDTH-1:0]  axi_araddr,
    input [3:0]                    axi_arregion,
    input [7:0]                    axi_arlen,
    input [2:0]                    axi_arsize,
    input [1:0]                    axi_arburst,
    input                          axi_arlock,
    input [3:0]                    axi_arcache,
    input [2:0]                    axi_arprot,
    input [3:0]                    axi_arqos,
    input [AXI_ARUSER_WIDTH-1:0]   axi_aruser,
    input                          axi_arvalid,
    input                          axi_arready,
    // Read Data Channel (R)
    input [AXI_ID_WIDTH-1:0]       axi_rid,
    input [AXI_DATA_WIDTH-1:0]     axi_rdata,
    input [1:0]                    axi_rresp,
    input                          axi_rlast,
    input [AXI_RUSER_WIDTH-1:0]    axi_ruser,
    input                          axi_rvalid,
    input                          axi_rready

	`RVFI_BUS_CHANNEL_OUTPUTS
);

    wire ar_transfer = axi_arvalid && axi_arready;
    wire r_transfer = axi_rvalid && axi_rready;

    wire ar_transfer_match = ar_transfer && ((axi_arid & AXI_ID_MASK) == AXI_ID);
    wire r_transfer_match = r_transfer && ((axi_rid & AXI_ID_MASK) == AXI_ID);


    wire [AXI_ADDRESS_WIDTH-1:0]  out_araddr;
    wire [7:0]                    out_arlen;
    wire [2:0]                    out_arsize;
    wire [1:0]                    out_arburst;
    wire [2:0]                    out_arprot;

    rvfi_bus_util_fifo #(
        .DEPTH(DEPTH),
        .WIDTH(AXI_ADDRESS_WIDTH + 8 + 3 + 2 + 3)
    ) aw_fifo (
        .clock(clock),
        .reset(reset),

        .in_data( {axi_araddr, axi_arlen, axi_arsize, axi_arburst, axi_arprot}),
        .out_data({out_araddr, out_arlen, out_arsize, out_arburst, out_arprot}),

        .in_valid(ar_transfer_match),
        // TODO check in_ready
        .out_ready(r_transfer_match && axi_rlast)
        // TODO check out_valid
    );

    reg [7:0] burst_counter; // TODO optionally check and assert axi_rlast?

    always @(posedge clock) begin
        if (r_transfer_match) begin
            if (axi_rlast) begin
                burst_counter <= 0;
            end else begin
                burst_counter <= burst_counter + 1;
            end
        end
        if (reset) begin
            burst_counter <= 0;
        end
    end

    reg [AXI_ADDRESS_WIDTH-1:0] burst_mask;
    reg [2:0] burst_len_log2;

    always @* begin
        // TODO test this warp logic
        // TODO optionally assert against invalid burst modes?
        case (out_arlen)
            8'h01: burst_len_log2 = 1;
            8'h03: burst_len_log2 = 2;
            8'h07: burst_len_log2 = 3;
            8'h0f: burst_len_log2 = 4;
            default: burst_len_log2 = 0;
        endcase
        case (out_arburst)
            2'b01: burst_mask = {AXI_ADDRESS_WIDTH{1'b1}};
            2'b10: burst_mask = ~({AXI_ADDRESS_WIDTH{1'b1}} << (out_arsize + burst_len_log2));
            default: burst_mask = {AXI_ADDRESS_WIDTH{1'b0}};
        endcase
    end

    // TODO handle smaller transfer sizes

    assign rvfi_bus_rdata = axi_rdata; // TODO explicitly pad
    assign rvfi_bus_wdata = 'x;
    assign rvfi_bus_addr =
        ( burst_mask & (out_araddr + (burst_counter * (AXI_DATA_WIDTH / 8)))) |
        (~burst_mask & out_araddr);
    assign rvfi_bus_rmask = {AXI_DATA_WIDTH{1'b1}}; // TODO explicitly pad
    assign rvfi_bus_insn = IGNORE_PROT_DATA_INSN || out_arprot[2];
    assign rvfi_bus_data = IGNORE_PROT_DATA_INSN || !out_arprot[2];

    assign rvfi_bus_wmask = 0;
    assign rvfi_bus_fault = axi_rresp[1];
    assign rvfi_bus_valid = r_transfer_match;
endmodule

