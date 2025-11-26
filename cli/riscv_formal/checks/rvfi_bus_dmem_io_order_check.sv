// external bus: check i/o access ordering
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

module rvfi_bus_dmem_io_order_check (
	input clock, reset, check,
	`RVFI_INPUTS
	`RVFI_BUS_INPUTS
);
	`rvformal_rand_const_reg [`RISCV_FORMAL_XLEN   - 1:0] check_addr_0;
	`rvformal_rand_const_reg [`RISCV_FORMAL_XLEN   - 1:0] check_addr_1;
	`rvformal_rand_const_reg check_write_0;
	`rvformal_rand_const_reg check_fault_0;
	`rvformal_rand_const_reg check_write_1;
	`rvformal_rand_const_reg check_fault_1;

	(* keep *) reg bus_0_prev, bus_0_current, bus_1_current, bus_seq_seen;

	(* keep *) reg [`RISCV_FORMAL_NBUS-1:0] bus_is_io;

	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] bus_addr;
	(* keep *) reg [`RISCV_FORMAL_BUSLEN/8 - 1:0] bus_rmask;
	(* keep *) reg [`RISCV_FORMAL_BUSLEN   - 1:0] bus_rdata;
	(* keep *) reg [`RISCV_FORMAL_BUSLEN/8 - 1:0] bus_wmask;
	(* keep *) reg [`RISCV_FORMAL_BUSLEN   - 1:0] bus_wdata;

	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] mem_addr;
	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] mem_rdata;
	(* keep *) reg [  `RISCV_FORMAL_XLEN/8 - 1:0] mem_rmask;
	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] mem_wdata;
	(* keep *) reg [  `RISCV_FORMAL_XLEN/8 - 1:0] mem_wmask;

	(* keep *) reg fault;

	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] prev_addr;
	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] prev_rdata;
	(* keep *) reg [  `RISCV_FORMAL_XLEN/8 - 1:0] prev_rmask;
	(* keep *) reg [  `RISCV_FORMAL_XLEN   - 1:0] prev_wdata;
	(* keep *) reg [  `RISCV_FORMAL_XLEN/8 - 1:0] prev_wmask;
	(* keep *) reg                                prev_fault;

	(* keep *) reg core_has_prev;

	(* keep *) reg core_0_match;
	(* keep *) reg core_1_match;

	reg [  `RISCV_FORMAL_XLEN   - 1:0] bus_byte_addr;

	integer channel_idx, i, j;

	always @(posedge clock) begin
		if (reset) begin
			bus_0_current = 0;
			bus_0_prev = 0;
			bus_1_current = 0;
			bus_seq_seen = 0;

			core_has_prev = 0;
		end else begin
			for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NBUS; channel_idx=channel_idx+1) begin
				if (rvfi_bus_valid[channel_idx] && rvfi_bus_data[channel_idx]) begin
					bus_addr = rvfi_bus_addr[channel_idx*`RISCV_FORMAL_XLEN +: `RISCV_FORMAL_XLEN];
					bus_rmask = rvfi_bus_rmask[channel_idx*`RISCV_FORMAL_BUSLEN/8 +: `RISCV_FORMAL_BUSLEN/8];
					bus_rdata = rvfi_bus_rdata[channel_idx*`RISCV_FORMAL_BUSLEN +: `RISCV_FORMAL_BUSLEN];
					bus_wmask = rvfi_bus_wmask[channel_idx*`RISCV_FORMAL_BUSLEN/8 +: `RISCV_FORMAL_BUSLEN/8];
					bus_wdata = rvfi_bus_wdata[channel_idx*`RISCV_FORMAL_BUSLEN +: `RISCV_FORMAL_BUSLEN];

					bus_is_io[channel_idx] = 0;
					for (i = 0; i < `RISCV_FORMAL_BUSLEN/8; i=i+1) begin
						bus_byte_addr = bus_addr + i;
						if (`rvformal_addr_io(bus_byte_addr) && (bus_rmask[i] || bus_wmask[i])) begin
							bus_is_io[channel_idx] = 1;
						end
					end

					if (bus_is_io[channel_idx]) begin
						bus_1_current = 0;
						bus_0_prev = bus_0_current;
						bus_0_current = 0;

						for (i = 0; i < `RISCV_FORMAL_BUSLEN/8; i=i+1) begin
							if ((bus_addr + i == check_addr_0) && (check_fault_0 == rvfi_bus_fault[channel_idx]) && (check_write_0 ? bus_wmask[i] : bus_rmask[i])) begin
								bus_0_current = 1;
							end
							if ((bus_addr + i == check_addr_1) && (check_fault_1 == rvfi_bus_fault[channel_idx]) && (check_write_1 ? bus_wmask[i] : bus_rmask[i])) begin
								bus_1_current = 1;
							end
						end

						if (bus_1_current && bus_0_prev) begin
							bus_seq_seen = 1;
							cover (1);
						end
					end

				end
			end
			for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NRET; channel_idx=channel_idx+1) begin
				mem_addr  = rvfi_mem_addr [channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
				mem_rdata = rvfi_mem_rdata[channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
				mem_rmask = rvfi_mem_rmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];
				mem_wdata = rvfi_mem_wdata[channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
				mem_wmask = rvfi_mem_wmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];

`ifdef RISCV_FORMAL_MEM_FAULT
				fault = rvfi_mem_fault[channel_idx];
				if (fault) begin
					mem_rmask = rvfi_mem_fault_rmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];
					mem_wmask = rvfi_mem_fault_wmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];
				end
`else
				fault = 0;
`endif
				core_0_match = 0;
				core_1_match = 0;

				for (i = 0; i < `RISCV_FORMAL_XLEN/8; i=i+1) begin
					if ((prev_addr + i == check_addr_0) && (check_fault_0 == prev_fault) && (check_write_0 ? prev_wmask[i] : prev_rmask[i])) begin
						core_0_match = core_has_prev;
					end
					if ((mem_addr + i == check_addr_1) && (check_fault_1 == fault) && (check_write_1 ? mem_wmask[i] : mem_rmask[i])) begin
						core_1_match = 1;
					end
				end

				if (
					check && rvfi_valid[channel_idx] &&
					channel_idx == `RISCV_FORMAL_CHANNEL_IDX &&
					`rvformal_addr_io(mem_addr) &&
					core_0_match && core_1_match
				) begin
					cover (1);
					assert (bus_seq_seen);

				end

				if (rvfi_valid[channel_idx] && `rvformal_addr_io(mem_addr) && (mem_rmask || mem_wmask)) begin
					// This check would need to be extended to handle potential instructions that
					// simultaneously read and write. This assertion makes sure this check doesn't
					// silently miss any issues should such instructions be added.
					assert (!(mem_rmask && mem_wmask));
					core_has_prev = 1;
					prev_addr = mem_addr;
					prev_rdata = mem_rdata;
					prev_rmask = mem_rmask;
					prev_wdata = mem_wdata;
					prev_wmask = mem_wmask;
					prev_fault = fault;
				end
			end
		end
	end

endmodule
