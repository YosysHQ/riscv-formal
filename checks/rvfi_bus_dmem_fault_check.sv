// external bus: check data reads
//
// Note: This only checks the data on the core side, so it is valid even with
// caches between the checked bus and core. It also checks that the first bus
// read of the checked data makes it to the core, but does not check that any
// writes make it to the bus nor that any other bus-side data makes it to the
// core.
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
module rvfi_bus_dmem_fault_check (
	input clock, reset, check,
	`RVFI_INPUTS
	`RVFI_BUS_INPUTS
);
	`rvformal_rand_const_reg [`RISCV_FORMAL_XLEN-1:0] dmem_addr;

	reg [  `RISCV_FORMAL_XLEN   - 1:0] bus_addr;
	reg [`RISCV_FORMAL_BUSLEN/8 - 1:0] bus_rmask;
	reg [`RISCV_FORMAL_BUSLEN   - 1:0] bus_rdata;
	reg [`RISCV_FORMAL_BUSLEN/8 - 1:0] bus_wmask;
	reg [`RISCV_FORMAL_BUSLEN   - 1:0] bus_wdata;

`ifdef RISCV_FORMAL_CSR_MCAUSE
	reg [`RISCV_FORMAL_XLEN-1:0] csr_mcause_wmask;
	reg [`RISCV_FORMAL_XLEN-1:0] csr_mcause_wdata;
`endif

	reg activated = 0;

	integer channel_idx, i, j;

	always @(posedge clock) begin
		if (!reset) begin
			for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NBUS; channel_idx=channel_idx+1) begin
				if (rvfi_bus_valid[channel_idx] && rvfi_bus_data[channel_idx]) begin
					bus_addr = rvfi_bus_addr[channel_idx*`RISCV_FORMAL_XLEN +: `RISCV_FORMAL_XLEN];
					bus_rmask = rvfi_bus_rmask[channel_idx*`RISCV_FORMAL_BUSLEN/8 +: `RISCV_FORMAL_BUSLEN/8];
					bus_rdata = rvfi_bus_rdata[channel_idx*`RISCV_FORMAL_BUSLEN +: `RISCV_FORMAL_BUSLEN];
					bus_wmask = rvfi_bus_wmask[channel_idx*`RISCV_FORMAL_BUSLEN/8 +: `RISCV_FORMAL_BUSLEN/8];
					bus_wdata = rvfi_bus_wdata[channel_idx*`RISCV_FORMAL_BUSLEN +: `RISCV_FORMAL_BUSLEN];

					for (i = 0; i < `RISCV_FORMAL_BUSLEN/8; i=i+1) begin
						for (j = 0; j < `RISCV_FORMAL_XLEN/8; j=j+1) begin
							if (bus_addr + i == dmem_addr + j) begin
								if (bus_rmask[i]) begin
									assume (rvfi_bus_fault[channel_idx]);
								end
								if (bus_wmask[i]) begin
									assume (rvfi_bus_fault[channel_idx]);
								end
							end
						end
					end
				end
			end
			for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NRET; channel_idx=channel_idx+1) begin
				if (rvfi_valid[channel_idx] && rvfi_mem_addr[channel_idx*`RISCV_FORMAL_XLEN +: `RISCV_FORMAL_XLEN] == dmem_addr && `rvformal_addr_valid(dmem_addr)) begin
					for (i = 0; i < `RISCV_FORMAL_XLEN/8; i = i+1) begin
						if (
`ifdef RISCV_FORMAL_CHANNEL_IDX
							i == `RISCV_FORMAL_CHANNEL_IDX &&
`endif
							check
						) begin
`ifdef RISCV_FORMAL_CSR_MCAUSE
							csr_mcause_wmask = rvfi_csr_mcause_wmask[channel_idx*`RISCV_FORMAL_ILEN +: `RISCV_FORMAL_ILEN];
							csr_mcause_wdata = rvfi_csr_mcause_wdata[channel_idx*`RISCV_FORMAL_ILEN +: `RISCV_FORMAL_ILEN];
`endif
							if (rvfi_mem_wmask[channel_idx*`RISCV_FORMAL_XLEN/8 + i]) begin
								cover (1);
								assert (rvfi_trap[channel_idx]);
`ifdef RISCV_FORMAL_MEM_FAULT
								assert (rvfi_mem_fault[channel_idx]);
`endif
`ifdef RISCV_FORMAL_CSR_MCAUSE
								assert (&csr_mcause_wmask);
								assert (csr_mcause_wdata == 7);
`endif
							end else if (rvfi_mem_rmask[channel_idx*`RISCV_FORMAL_XLEN/8 + i]) begin
								cover (1);
								assert (rvfi_trap[channel_idx]);
`ifdef RISCV_FORMAL_MEM_FAULT
								assert (rvfi_mem_fault[channel_idx]);
`endif
`ifdef RISCV_FORMAL_CSR_MCAUSE
								assert (&csr_mcause_wmask);
								assert (csr_mcause_wdata == 5);
`endif
							end;
						end
					end
				end
			end
		end
	end

endmodule
