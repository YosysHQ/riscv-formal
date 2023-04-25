// check handling of memory faults
//
// This checks that a dynamically occuring memory fault causes a trap and that
// the mcause csr correctly reports the cause of the trap.
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

module rvfi_fault_check (
	input clock, reset, check,
	`RVFI_INPUTS
);
`ifdef RISCV_FORMAL_CHANNEL_IDX
	localparam integer channel_idx = `RISCV_FORMAL_CHANNEL_IDX;
`else
	genvar channel_idx;
	generate for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NRET; channel_idx=channel_idx+1) begin:channel
`endif
		(* keep *) wire valid = !reset && rvfi_valid[channel_idx];
		(* keep *) wire [`RISCV_FORMAL_ILEN   - 1 : 0] insn      = rvfi_insn     [channel_idx*`RISCV_FORMAL_ILEN   +: `RISCV_FORMAL_ILEN];
		(* keep *) wire                                trap      = rvfi_trap     [channel_idx];
		(* keep *) wire                                mem_fault = rvfi_mem_fault[channel_idx];
		(* keep *) wire                                halt      = rvfi_halt     [channel_idx];
		(* keep *) wire                                intr      = rvfi_intr     [channel_idx];
		(* keep *) wire [                       4 : 0] rs1_addr  = rvfi_rs1_addr [channel_idx*5  +:  5];
		(* keep *) wire [                       4 : 0] rs2_addr  = rvfi_rs2_addr [channel_idx*5  +:  5];
		(* keep *) wire [`RISCV_FORMAL_XLEN   - 1 : 0] rs1_rdata = rvfi_rs1_rdata[channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
		(* keep *) wire [`RISCV_FORMAL_XLEN   - 1 : 0] rs2_rdata = rvfi_rs2_rdata[channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
		(* keep *) wire [                       4 : 0] rd_addr   = rvfi_rd_addr  [channel_idx*5  +:  5];
		(* keep *) wire [`RISCV_FORMAL_XLEN   - 1 : 0] rd_wdata  = rvfi_rd_wdata [channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
		(* keep *) wire [`RISCV_FORMAL_XLEN   - 1 : 0] pc_rdata  = rvfi_pc_rdata [channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
		(* keep *) wire [`RISCV_FORMAL_XLEN   - 1 : 0] pc_wdata  = rvfi_pc_wdata [channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];

		(* keep *) wire [`RISCV_FORMAL_XLEN   - 1 : 0] mem_addr  = rvfi_mem_addr [channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
		(* keep *) wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] mem_rmask = rvfi_mem_rmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];
		(* keep *) wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] mem_wmask = rvfi_mem_wmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];
		(* keep *) wire [`RISCV_FORMAL_XLEN   - 1 : 0] mem_rdata = rvfi_mem_rdata[channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];
		(* keep *) wire [`RISCV_FORMAL_XLEN   - 1 : 0] mem_wdata = rvfi_mem_wdata[channel_idx*`RISCV_FORMAL_XLEN   +: `RISCV_FORMAL_XLEN];

		(* keep *) wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] mem_fault_rmask = rvfi_mem_fault_rmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];
		(* keep *) wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] mem_fault_wmask = rvfi_mem_fault_wmask[channel_idx*`RISCV_FORMAL_XLEN/8 +: `RISCV_FORMAL_XLEN/8];

`ifdef RISCV_FORMAL_CSR_MCAUSE
		(* keep *) wire [`RISCV_FORMAL_XLEN-1:0] csr_mcause_wmask = rvfi_csr_mcause_wmask[channel_idx*`RISCV_FORMAL_XLEN +: `RISCV_FORMAL_XLEN];
		(* keep *) wire [`RISCV_FORMAL_XLEN-1:0] csr_mcause_wdata = rvfi_csr_mcause_wdata[channel_idx*`RISCV_FORMAL_XLEN +: `RISCV_FORMAL_XLEN];
`endif

		wire rfault = |mem_fault_rmask;
		wire wfault = |mem_fault_wmask;
		wire ifault = !(rfault || wfault);

		always @* begin
			if (!reset && check) begin
				assume(valid);
				if (mem_fault) begin

					assert (trap);
					assert (rd_addr == 0);
					assert (rd_wdata == 0);
					assert (mem_wmask == 0);

					cover (rfault);
					cover (wfault);
					cover (ifault);

					if (ifault) begin
						assert (insn == 0);
					end else begin
						assert (insn != 0);
					end

`ifdef RISCV_FORMAL_CSR_MCAUSE
					if (wfault) begin
						assert (&csr_mcause_wmask);
						assert (csr_mcause_wdata == 7);
					end else if (rfault) begin
						assert (&csr_mcause_wmask);
						assert (csr_mcause_wdata == 5);
					end else if (ifault) begin
						assert (&csr_mcause_wmask);
						assert (csr_mcause_wdata == 1);
					end
`endif
				else begin end
				end else begin
					assert (mem_fault_rmask == 0);
					assert (mem_fault_wmask == 0);
				end
			end
		end
`ifndef RISCV_FORMAL_CHANNEL_IDX
	end endgenerate
`endif
endmodule
