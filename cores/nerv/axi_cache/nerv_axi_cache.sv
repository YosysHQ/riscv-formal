// Direct mapped, write-back/write-allocate AXI cache for the NERV core.
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

`default_nettype none

// The complete AXI cache.
//
// Provides NERV's native `imem_*` and `dmem_*` interface on one side and an
// AXI4 manager interface on the other side.
//
// The NERV core expects single cycle accesses for both instruction and data
// memory, and has a single `stall` signal that needs to be asserted to halt
// the core when accesses take logner. To support multiplexing between the
// cache and uncached memory/devices on the NERV side, this cache provides a
// `stall` output and a `stalled` input. The `stalled` signal should be
// connected to the same signal as NERV's `stall` input while NERV's `stall`
// input should be an or of the cache's `stall` output with any other external
// stall signal.
//
// ## Parameters
//
// This uses the convention that `<NAME>_WIDTH` = `8 << <NAME>_SIZE`.
//
// * `ADDRESS_WIDTH`: Address bit width for both AXI and NERV's interface. NERV
//   only supports 32 bit, but the cache is generic.
//
// * `DATA_SIZE`: Data size for NERV's interface, NERV only supports 2
//   (corresponding to 32-bit).
//
// * `INSN_SIZE`: Instruction size for NERV's interface, NERV only supports 2
//   (corresponding to 32-bit).
//
// * `LINE_SIZE`: Size of a cache line, needs to be  larger than the maximum of
//   `DATA_SIZE` and `INSN_SIZE` (corresponding to a cache line that is at
//   least twice as wide as the NERV side accesses).
//
// * `ICACHE_INDEX_SIZE`, `DCACHE_INDEX_SIZE`: How many address bits are used
//   to index the instruction/data cache memory. The size of the corresponding
//   cache is `1 << INDEX_SIZE` cache lines.
//
// * `AXI_DATA_WIDTH`: Data width of the AXI interface, independent from the
//   the widths used for NERV's interface.
//
// * `AXI_ID_WIDTH`: ID width for the AXI interface, doesn't affect NERV's
//   interface.
//
// * `AXI_IMEM_ID`, `AXI_DMEM_ID`: which AXI ID to use for instruction and data
//   accesses. Can be the same.
module nerv_axi_cache #(
    parameter ADDRESS_WIDTH = 32,
    parameter DATA_SIZE = 2,
    parameter INSN_SIZE = 2,
    parameter LINE_SIZE = 3,
    parameter ICACHE_INDEX_SIZE = 3,
    parameter DCACHE_INDEX_SIZE = 3,

    parameter AXI_DATA_WIDTH = 32,
    parameter AXI_ID_WIDTH = 1,

    parameter AXI_IMEM_ID = 0,
    parameter AXI_DMEM_ID = 1,

    localparam INSN_WIDTH = 8 << INSN_SIZE,
    localparam DATA_WIDTH = 8 << DATA_SIZE,
    localparam LINE_WIDTH = 8 << LINE_SIZE,

    localparam AXI_ADDRESS_WIDTH = ADDRESS_WIDTH,
    localparam AXI_AWUSER_WIDTH = 1,
    localparam AXI_WUSER_WIDTH = 1,
    localparam AXI_BUSER_WIDTH = 1,
    localparam AXI_ARUSER_WIDTH = 1,
    localparam AXI_RUSER_WIDTH = 1,
    localparam AXI_STRB_WIDTH = AXI_DATA_WIDTH / 8
) (
    input wire clock,
    input wire reset,

    input wire stalled,
    output var stall,

    input wire [ADDRESS_WIDTH-1:0]   imem_addr,
    output var [INSN_WIDTH-1:0]      imem_data,
    output var                       imem_fault,

    // the other is data memory
    input wire                       dmem_valid,
    input wire [ADDRESS_WIDTH-1:0]   dmem_addr,
    input wire [DATA_WIDTH/8-1:0]    dmem_wstrb,
    input wire [DATA_WIDTH-1:0]      dmem_wdata,
    output var [DATA_WIDTH-1:0]      dmem_rdata,
    output var                       dmem_fault,

    // Write Address Channel (AW)
    output var [AXI_ID_WIDTH-1:0]       axi_awid,
    output var [AXI_ADDRESS_WIDTH-1:0]  axi_awaddr,
    output var [3:0]                    axi_awregion,  // not used, default value
    output var [7:0]                    axi_awlen,
    output var [2:0]                    axi_awsize,
    output var [1:0]                    axi_awburst,
    output var                          axi_awlock,    // not used, default value
    output var [3:0]                    axi_awcache,   // not used, fixed value
    output var [2:0]                    axi_awprot,
    output var [3:0]                    axi_awqos,     // not used, default value
    output var [AXI_AWUSER_WIDTH-1:0]   axi_awuser,    // not used, all zero
    output var                          axi_awvalid,
    input wire                          axi_awready,
    // Write Data Channel (W)
    output var [AXI_DATA_WIDTH-1:0]     axi_wdata,
    output var [AXI_STRB_WIDTH-1:0]     axi_wstrb,
    output var                          axi_wlast,
    output var [AXI_WUSER_WIDTH-1:0]    axi_wuser,     // not used, all zero
    output var                          axi_wvalid,
    input wire                          axi_wready,
    // Write Response Channel (B)
    input wire [AXI_ID_WIDTH-1:0]       axi_bid,       // ignored, cache does not use overlapping transactions
    input wire [1:0]                    axi_bresp,     // ignored, cache does not handle faults during writeback
    input wire [AXI_BUSER_WIDTH-1:0]    axi_buser,     // ignored
    input wire                          axi_bvalid,
    output var                          axi_bready,
    // Read Address Channel (AR)
    output var [AXI_ID_WIDTH-1:0]       axi_arid,
    output var [AXI_ADDRESS_WIDTH-1:0]  axi_araddr,
    output var [3:0]                    axi_arregion,  // not used, default value
    output var [7:0]                    axi_arlen,
    output var [2:0]                    axi_arsize,
    output var [1:0]                    axi_arburst,
    output var                          axi_arlock,    // not used, default value
    output var [3:0]                    axi_arcache,   // not used, fixed value
    output var [2:0]                    axi_arprot,
    output var [3:0]                    axi_arqos,     // not used, default value
    output var [AXI_ARUSER_WIDTH-1:0]   axi_aruser,    // not used, all zero
    output var                          axi_arvalid,
    input wire                          axi_arready,
    // Read Data Channel (R)
    input wire [AXI_ID_WIDTH-1:0]       axi_rid,       // ignored, cache does not use overlapping transactions
    input wire [AXI_DATA_WIDTH-1:0]     axi_rdata,
    input wire [1:0]                    axi_rresp,
    input wire                          axi_rlast,
    input wire [AXI_RUSER_WIDTH-1:0]    axi_ruser,     // ignored
    input wire                          axi_rvalid,
    output var                          axi_rready

);

    logic [ADDRESS_WIDTH-1:0]   imem_req_addr;
    logic                       imem_req_valid;

    logic [LINE_WIDTH-1:0]      imem_res_data;
    logic                       imem_res_fault;
    logic                       imem_res_valid;

    logic [ADDRESS_WIDTH-1:0]   dmem_req_r_addr;
    logic                       dmem_req_r_valid;

    logic [LINE_WIDTH-1:0]      dmem_res_r_data;
    logic                       dmem_res_r_fault;
    logic                       dmem_res_r_valid;

    logic [ADDRESS_WIDTH-1:0]   dmem_req_w_addr;
    logic [LINE_WIDTH-1:0]      dmem_req_w_data;
    logic                       dmem_req_w_valid;

    logic                       dmem_res_w_fault;
    logic                       dmem_res_w_valid;

    logic icache_stall, dcache_stall;

    assign stall = icache_stall || dcache_stall;

    nerv_axi_cache_axi #(
        .ADDRESS_WIDTH(ADDRESS_WIDTH),
        .DATA_SIZE(DATA_SIZE),
        .INSN_SIZE(INSN_SIZE),
        .LINE_SIZE(LINE_SIZE),
        .AXI_DATA_WIDTH(AXI_DATA_WIDTH),
        .AXI_ID_WIDTH(AXI_ID_WIDTH),

        .AXI_IMEM_ID(AXI_IMEM_ID),
        .AXI_DMEM_ID(AXI_DMEM_ID)
    ) axi (
        .clock(clock),
        .reset(reset),

        .imem_req_addr(imem_req_addr),
        .imem_req_valid(imem_req_valid),

        .imem_res_data(imem_res_data),
        .imem_res_fault(imem_res_fault),
        .imem_res_valid(imem_res_valid),

        .dmem_req_r_addr(dmem_req_r_addr),
        .dmem_req_r_valid(dmem_req_r_valid),

        .dmem_res_r_data(dmem_res_r_data),
        .dmem_res_r_fault(dmem_res_r_fault),
        .dmem_res_r_valid(dmem_res_r_valid),

        .dmem_req_w_addr(dmem_req_w_addr),
        .dmem_req_w_data(dmem_req_w_data),
        .dmem_req_w_valid(dmem_req_w_valid),

        .dmem_res_w_fault(dmem_res_w_fault),
        .dmem_res_w_valid(dmem_res_w_valid),

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


    nerv_axi_cache_icache #(
        .ADDRESS_WIDTH(ADDRESS_WIDTH),
        .INSN_SIZE(INSN_SIZE),
        .LINE_SIZE(LINE_SIZE),
        .INDEX_SIZE(ICACHE_INDEX_SIZE)
    ) icache (
        .clock(clock),
        .reset(reset),

        .stalled(stalled),
        .stall(icache_stall),

        .imem_addr(imem_addr),
        .imem_data(imem_data),
        .imem_fault(imem_fault),

        .req_addr(imem_req_addr),
        .req_valid(imem_req_valid),

        .res_data(imem_res_data),
        .res_fault(imem_res_fault),
        .res_valid(imem_res_valid)
    );

    nerv_axi_cache_dcache #(
        .ADDRESS_WIDTH(ADDRESS_WIDTH),
        .DATA_SIZE(DATA_SIZE),
        .LINE_SIZE(LINE_SIZE),
        .INDEX_SIZE(DCACHE_INDEX_SIZE)
    ) dcache (
        .clock(clock),
        .reset(reset),

        .stalled(stalled),
        .stall(dcache_stall),

        .dmem_valid(dmem_valid),
        .dmem_addr(dmem_addr),
        .dmem_wstrb(dmem_wstrb),
        .dmem_wdata(dmem_wdata),
        .dmem_rdata(dmem_rdata),
        .dmem_fault(dmem_fault),

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

endmodule

// AXI protocol handling
//
// This has the AXI interface on one side and the actual instruction and data
// caches on the other side. The caches are interfaced using an internal
// interface ({imem,dmem}_{req,res}_{r,w}_*) that transfers whole cache lines
// at once.
//
// See `nerv_axi_cache` for parameter descriptions.
module nerv_axi_cache_axi #(
    parameter ADDRESS_WIDTH = 32,
    parameter DATA_SIZE = 2,
    parameter INSN_SIZE = 2,
    parameter LINE_SIZE = 3,

    parameter AXI_DATA_WIDTH = 32,
    parameter AXI_ID_WIDTH = 1,

    parameter AXI_IMEM_ID = 0,
    parameter AXI_DMEM_ID = 1,

    localparam INSN_WIDTH = 8 << INSN_SIZE,
    localparam DATA_WIDTH = 8 << DATA_SIZE,
    localparam LINE_WIDTH = 8 << LINE_SIZE,

    localparam AXI_ADDRESS_WIDTH = ADDRESS_WIDTH,
    localparam AXI_AWUSER_WIDTH = 1,
    localparam AXI_WUSER_WIDTH = 1,
    localparam AXI_BUSER_WIDTH = 1,
    localparam AXI_ARUSER_WIDTH = 1,
    localparam AXI_RUSER_WIDTH = 1,
    localparam AXI_STRB_WIDTH = AXI_DATA_WIDTH / 8
) (
    input wire clock,
    input wire reset,

    input wire [ADDRESS_WIDTH-1:0]   imem_req_addr,
    input wire                       imem_req_valid,

    output var [LINE_WIDTH-1:0]      imem_res_data,
    output var                       imem_res_fault,
    output var                       imem_res_valid,


    input wire [ADDRESS_WIDTH-1:0]   dmem_req_r_addr,
    input wire                       dmem_req_r_valid,

    output var [LINE_WIDTH-1:0]      dmem_res_r_data,
    output var                       dmem_res_r_fault,
    output var                       dmem_res_r_valid,

    input wire [ADDRESS_WIDTH-1:0]   dmem_req_w_addr,
    input wire [LINE_WIDTH-1:0]      dmem_req_w_data,
    input wire                       dmem_req_w_valid,

    output var                       dmem_res_w_fault,
    output var                       dmem_res_w_valid,

    // Write Address Channel (AW)
    output var [AXI_ID_WIDTH-1:0]       axi_awid,
    output var [AXI_ADDRESS_WIDTH-1:0]  axi_awaddr,
    output var [3:0]                    axi_awregion,  // not used, default value
    output var [7:0]                    axi_awlen,
    output var [2:0]                    axi_awsize,
    output var [1:0]                    axi_awburst,
    output var                          axi_awlock,    // not used, default value
    output var [3:0]                    axi_awcache,   // not used, fixed value
    output var [2:0]                    axi_awprot,
    output var [3:0]                    axi_awqos,     // not used, default value
    output var [AXI_AWUSER_WIDTH-1:0]   axi_awuser,    // not used, all zero
    output var                          axi_awvalid,
    input wire                          axi_awready,
    // Write Data Channel (W)
    output var [AXI_DATA_WIDTH-1:0]     axi_wdata,
    output var [AXI_STRB_WIDTH-1:0]     axi_wstrb,
    output var                          axi_wlast,
    output var [AXI_WUSER_WIDTH-1:0]    axi_wuser,     // not used, all zero
    output var                          axi_wvalid,
    input wire                          axi_wready,
    // Write Response Channel (B)
    input wire [AXI_ID_WIDTH-1:0]       axi_bid,       // ignored, cache does not use overlapping transactions
    input wire [1:0]                    axi_bresp,     // ignored, cache does not handle faults during writeback
    input wire [AXI_BUSER_WIDTH-1:0]    axi_buser,     // ignored
    input wire                          axi_bvalid,
    output var                          axi_bready,
    // Read Address Channel (AR)
    output var [AXI_ID_WIDTH-1:0]       axi_arid,
    output var [AXI_ADDRESS_WIDTH-1:0]  axi_araddr,
    output var [3:0]                    axi_arregion,  // not used, default value
    output var [7:0]                    axi_arlen,
    output var [2:0]                    axi_arsize,
    output var [1:0]                    axi_arburst,
    output var                          axi_arlock,    // not used, default value
    output var [3:0]                    axi_arcache,   // not used, fixed value
    output var [2:0]                    axi_arprot,
    output var [3:0]                    axi_arqos,     // not used, default value
    output var [AXI_ARUSER_WIDTH-1:0]   axi_aruser,    // not used, all zero
    output var                          axi_arvalid,
    input wire                          axi_arready,
    // Read Data Channel (R)
    input wire [AXI_ID_WIDTH-1:0]       axi_rid,       // ignored, cache does not use overlapping transactions
    input wire [AXI_DATA_WIDTH-1:0]     axi_rdata,
    input wire [1:0]                    axi_rresp,
    input wire                          axi_rlast,
    input wire [AXI_RUSER_WIDTH-1:0]    axi_ruser,     // ignored
    input wire                          axi_rvalid,
    output var                          axi_rready
);

    // handle reads

    typedef enum {
        R_IDLE,
        R_IFETCH,
        R_DFETCH
    } read_state_t;

    read_state_t read_state, read_state_q;

    assign axi_arregion = 0; // not used
    assign axi_arlock = 0; // not used
    assign axi_arcache = 4'b1111; // not used, TODO also support uncached accesses
    assign axi_arqos = 0; // not used
    assign axi_aruser = 0; // not used

    assign axi_arsize = $clog2(AXI_DATA_WIDTH / 8); // always use full bus width
    assign axi_arlen = (LINE_WIDTH / AXI_DATA_WIDTH) - 1; // always transfer complete lines
    assign axi_arburst = 2'b01; // always incr

    assign axi_rready = 1; // always ready

    logic axi_arready_q, axi_arvalid_q;
    logic [2:0] axi_arprot_q;
    logic [AXI_ID_WIDTH-1:0] axi_arid_q;
    logic [AXI_ADDRESS_WIDTH-1:0] axi_araddr_q;

    logic [LINE_WIDTH-1:0] read_data, read_data_q;
    logic read_fault, read_fault_q;
    logic read_valid;

    logic reset_q;

    always_ff @(posedge clock) begin
        axi_arready_q <= axi_arready;

        axi_arvalid_q <= axi_arvalid;
        axi_arprot_q <= axi_arprot;
        axi_arid_q <= axi_arid;
        axi_araddr_q <= axi_araddr;

        read_data_q <= read_data;
        read_fault_q <= read_fault;

        read_state_q <= read_state;

        reset_q <= reset;
    end

    assign imem_res_fault = read_fault;
    assign dmem_res_r_fault = read_fault;

    assign imem_res_valid = (read_state_q == R_IFETCH && read_valid);
    assign dmem_res_r_valid = (read_state_q == R_DFETCH && read_valid);

    assign imem_res_data = read_data;
    assign dmem_res_r_data = read_data;

    always_comb begin
        logic local_read_valid;

        axi_arvalid = axi_arvalid_q;
        axi_arprot = axi_arprot_q;
        axi_arid = axi_arid_q;
        axi_araddr = axi_araddr_q;

        read_data = read_data_q;
        read_fault = read_fault_q;

        read_state = read_state_q;

        local_read_valid = 0;

        if (axi_arready_q && axi_arvalid_q) begin
            axi_arvalid = 0;
            read_fault = 0;
        end

        case (read_state)
        R_IFETCH, R_DFETCH:
            if (axi_rvalid && axi_rready) begin
                read_data = {axi_rdata, read_data[LINE_WIDTH - 1:AXI_DATA_WIDTH]};
                if (axi_rresp[1]) begin
                    read_fault = 1;
                end

                if (axi_rlast) begin
                    read_state = R_IDLE;
                    local_read_valid = 1;
                end
            end
        default:
            if (!axi_arvalid && !reset_q && (imem_req_valid || dmem_req_r_valid)) begin
                axi_arvalid = 1;
                if (imem_req_valid) begin
                    axi_arid = AXI_IMEM_ID;
                    axi_arprot = 3'b111; // insn, non-secure, priviliged
                    axi_araddr = imem_req_addr;
                    read_state = R_IFETCH;
                end else begin
                    axi_arid = AXI_DMEM_ID;
                    axi_arprot = 3'b011; // data, non-secure, priviliged
                    axi_araddr = dmem_req_r_addr;
                    read_state = R_DFETCH;
                end
            end
        endcase

        if (reset) begin
            axi_arvalid = 0;
            read_state = R_IDLE;
        end

        read_valid = local_read_valid;
    end

    // handle writes

    typedef enum {
        W_IDLE,
        W_DSTORE
    } write_state_t;

    write_state_t write_state, write_state_q;

    assign axi_awregion = 0; // not used
    assign axi_awlock = 0; // not used
    assign axi_awcache = 4'b1111; // not used, TODO also support uncached accesses
    assign axi_awqos = 0; // not used
    assign axi_awuser = 0; // not used


    assign axi_awsize = $clog2(AXI_DATA_WIDTH / 8); // always use full bus width
    assign axi_awlen = (LINE_WIDTH / AXI_DATA_WIDTH) - 1; // always transfer complete lines
    assign axi_awburst = 2'b01; // always incr

    assign axi_wstrb = {AXI_STRB_WIDTH{1'b1}}; // always transfer complete lines
    assign axi_wuser = 0; // not used

    assign axi_bready = 1; // always ready

    logic axi_awready_q, axi_awvalid_q;
    logic [2:0] axi_awprot_q;
    logic [AXI_ID_WIDTH-1:0] axi_awid_q;
    logic [AXI_ADDRESS_WIDTH-1:0] axi_awaddr_q;

    logic [$clog2(LINE_WIDTH / AXI_DATA_WIDTH):0] wvalid_counter, wvalid_counter_q;
    logic axi_wready_q;

    logic [LINE_WIDTH-1:0] wdata_shiftreg, wdata_shiftreg_q;

    assign axi_wvalid = wvalid_counter != 0;
    assign axi_wlast = wvalid_counter == 1;

    assign axi_wdata = wdata_shiftreg[AXI_DATA_WIDTH-1:0];

    always_ff @(posedge clock) begin
        axi_awready_q <= axi_awready;

        axi_awvalid_q <= axi_awvalid;
        axi_awprot_q <= axi_awprot;
        axi_awid_q <= axi_awid;
        axi_awaddr_q <= axi_awaddr;

        axi_wready_q <= axi_wready;

        wvalid_counter_q <= wvalid_counter;
        wdata_shiftreg_q <= wdata_shiftreg;

        write_state_q <= write_state;
    end

    assign dmem_res_w_valid = write_state_q == W_DSTORE && axi_bready && axi_bvalid;

    // We ignore write responses / write faults for now as our cache will never
    // write something it hasn't successfully read before
    assign dmem_res_w_fault = 0;

    always_comb begin
        axi_awvalid = axi_awvalid_q;
        axi_awprot = axi_awprot_q;
        axi_awid = axi_awid_q;
        axi_awaddr = axi_awaddr_q;

        wvalid_counter = wvalid_counter_q;
        wdata_shiftreg = wdata_shiftreg_q;

        write_state = write_state_q;

        if (axi_awready_q && axi_awvalid_q) begin
            axi_awvalid = 0;
        end

        if (axi_wready_q && (wvalid_counter_q != 0)) begin
            wvalid_counter -= 1;
            wdata_shiftreg = {{AXI_DATA_WIDTH{1'b0}}, wdata_shiftreg[LINE_WIDTH-1:AXI_DATA_WIDTH]};
            if (wvalid_counter == 0) begin
                write_state = W_IDLE;
            end
        end

        if (write_state == W_IDLE && !axi_awvalid && wvalid_counter == 0 && dmem_req_w_valid) begin
            axi_awvalid = 1;
            wvalid_counter = LINE_WIDTH / AXI_DATA_WIDTH;
            axi_awid = AXI_DMEM_ID;
            axi_awprot = 3'b011; // data, non-secure, priviliged
            axi_awaddr = dmem_req_w_addr;
            wdata_shiftreg = dmem_req_w_data;
            write_state = W_DSTORE;
        end

        if (reset) begin
            axi_awvalid = 0;
            wvalid_counter = 0;
            write_state = W_IDLE;
        end
    end

endmodule
