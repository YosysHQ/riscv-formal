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

// Read only instruction cache.
//
// This implements the instruction cache. It directly uses NERV's native
// interface on the core side but uses a simple internal interface that
// transfers whole cache lines on the bus side. Translating this into AXI is
// done using `nerv_axi_cache_axi` which together with this and the data cache
// is wrapped by `nerv_axi_cache`.
//
// See `nerv_axi_cache` for parameter descriptions.
module nerv_axi_cache_icache #(
    parameter ADDRESS_WIDTH = 32,
    parameter INSN_SIZE = 2,
    parameter LINE_SIZE = 3,
    parameter INDEX_SIZE = 2,

    localparam INSN_WIDTH = 8 << INSN_SIZE,
    localparam LINE_WIDTH = 8 << LINE_SIZE,
    localparam LINE_COUNT = 1 << INDEX_SIZE
) (
    input wire                       clock,
    input wire                       reset,

    input wire                       stalled,
    output var                       stall,

    input wire [ADDRESS_WIDTH-1:0]   imem_addr,
    output var [INSN_WIDTH-1:0]      imem_data,
    output var                       imem_fault,

    output var [ADDRESS_WIDTH-1:0]   req_addr,
    output var                       req_valid,

    input wire [LINE_WIDTH-1:0]      res_data,
    input wire                       res_fault,
    input wire                       res_valid
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

    // cache last imem interface values while the core is stalled

    addr_t stable_addr, stable_addr_q;
    logic stable_valid, stable_valid_q;
    logic stalled_q;

    always_ff @(posedge clock) begin
        stable_addr_q <= stable_addr;
        stable_valid_q <= stable_valid;
        stalled_q <= stalled;
    end

    always_comb begin
        stable_addr = stable_addr_q;
        stable_valid = stable_valid_q;
        if (!stalled) begin
            stable_addr = imem_addr;
            stable_valid = 1;
        end
    end

    // fast path for read and write hits

    wire line_addr_t line_addr = stable_addr[ADDRESS_WIDTH-1:LINE_SIZE];
    wire line_addr_t line_addr_q = stable_addr_q[ADDRESS_WIDTH-1:LINE_SIZE];

    assign cache_line_addr_rd = line_addr;
    assign cache_line_addr_wr = line_addr;

    wire logic [LINE_SIZE-INSN_SIZE-1:0] line_subaddr = stable_addr[LINE_SIZE-1:INSN_SIZE];
    wire logic [LINE_SIZE-INSN_SIZE-1:0] line_subaddr_q = stable_addr_q[LINE_SIZE-1:INSN_SIZE];

    line_t imem_data_line, imem_data_line_q;
    logic imem_next_fault, imem_next_fault_q;

    always_ff @(posedge clock) begin
        imem_data_line_q <= imem_data_line;
        imem_next_fault_q <= imem_next_fault;
    end

    assign imem_data_line = cache_data_in;

    assign imem_data = imem_data_line_q[line_subaddr_q * INSN_WIDTH +: INSN_WIDTH];

    assign imem_fault = imem_next_fault_q;

    wire logic cache_hit = (cache_tag_out == cache_tag_rd && cache_valid_out);
    wire logic cache_miss = (stable_valid && !cache_hit);

    logic cache_hit_q, cache_miss_q;

    wire logic cache_writeback = (cache_miss  && cache_dirty_out && cache_valid_out);

    always_ff @(posedge clock) begin
        cache_hit_q <= cache_hit && !reset;
        cache_miss_q <= cache_miss && !reset;
    end

    always_comb begin
        imem_next_fault = imem_next_fault_q && stalled;

        cache_data_in = cache_data_out;
        cache_dirty_in = cache_dirty_out;
        cache_valid_in = cache_hit;

        // inject fetched data
        if (res_valid) begin
            cache_data_in = res_data;
            cache_dirty_in = 0;
            cache_valid_in = !res_fault;
            imem_next_fault = res_fault;
        end

        if (reset) begin
            imem_next_fault = 0;
        end
    end

    assign stall = cache_miss_q && !imem_next_fault_q;

    // fetch misses

    assign req_addr = {cache_line_addr_rd, {LINE_SIZE{1'b0}}};

    logic req_valid_q, res_valid_q;

    always_ff @(posedge clock) begin
        req_valid_q <= req_valid;
        res_valid_q <= res_valid;
    end

    always_comb begin
        req_valid = req_valid_q;

        if (res_valid_q) begin
            req_valid = 0;
        end

        if (cache_miss && !stalled) begin
            req_valid = 1;
        end

        if (reset) begin
            req_valid = 0;
        end
    end

endmodule
