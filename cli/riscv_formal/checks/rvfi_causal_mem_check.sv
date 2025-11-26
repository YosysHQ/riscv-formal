// check that no memory accesses are retired in a non-causal order
//
// This checks that no read of a memory location is retired before the write of
// the to-be-read value.
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

module rvfi_causal_mem_check (
	input clock, reset, check,
	`RVFI_INPUTS
);
	`rvformal_rand_const_reg [63:0] insn_order;
	`rvformal_rand_const_reg [`RISCV_FORMAL_XLEN-1:0] check_addr;


	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] mem_addr;
	(* keep *) reg [  `RISCV_FORMAL_XLEN/8 - 1:0] mem_rmask;
	(* keep *) reg [  `RISCV_FORMAL_XLEN/8 - 1:0] mem_wmask;

	reg found_non_causal = 0;
	reg reads_check_addr;
	reg writes_check_addr;

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

				reads_check_addr = 0;
				writes_check_addr = 0;

				for (i = 0; i < `RISCV_FORMAL_XLEN/8; i = i+1) begin
					if (mem_addr + i == check_addr) begin
						reads_check_addr |= mem_rmask[i];
						writes_check_addr |= mem_wmask[i];
					end
				end

				if (check && channel_idx == `RISCV_FORMAL_CHANNEL_IDX) begin
					assume (rvfi_valid[`RISCV_FORMAL_CHANNEL_IDX]);
					assume (writes_check_addr);
					assume (insn_order == rvfi_order[64*`RISCV_FORMAL_CHANNEL_IDX +: 64]);
					cover (1);
					assert (!found_non_causal);
				end

				if (rvfi_valid[channel_idx] && rvfi_order[64*channel_idx +: 64] > insn_order && reads_check_addr) begin
					found_non_causal = 1;
				end
			end
		end
	end
endmodule
