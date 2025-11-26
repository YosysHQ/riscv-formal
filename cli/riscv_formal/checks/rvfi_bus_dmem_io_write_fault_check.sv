// external bus: check i/o write faults
//
// This checks that a retired faulting store is contained in a single read
// transaction on the external bus. It doesn't check any relationships bitween
// multiple instructions or bus transactions. See the inline comment for
// details on stores that are not as wide as the bus.
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

module rvfi_bus_dmem_io_write_fault_check (
	input clock, reset, check,
	`RVFI_INPUTS
	`RVFI_BUS_INPUTS
);
	`rvformal_rand_const_reg [`RISCV_FORMAL_XLEN   - 1:0] check_addr;
	`rvformal_rand_const_reg [`RISCV_FORMAL_XLEN   - 1:0] check_wdata;
	`rvformal_rand_const_reg [`RISCV_FORMAL_XLEN/8 - 1:0] check_wmask;

	reg bus_write_seen, bus_write_matches;
	reg core_write_matches;

	reg [`RISCV_FORMAL_XLEN/8 - 1:0] check_match_mask;
	reg [`RISCV_FORMAL_BUSLEN/8 - 1:0] bus_match_mask;

	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] bus_addr;
	(* keep *) reg [`RISCV_FORMAL_BUSLEN/8 - 1:0] bus_wmask;
	(* keep *) reg [`RISCV_FORMAL_BUSLEN   - 1:0] bus_wdata;

	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] mem_addr;
	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] mem_wdata;
	(* keep *) reg [  `RISCV_FORMAL_XLEN/8 - 1:0] mem_wmask;

	integer channel_idx, i, j;

	always @(posedge clock) begin
		if (reset) begin
			bus_write_seen <= 0;
		end else begin
			for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NBUS; channel_idx=channel_idx+1) begin
				if (rvfi_bus_valid[channel_idx] && rvfi_bus_data[channel_idx]) begin
					bus_addr = rvfi_bus_addr[channel_idx*`RISCV_FORMAL_XLEN +: `RISCV_FORMAL_XLEN];
					bus_wmask = rvfi_bus_wmask[channel_idx*`RISCV_FORMAL_BUSLEN/8 +: `RISCV_FORMAL_BUSLEN/8];
					bus_wdata = rvfi_bus_wdata[channel_idx*`RISCV_FORMAL_BUSLEN +: `RISCV_FORMAL_BUSLEN];

					// This allows the write to appear anywhere in the bus data as long as it fits
					// into a single transaction. Unlike for reads, we don't allow writing
					// additional adjacent bytes.

					check_match_mask = 0;
					bus_match_mask = 0;
					bus_write_matches = 1;

					for (i = 0; i < `RISCV_FORMAL_BUSLEN/8; i=i+1) begin
						for (j = 0; j < `RISCV_FORMAL_XLEN/8; j=j+1) begin
							if (bus_addr + i == check_addr + j && check_wmask[i]) begin
								if (bus_wmask[i] && bus_wdata[i*8 +: 8] == check_wdata[j*8 +: 8]) begin
									check_match_mask[j] = 1;
									bus_match_mask[i] = 1;
								end else begin
									bus_write_matches = 0;
								end
							end
						end
					end

					if (bus_write_matches && bus_match_mask == bus_wmask && check_match_mask == check_wmask && rvfi_bus_fault[channel_idx]) begin
						bus_write_seen = 1;
					end
				end
			end
			for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NRET; channel_idx=channel_idx+1) begin
				mem_addr  = rvfi_mem_addr [channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
				mem_wdata = rvfi_mem_wdata[channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
				mem_wmask = rvfi_mem_fault_wmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];
				core_write_matches = check_wmask && mem_addr == check_addr && mem_wmask == check_wmask && rvfi_mem_fault[channel_idx];
				for (i = 0; i < `RISCV_FORMAL_XLEN/8; i=i+1) begin
					if (mem_wmask[i] && mem_wdata[i*8 +: 8] != check_wdata[i*8 +: 8]) begin
						core_write_matches = 0;
					end
				end

				if (check && rvfi_valid[channel_idx] && core_write_matches && `rvformal_addr_io(check_addr)) begin
					cover (1);
					assert (bus_write_seen);
				end
			end
		end
	end

endmodule
