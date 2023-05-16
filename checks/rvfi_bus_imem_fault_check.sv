// external bus: check faulting instruction memory reads
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
module rvfi_bus_imem_fault_check (
	input clock, reset, check,
	`RVFI_INPUTS
	`RVFI_BUS_INPUTS
);
	`rvformal_rand_const_reg [`RISCV_FORMAL_XLEN-1:0] imem_addr;

	reg [`RISCV_FORMAL_XLEN-1:0] pc;
	reg [`RISCV_FORMAL_ILEN-1:0] insn;

	reg [  `RISCV_FORMAL_XLEN   - 1:0] bus_addr;
	reg [`RISCV_FORMAL_BUSLEN/8 - 1:0] bus_rmask;
	reg [`RISCV_FORMAL_BUSLEN   - 1:0] bus_rdata;

	integer channel_idx, i, j;

	always @(posedge clock) begin
		if (reset) begin
		end else begin
			for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NBUS; channel_idx=channel_idx+1) begin
				if (rvfi_bus_valid[channel_idx] && rvfi_bus_insn[channel_idx]) begin
					bus_addr = rvfi_bus_addr[channel_idx*`RISCV_FORMAL_XLEN +: `RISCV_FORMAL_XLEN];
					bus_rmask = rvfi_bus_rmask[channel_idx*`RISCV_FORMAL_BUSLEN/8 +: `RISCV_FORMAL_BUSLEN/8];
					bus_rdata = rvfi_bus_rdata[channel_idx*`RISCV_FORMAL_BUSLEN +: `RISCV_FORMAL_BUSLEN];
					for (i = 0; i < `RISCV_FORMAL_BUSLEN/8; i=i+1)
					for (j = 0; j < 2; j=j+1) begin
						if (bus_rmask[i] && bus_addr + i == imem_addr + j) begin
							assume (rvfi_bus_fault[channel_idx]);
						end
					end
					cover (rvfi_bus_fault[channel_idx]);
				end
			end

			if (check) begin
				if (rvfi_valid[`RISCV_FORMAL_CHANNEL_IDX]) begin
					pc = rvfi_pc_rdata[`RISCV_FORMAL_CHANNEL_IDX*`RISCV_FORMAL_XLEN +: `RISCV_FORMAL_XLEN];
					insn = rvfi_insn[`RISCV_FORMAL_CHANNEL_IDX*`RISCV_FORMAL_ILEN +: `RISCV_FORMAL_ILEN];

					if (`rvformal_addr_valid(pc) && pc == imem_addr) begin
						cover (1);
						assert (rvfi_trap[`RISCV_FORMAL_CHANNEL_IDX]);
						assert (insn == 0);
`ifdef RISCV_FORMAL_MEM_FAULT
						assert (rvfi_mem_fault[`RISCV_FORMAL_CHANNEL_IDX]);
`endif
					end;

					if (`rvformal_addr_valid(pc+2) && pc+2 == imem_addr) begin
						cover (1);
						assert (rvfi_trap[`RISCV_FORMAL_CHANNEL_IDX]);
						assert (insn == 0);
`ifdef RISCV_FORMAL_MEM_FAULT
						assert (rvfi_mem_fault[`RISCV_FORMAL_CHANNEL_IDX]);
`endif
					end;
				end
			end
		end
	end

endmodule
