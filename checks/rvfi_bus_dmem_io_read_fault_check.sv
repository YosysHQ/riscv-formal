// external bus: check i/o read faults
//
// This checks that a retired faulting load is contained in a single read
// transaction on the external bus. It doesn't check any relationships bitween
// multiple instructions or bus transactions. See the inline comment for
// details on loads that are not as wide as the bus.
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

module rvfi_bus_dmem_io_read_fault_check (
	input clock, reset, check,
	`RVFI_INPUTS
	`RVFI_BUS_INPUTS
);
	`rvformal_rand_const_reg [`RISCV_FORMAL_XLEN   - 1:0] check_addr;
	`rvformal_rand_const_reg [`RISCV_FORMAL_XLEN/8 - 1:0] check_rmask;

	reg bus_read_seen, bus_read_matches;
	reg core_read_matches;

	reg [`RISCV_FORMAL_XLEN/8 - 1:0] check_match_mask;

	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] bus_addr;
	(* keep *) reg [`RISCV_FORMAL_BUSLEN/8 - 1:0] bus_rmask;
	(* keep *) reg [`RISCV_FORMAL_BUSLEN   - 1:0] bus_rdata;

	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] mem_addr;
	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] mem_rdata;
	(* keep *) reg [  `RISCV_FORMAL_XLEN/8 - 1:0] mem_rmask;

	integer channel_idx, i, j;

	always @(posedge clock) begin
		if (reset) begin
			bus_read_seen <= 0;
		end else begin
			for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NBUS; channel_idx=channel_idx+1) begin
				if (rvfi_bus_valid[channel_idx] && rvfi_bus_data[channel_idx]) begin
					bus_addr = rvfi_bus_addr[channel_idx*`RISCV_FORMAL_XLEN +: `RISCV_FORMAL_XLEN];
					bus_rmask = rvfi_bus_rmask[channel_idx*`RISCV_FORMAL_BUSLEN/8 +: `RISCV_FORMAL_BUSLEN/8];
					bus_rdata = rvfi_bus_rdata[channel_idx*`RISCV_FORMAL_BUSLEN +: `RISCV_FORMAL_BUSLEN];

					// This allows the read to appear anywhere in the bus data as long as it fits
					// into a single transaction. It also allows reading adjacent bytes in the same
					// transaction. Different busses handle narrow reads differently, so as a
					// generic check we don't prescribe any particular behavior.

					check_match_mask = 0;
					bus_read_matches = 1;

					for (i = 0; i < `RISCV_FORMAL_BUSLEN/8; i=i+1) begin
						for (j = 0; j < `RISCV_FORMAL_XLEN/8; j=j+1) begin
							if (bus_addr + i == check_addr + j && check_rmask[i]) begin
								if (bus_rmask[i]) begin
									check_match_mask[j] = 1;
								end else begin
									bus_read_matches = 0;
								end
							end
						end
					end

					if (bus_read_matches && check_match_mask == check_rmask && rvfi_bus_fault[channel_idx]) begin
						bus_read_seen = 1;
					end
				end
			end
			for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NRET; channel_idx=channel_idx+1) begin
				mem_addr  = rvfi_mem_addr [channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
				mem_rdata = rvfi_mem_rdata[channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
				mem_rmask = rvfi_mem_fault_rmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];
				core_read_matches = check_rmask && mem_addr == check_addr && mem_rmask == check_rmask && rvfi_mem_fault[channel_idx];

				if (check && rvfi_valid[channel_idx] && core_read_matches && `rvformal_addr_io(check_addr)) begin
					cover (1);
					assert (bus_read_seen);
				end
			end
		end
	end

endmodule
