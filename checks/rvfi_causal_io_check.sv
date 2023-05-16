// check that no i/o memory accesses are retired in a non-causal order
//
// This checks that no i/o memory accesses are retired out of order. It uses
// the RISCV_FORMAL_IOADDR(addr) macro to determine whether a memory location
// is considered to be an i/o address.
//
// Copyright (C) 2017  Claire Xenia Wolf <claire@yosyshq.com>
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

module rvfi_causal_io_check (
	input clock, reset, check,
	`RVFI_INPUTS
);
	`rvformal_rand_const_reg [63:0] insn_order;

	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] mem_addr;
	(* keep *) reg [  `RISCV_FORMAL_XLEN/8 - 1:0] mem_rmask;
	(* keep *) reg [  `RISCV_FORMAL_XLEN/8 - 1:0] mem_wmask;

	reg found_non_causal = 0;
	reg performs_io = 0;

	reg [  `RISCV_FORMAL_XLEN   - 1:0] byte_addr;

	integer channel_idx;
	integer i;

	always @(posedge clock) begin
		if (reset) begin
			found_non_causal = 0;
		end else begin
			for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NRET; channel_idx=channel_idx+1) begin
				mem_addr = rvfi_mem_addr[channel_idx*`RISCV_FORMAL_XLEN +: `RISCV_FORMAL_XLEN];
				mem_rmask = rvfi_mem_rmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];
				mem_wmask = rvfi_mem_wmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];

`ifdef RISCV_FORMAL_MEM_FAULT
				if (rvfi_mem_fault[channel_idx]) begin
					mem_rmask = rvfi_mem_fault_rmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];
					mem_wmask = rvfi_mem_fault_wmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];
				end
`endif

				performs_io = 0;

				for (i = 0; i < `RISCV_FORMAL_XLEN/8; i = i+1) begin
					byte_addr = mem_addr + i;
					if (`rvformal_addr_io(byte_addr)) begin
						performs_io |= mem_rmask[i] | mem_wmask[i];
					end
				end

				if (check && channel_idx == `RISCV_FORMAL_CHANNEL_IDX) begin
					assume (rvfi_valid[`RISCV_FORMAL_CHANNEL_IDX]);
					assume (performs_io);
					assume (insn_order == rvfi_order[64*`RISCV_FORMAL_CHANNEL_IDX +: 64]);
					cover (1);
					assert (!found_non_causal);
				end

				if (rvfi_valid[channel_idx] && rvfi_order[64*channel_idx +: 64] > insn_order && performs_io) begin
					found_non_causal = 1;
				end
			end
		end
	end
endmodule
