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

module rvfi_csr_ill_check (
	input clock, reset, check,
	`RVFI_INPUTS
);
	`RVFI_CHANNEL(rvfi, `RISCV_FORMAL_CHANNEL_IDX)

	wire csr_insn_valid = rvfi.valid && (rvfi.insn[6:0] == 7'b 1110011) && (rvfi.insn[13:12] != 0) && ((rvfi.insn >> 16 >> 16) == 0);
	wire [11:0] csr_insn_addr = rvfi.insn[31:20];

	wire csr_write = !rvfi.insn[13] || rvfi.insn[19:15];
	wire csr_read = rvfi.insn[11:7] != 0;

	always @* begin
		if (!reset && check) begin
			assume (csr_insn_valid);
			assume (csr_insn_addr == `RISCV_FORMAL_ILL_CSR_ADDR);
			if ( (0
				`ifdef RISCV_FORMAL_ILL_MMODE
					|| rvfi.mode == 3
					
				`endif
				`ifdef RISCV_FORMAL_ILL_SMODE
					|| rvfi.mode == 1
					
				`endif
				`ifdef RISCV_FORMAL_ILL_UMODE
					|| rvfi.mode == 0
					
				`endif
			) && (0
				`ifdef RISCV_FORMAL_ILL_WRITE
					|| csr_write
					
				`endif
				`ifdef RISCV_FORMAL_ILL_READ
					|| csr_read
					
				`endif
			) ) begin
				assert (rvfi.trap);
			end
		end
	end
endmodule
