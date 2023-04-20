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

// Read/write data cache.
//
// This implements the instruction cache. It directly uses NERV's native
// interface on the core side but uses a simple internal interface that
// transfers whole cache lines on the bus side. Translating this into AXI is
// done using `nerv_axi_cache_axi` which together with this and the data cache
// is wrapped by `nerv_axi_cache`.
//
// See `nerv_axi_cache` for parameter descriptions.
module nerv_axi_cache_dcache #(
    parameter ADDRESS_WIDTH = 32,
    parameter DATA_SIZE = 2,
    parameter LINE_SIZE = 5,
    parameter INDEX_SIZE = 4,

    localparam DATA_WIDTH = 8 << DATA_SIZE,
    localparam LINE_WIDTH = 8 << LINE_SIZE,
    localparam LINE_COUNT = 1 << INDEX_SIZE
) (
    input wire                       clock,
    input wire                       reset,

    input wire                       stalled,
    output var                       stall,

    input wire                       dmem_valid,
    input wire [ADDRESS_WIDTH-1:0]   dmem_addr,
    input wire [DATA_WIDTH/8-1:0]    dmem_wstrb,
    input wire [DATA_WIDTH-1:0]      dmem_wdata,
    output var [DATA_WIDTH-1:0]      dmem_rdata,
    output var                       dmem_fault,

    output var [ADDRESS_WIDTH-1:0]   req_r_addr,
    output var                       req_r_valid,

    input wire [LINE_WIDTH-1:0]      res_r_data,
    input wire                       res_r_fault,
    input wire                       res_r_valid,

    output var [ADDRESS_WIDTH-1:0]   req_w_addr,
    output var [LINE_WIDTH-1:0]      req_w_data,
    output var                       req_w_valid,

    input wire                       res_w_fault,
    input wire                       res_w_valid
);

    typedef logic [ADDRESS_WIDTH-1:0] addr_t;
    typedef logic [ADDRESS_WIDTH-LINE_SIZE-1:0] line_addr_t;
    typedef logic [LINE_WIDTH-1:0] line_t;
    typedef logic [INDEX_SIZE-1:0] index_t;
    typedef logic [ADDRESS_WIDTH-LINE_SIZE-INDEX_SIZE-1:0] tag_t;

    // cache memory

    line_addr_t cache_line_addr_rd;
    (*keep*) line_addr_t cache_line_addr_wr;

    index_t cache_index_rd, cache_index_rd_q;
    tag_t cache_tag_rd, cache_tag_rd_q;

    index_t cache_index_wr;
    tag_t cache_tag_wr;

    assign {cache_tag_rd,   cache_index_rd  } = cache_line_addr_rd;
    assign {cache_tag_wr,   cache_index_wr  } = cache_line_addr_wr;

    line_t cache_data_mem [0:LINE_COUNT-1];
    tag_t cache_tag_mem [0:LINE_COUNT-1];
    logic [LINE_COUNT-1:0] cache_valid_mem;
    logic [LINE_COUNT-1:0] cache_dirty_mem;

    line_t cache_data_out, cache_data_out_q;
    tag_t cache_tag_out;
    logic cache_valid_out;
    logic cache_dirty_out;

    assign cache_data_out = cache_data_mem[cache_index_rd];
    assign cache_tag_out = cache_tag_mem[cache_index_rd];
    assign cache_valid_out = cache_valid_mem[cache_index_rd];
    assign cache_dirty_out = cache_dirty_mem[cache_index_rd];

    line_t cache_data_in;
    logic cache_valid_in;
    logic cache_dirty_in;

    always @(posedge clock) begin
        cache_data_out_q <= cache_data_out;

        cache_data_mem[cache_index_wr] <= cache_data_in;
        cache_tag_mem[cache_index_wr] <= cache_tag_wr;
        cache_valid_mem[cache_index_wr] <= cache_valid_in;
        cache_dirty_mem[cache_index_wr] <= cache_dirty_in;

        if (reset) begin
            cache_valid_mem <= 0;
            cache_dirty_mem <= 0;
        end
    end

    // cache last dmem interface values while the core is stalled

    addr_t stable_addr, stable_addr_q;
    logic [DATA_WIDTH/8-1:0] stable_wstrb;
    logic [DATA_WIDTH/8-1:0] stable_wstrb_q;
    logic [DATA_WIDTH-1:0] stable_wdata;
    logic [DATA_WIDTH-1:0] stable_wdata_q;
    logic stable_valid, stable_valid_q;
    logic stalled_q;

    always_ff @(posedge clock) begin
        stable_addr_q <= stable_addr;
        stable_wstrb_q <= stable_wstrb;
        stable_wdata_q <= stable_wdata;
        stable_valid_q <= stable_valid;
        stalled_q <= stalled;
    end

    always_comb begin
        stable_addr = stable_addr_q;
        stable_wstrb = stable_wstrb_q;
        stable_wdata = stable_wdata_q;
        stable_valid = stable_valid_q;
        if (!stalled && dmem_valid) begin
            stable_addr = dmem_addr;
            stable_wdata = dmem_wdata;
            stable_wstrb = dmem_wstrb;
        end
        if (!stalled) begin
            stable_valid = dmem_valid;
        end
    end

    // fast path for read and write hits

    wire line_addr_t line_addr = stable_addr[ADDRESS_WIDTH-1:LINE_SIZE];
    wire line_addr_t line_addr_q = stable_addr_q[ADDRESS_WIDTH-1:LINE_SIZE];

    assign cache_line_addr_rd = line_addr;
    assign cache_line_addr_wr = line_addr;

    wire logic [LINE_SIZE-DATA_SIZE-1:0] line_subaddr = stable_addr[LINE_SIZE-1:DATA_SIZE];
    wire logic [LINE_SIZE-DATA_SIZE-1:0] line_subaddr_q = stable_addr_q[LINE_SIZE-1:DATA_SIZE];

    line_t dmem_rdata_line, dmem_rdata_line_q;
    logic dmem_next_fault, dmem_next_fault_q;

    always_ff @(posedge clock) begin
        dmem_rdata_line_q <= dmem_rdata_line;
        dmem_next_fault_q <= dmem_next_fault;
    end

    assign dmem_rdata_line = cache_data_in;

    assign dmem_rdata = dmem_rdata_line_q[line_subaddr_q * DATA_WIDTH +: DATA_WIDTH];

    assign dmem_fault = dmem_next_fault_q;

    wire logic cache_hit = (cache_tag_out == cache_tag_rd && cache_valid_out);
    wire logic cache_miss = (stable_valid && !cache_hit);

    logic cache_hit_q, cache_miss_q;

    wire logic cache_writeback = (cache_miss  && cache_dirty_out && cache_valid_out);

    always_ff @(posedge clock) begin
        cache_hit_q <= cache_hit && !reset;
        cache_miss_q <= cache_miss && !reset;
    end

    always_comb begin
        dmem_next_fault = dmem_next_fault_q && stalled;

        cache_data_in = cache_data_out;
        cache_dirty_in = cache_dirty_out;
        cache_valid_in = cache_hit;

        // inject fetched data
        if (res_r_valid) begin
            cache_data_in = res_r_data;
            cache_dirty_in = 0;
            cache_valid_in = !res_r_fault;
            dmem_next_fault = res_r_fault;
        end

        for (int i = 0; i < DATA_WIDTH / 8; i++) begin
            if (stable_valid && stable_wstrb[i]) begin
                cache_dirty_in = 1;
                cache_data_in[line_subaddr * DATA_WIDTH + 8 * i +: 8] =
                    stable_wdata[8 * i +: 8];
            end
        end

        if (reset) begin
            dmem_next_fault = 0;
        end
    end

    // fetch misses and perform writebacks

    assign req_r_addr = {cache_line_addr_rd, {LINE_SIZE{1'b0}}};

    addr_t req_w_addr_q;
    line_t req_w_data_q;
    logic req_w_valid_q;
    logic req_r_valid_q;
    logic res_w_valid_q;
    logic res_r_valid_q;

    always_ff @(posedge clock) begin
        req_w_addr_q <= req_w_addr;
        req_w_data_q <= req_w_data;
        req_w_valid_q <= req_w_valid;
        req_r_valid_q <= req_r_valid;
        res_w_valid_q <= res_w_valid;
        res_r_valid_q <= res_r_valid;
    end

    assign stall = (cache_miss_q && !dmem_next_fault_q) || req_w_valid_q;

    always_comb begin
        req_w_valid = req_w_valid_q;
        req_w_data = req_w_data_q;
        req_w_addr = req_w_addr_q;

        req_r_valid = req_r_valid_q;

        if (res_r_valid_q) begin
            req_r_valid = 0;
        end

        if (cache_miss && !stalled) begin
            req_r_valid = 1;
        end

        if (res_w_valid_q) begin
            req_w_valid = 0;
        end

        if (cache_writeback && !stalled) begin
            req_w_valid = 1;
            req_w_addr = {cache_tag_out, cache_index_rd, {LINE_SIZE{1'b0}}};
            req_w_data = cache_data_out;
        end

        if (reset) begin
            req_w_valid = 0;
            req_r_valid = 0;
        end
    end
endmodule
