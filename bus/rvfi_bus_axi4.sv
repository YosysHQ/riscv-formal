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


// NOTE: When a W transfer happens before the corresponding AW transfer, the
// data appears on the RVFI_BUS signals starting with the cycle of that AW
// transfer, processing at most one W transfer per cycle. This can cause the
// whole burst to be delayed, potentially also delaying the processing of a
// following burst's W transfers even when that burst's AW transfer arrived for
// the first W transfer.
//
// An alternative that could process the W transfers before the AW transfers
// would have to let the solver guess the write addresses. This could cause
// spurious writes to appear that cause an assertion violation in a cycle
// before the actual AW transfer arrives that would constrain the guessed write
// address to be correctly guessed, as the AW transfer cycle is never
// considered by the solver due to the assertion being violated prior to
// reaching that.
//
// Hence, delaying the processing of W transfers until the corresponding AW
// transfer happens is less likely to cause false positives for most reasonable
// properties to check. In any case, writes appear on the RVFI_BUS signals in
// the exact same order as they appear on the AXI bus. When all AW transfers
// are guaranteed to arrive in time for their their first W transfer, the
// writes also appear on the same cycle as the W transfers carrying the data.

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

    wire [AXI_DATA_WIDTH-1:0]     out_wdata;
    wire [AXI_STRB_WIDTH-1:0]     out_wstrb;
    wire                          out_wlast;

    wire aw_fifo_in_ready, aw_fifo_out_valid;
    wire w_fifo_in_ready, w_fifo_out_valid;
    wire fut_b_fifo_in_ready, fut_b_fifo_out_valid;

    `rvformal_rand_reg [1:0] rand_bresp;
    wire [1:0] out_aw_bresp;
    wire [1:0] out_bresp;

    rvfi_bus_util_fifo #(
        .DEPTH(DEPTH),
        .WIDTH(AXI_ID_WIDTH + AXI_ADDRESS_WIDTH + 8 + 3 + 2 + 3 + 2)
    ) aw_fifo (
        .clock(clock),
        .reset(reset),

        .in_data( {axi_awid, axi_awaddr, axi_awlen, axi_awsize, axi_awburst, axi_awprot, rand_bresp}),
        .out_data({out_awid, out_awaddr, out_awlen, out_awsize, out_awburst, out_awprot, out_aw_bresp}),

        .in_valid(aw_transfer),
        .in_ready(aw_fifo_in_ready),
        .out_ready(w_fifo_out_valid && out_wlast),
        .out_valid(aw_fifo_out_valid)
    );

    rvfi_bus_util_fifo #(
        .DEPTH(DEPTH),
        .WIDTH(AXI_DATA_WIDTH + AXI_STRB_WIDTH + 1)
    ) w_fifo (
        .clock(clock),
        .reset(reset),

        .in_data( {axi_wdata, axi_wstrb, axi_wlast}),
        .out_data({out_wdata, out_wstrb, out_wlast}),

        .in_valid(w_transfer),
        .in_ready(w_fifo_in_ready),
        .out_ready(aw_fifo_out_valid),
        .out_valid(w_fifo_out_valid)
    );

    // We enqueue a guessed bresp value when we see an AW transfer and dequeue
    // it when we see a B transfer, then assuming we made a  correct guess.
    // This doesn't have the same problem described in the note above, as the B
    // channel is read by the AXI manager and any reasonable property of the
    // AXI manager regarding the B response cannot fail before the AXI manager
    // actually reads that response.
    rvfi_bus_util_fifo #(
        .DEPTH(DEPTH),
        .WIDTH(2)
    ) fut_b_fifo (
        .clock(clock),
        .reset(reset),

        .in_data( {rand_bresp}),
        .out_data({out_bresp}),

        .in_valid(aw_transfer),
        .in_ready(fut_b_fifo_in_ready),
        .out_ready(b_transfer),
        .out_valid(fut_b_fifo_out_valid)
    );

    always @(posedge clock) begin
        if (!reset) begin
            if (aw_transfer)
                DEPTH_too_small_AW: assert (aw_fifo_in_ready);
            if (aw_transfer)
                DEPTH_too_small_B: assert (fut_b_fifo_in_ready);
            if (w_transfer)
                DEPTH_too_small_W: assert (w_fifo_in_ready);
        end
    end

    reg [7:0] burst_counter;
    reg [AXI_ADDRESS_WIDTH-1:0] burst_offset;

    always @(posedge clock) begin
        if (w_fifo_out_valid && aw_fifo_out_valid) begin
            if (!reset)
                assert (out_wlast == (burst_counter == out_awlen));
            if (out_wlast) begin
                burst_counter <= 0;
                burst_offset <= 0;
            end else begin
                burst_counter <= burst_counter + 1'b1;
                burst_offset <= burst_offset + (1'b1 << out_awsize);
            end
        end
        if (reset) begin
            burst_counter <= 0;
            burst_offset <= 0;
        end
    end

    // Mask of address bits that can change between transfers of the same burst
    // given the current burst type. This is used to compute the unaligned
    // transfer address.
    reg [AXI_ADDRESS_WIDTH-1:0] burst_mask;

    // Log2 of the burst length, used to compute the burst mask for the WRAP
    // burst type.
    reg [2:0] burst_len_log2;

    // Current transfer address, not aligned.
    //
    // When unaligned, it stays unaligned for the entire burst and always
    // increments by the burst size. This means that transfers past the initial
    // can include bytes below this address down to the next size aligned
    // address.
    wire [AXI_ADDRESS_WIDTH-1:0] unaligned_addr =
        ( burst_mask & (out_awaddr + burst_offset)) |
        (~burst_mask & out_awaddr);

    // Current transfer address, aligned to the burst size.
    wire [AXI_ADDRESS_WIDTH-1:0] size_aligned_addr =
        unaligned_addr & ('1 << out_awsize);

    // Current transfer address, aligned to the bus width.
    wire [AXI_ADDRESS_WIDTH-1:0] bus_aligned_addr =
        unaligned_addr & ~(AXI_DATA_WIDTH/8 - 1);

    // Mask of data bytes/strobe bits that are active given the current
    // transfer address and burst size.
    wire [AXI_DATA_WIDTH/8-1:0] size_mask =
        (~('1 << (1 << out_awsize))) << (size_aligned_addr ^ bus_aligned_addr);

    // Mask of data bytes/strobe bits that are active given the current
    // misalignment (subset of size_mask). After the initial transfer in a
    // burst, this is always the same as size_mask, as the transfer includes
    // the remaining bytes that did not fit into the previous transfer.
    wire [AXI_DATA_WIDTH/8-1:0] alignment_mask =
        burst_counter ? size_mask : size_mask & (size_mask << (unaligned_addr ^ size_aligned_addr));

    always @* begin
        case (out_awlen)
            8'h00: burst_len_log2 = 0;
            8'h01: burst_len_log2 = 1;
            8'h03: burst_len_log2 = 2;
            8'h07: burst_len_log2 = 3;
            8'h0f: burst_len_log2 = 4;
            default: begin
                burst_len_log2 = 0;
                AWLEN_invalid_for_AWBURST: assert (reset || !aw_fifo_out_valid || out_awburst != 2'b10);
            end
        endcase
        case (out_awburst)
            // FIXED
            2'b00: burst_mask = '0;
            // INCR
            2'b01: burst_mask = '1;
            // WRAP
            2'b10: burst_mask = ~('1 << (out_awsize + burst_len_log2));
            // reserved
            default: begin
                burst_mask = '0;
                AWBURST_invalid: assert (reset || !aw_fifo_out_valid);
            end
        endcase
    end

    // The AXI spec says that the wstrb bits are restricted by the burst size
    // and alignment.
    //
    // Choosing to pass on invalid wstrb bits or to implicitly clear them could
    // hide bugs in designs that do produce such invalid strobe bits, so we are
    // checking this here.
    always @(posedge clock) begin
        if (!reset && rvfi_bus_valid)
            WSTRB_invalid: assert (!(out_wstrb & ~alignment_mask));
    end

    always @(posedge clock) begin
        if (!reset) begin
            if (b_transfer) begin
                unexpected_B_transfer: assert (fut_b_fifo_out_valid);

                // Only assume this when we can actually pull a not-yet
                // constrained value from the FIFO, so that this assumption
                // cannot hide any AXI signalling errors.
                assume ((out_bresp == axi_bresp) || !fut_b_fifo_out_valid);
            end
        end
    end

    initial begin
        BUSLEN_too_small: assert (AXI_DATA_WIDTH <= `RISCV_FORMAL_BUSLEN);
        XLEN_too_small: assert (AXI_ADDRESS_WIDTH <= `RISCV_FORMAL_XLEN);
    end

    assign rvfi_bus_rdata = '0;
    assign rvfi_bus_wdata = out_wdata;
    assign rvfi_bus_wmask = out_wstrb;
    assign rvfi_bus_addr = bus_aligned_addr;

    assign rvfi_bus_insn = !IGNORE_PROT_DATA_INSN && out_awprot[2];
    assign rvfi_bus_data = IGNORE_PROT_DATA_INSN || !out_awprot[2];

    assign rvfi_bus_rmask = 0;
    assign rvfi_bus_fault = out_aw_bresp[1];
    assign rvfi_bus_valid = w_fifo_out_valid && aw_fifo_out_valid && ((out_awid & AXI_ID_MASK) == AXI_ID);
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

    wire fifo_in_ready, fifo_out_valid;

    rvfi_bus_util_fifo #(
        .DEPTH(DEPTH),
        .WIDTH(AXI_ADDRESS_WIDTH + 8 + 3 + 2 + 3)
    ) aw_fifo (
        .clock(clock),
        .reset(reset),

        .in_data( {axi_araddr, axi_arlen, axi_arsize, axi_arburst, axi_arprot}),
        .out_data({out_araddr, out_arlen, out_arsize, out_arburst, out_arprot}),

        .in_valid(ar_transfer_match),
        .in_ready(fifo_in_ready),
        .out_ready(r_transfer_match && axi_rlast),
        .out_valid(fifo_out_valid)
    );

    always @(posedge clock) begin
        if (!reset) begin
            if (ar_transfer_match)
                DEPTH_too_small: assert (fifo_in_ready);
            if (r_transfer_match)
                unexpected_R_transfer: assert (fifo_out_valid);
        end
    end

    reg [7:0] burst_counter;
    reg [AXI_ADDRESS_WIDTH-1:0] burst_offset;

    always @(posedge clock) begin
        if (r_transfer_match) begin
            if (!reset)
                RLAST_invalid: assert (axi_rlast == (burst_counter == out_arlen));

            if (axi_rlast) begin
                burst_counter <= 0;
                burst_offset <= 0;
            end else begin
                burst_counter <= burst_counter + 1;
                burst_offset <= burst_offset + (1 << out_arsize);
            end
        end
        if (reset) begin
            burst_counter <= 0;
            burst_offset <= 0;
        end
    end

    // Mask of address bits that can change between transfers of the same burst
    // given the current burst type. This is used to compute the unaligned
    // transfer address.
    reg [AXI_ADDRESS_WIDTH-1:0] burst_mask;

    // Log2 of the burst length, used to compute the burst mask for the WRAP
    // burst type.
    reg [2:0] burst_len_log2;

    // Current transfer address, not aligned.
    //
    // When unaligned, it stays unaligned for the entire burst and always
    // increments by the burst size. This means that transfers past the initial
    // can include bytes below this address down to the next size aligned
    // address.
    wire [AXI_ADDRESS_WIDTH-1:0] unaligned_addr =
        ( burst_mask & (out_araddr + burst_offset)) |
        (~burst_mask & out_araddr);

    // Current transfer address, aligned to the burst size.
    wire [AXI_ADDRESS_WIDTH-1:0] size_aligned_addr =
        unaligned_addr & ('1 << out_arsize);

    // Current transfer address, aligned to the bus width.
    wire [AXI_ADDRESS_WIDTH-1:0] bus_aligned_addr =
        unaligned_addr & ~(AXI_DATA_WIDTH/8 - 1);

    // Mask of data bytes/strobe bits that are active given the current
    // transfer address and burst size.
    wire [AXI_DATA_WIDTH/8-1:0] size_mask =
        (~('1 << (1 << out_arsize))) << (size_aligned_addr ^ bus_aligned_addr);

    // Mask of data bytes/strobe bits that are active given the current
    // misalignment (subset of size_mask). After the initial transfer in a
    // burst, this is always the same as size_mask, as the transfer includes
    // the remaining bytes that did not fit into the previous transfer.
    wire [AXI_DATA_WIDTH/8-1:0] alignment_mask =
        burst_counter ? size_mask : size_mask & (size_mask << (unaligned_addr ^ size_aligned_addr));

    always @* begin
        case (out_arlen)
            8'h00: burst_len_log2 = 0;
            8'h01: burst_len_log2 = 1;
            8'h03: burst_len_log2 = 2;
            8'h07: burst_len_log2 = 3;
            8'h0f: burst_len_log2 = 4;
            default: begin
                burst_len_log2 = 0;
                ARLEN_invalid_for_ARBURST: assert (reset || !fifo_out_valid || out_arburst != 2'b10);
            end
        endcase
        case (out_arburst)
            // FIXED
            2'b00: burst_mask = '0;
            // INCR
            2'b01: burst_mask = '1;
            // WRAP
            2'b10: burst_mask = ~('1 << (out_arsize + burst_len_log2));
            // reserved
            default: begin
                burst_mask = '0;
                ARBURST_invalid: assert (reset || !fifo_out_valid);
            end
        endcase
    end

    initial begin
        BUSLEN_too_small: assert (AXI_DATA_WIDTH <= `RISCV_FORMAL_BUSLEN);
        XLEN_too_small: assert (AXI_ADDRESS_WIDTH <= `RISCV_FORMAL_XLEN);
    end

    assign rvfi_bus_rdata = axi_rdata;
    assign rvfi_bus_wdata = '0;
    assign rvfi_bus_addr = bus_aligned_addr;
    assign rvfi_bus_rmask = alignment_mask;
    assign rvfi_bus_insn = IGNORE_PROT_DATA_INSN || out_arprot[2];
    assign rvfi_bus_data = IGNORE_PROT_DATA_INSN || !out_arprot[2];

    assign rvfi_bus_wmask = 0;
    assign rvfi_bus_fault = axi_rresp[1];
    assign rvfi_bus_valid = r_transfer_match;
endmodule
