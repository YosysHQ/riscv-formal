// Copyright (C) 2023  Krystine Dawn Sherwin <krystinedawn@yosyshq.com>
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

module rvfi_csrc_zero_check (
	input clock, reset, check,
	`RVFI_INPUTS
);
	// Setup for csrs
	`RVFI_CHANNEL(rvfi, `RISCV_FORMAL_CHANNEL_IDX)

	localparam [11:0] csr_none = 12'hFFF;
	`RVFI_INDICES

	`define quoted(txt) txt
	`define csrget(_name, _type) rvfi.csr_``_name```quoted(_``_type)
	`define csr_mindex(_name) csr_mindex_``_name
	`define csr_sindex(_name) csr_sindex_``_name
	`define csr_uindex(_name) csr_uindex_``_name
	`define csr_mindexh(_name) csr_mindex_``_name```quoted(h)
	`define csr_sindexh(_name) csr_sindex_``_name```quoted(h)
	`define csr_uindexh(_name) csr_uindex_``_name```quoted(h)

	wire csr_insn_valid = rvfi.valid && (rvfi.insn[6:0] == 7'b 1110011) && (rvfi.insn[13:12] != 0) && ((rvfi.insn >> 16 >> 16) == 0);
	wire [11:0] csr_insn_addr = rvfi.insn[31:20];

	wire [`RISCV_FORMAL_XLEN-1:0] csr_insn_rmask = `csrget(`RISCV_FORMAL_CSRC_NAME, rmask);
	wire [`RISCV_FORMAL_XLEN-1:0] csr_insn_wmask = `csrget(`RISCV_FORMAL_CSRC_NAME, wmask);
	wire [`RISCV_FORMAL_XLEN-1:0] csr_insn_rdata = `csrget(`RISCV_FORMAL_CSRC_NAME, rdata);
	wire [`RISCV_FORMAL_XLEN-1:0] csr_insn_wdata = `csrget(`RISCV_FORMAL_CSRC_NAME, wdata);

	wire csr_write = !rvfi.insn[13] || rvfi.insn[19:15];
	wire csr_read = rvfi.insn[11:7] != 0;
	wire csr_write_valid = csr_write && csr_insn_valid;
	wire csr_read_valid = csr_read && csr_insn_valid;
	wire [1:0] csr_mode = rvfi.insn[13:12];
	wire [31:0] csr_rsval = rvfi.insn[14] ? rvfi.insn[19:15] : rvfi.rs1_rdata;

	// Setup for reg testing
	`rvformal_rand_const_reg [63:0] insn_order;
	reg [`RISCV_FORMAL_XLEN-1:0] wdata_shadow = 0;
	reg csr_written = 0;

	always @(posedge clock) begin
		if (reset) begin
			wdata_shadow = 0;
			csr_written = 0;
		end else begin
			if (check) begin
				if (csr_written && csr_read_valid && csr_insn_addr == `csr_mindex(`RISCV_FORMAL_CSRC_NAME)) begin
					assert(csr_insn_rdata == 0);
					assume(wdata_shadow != 0);
				end
			end else begin
				if (csr_write_valid && csr_insn_addr == `csr_mindex(`RISCV_FORMAL_CSRC_NAME)) begin
					// simplify things by only testing reg write, and not set/clear
					assume(csr_mode == 0 || csr_mode == 1);
					wdata_shadow = csr_insn_wdata;
					csr_written = 1;
				end
			end
		end
	end
endmodule
