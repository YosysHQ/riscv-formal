#!/usr/bin/env python3
#
# Copyright (C) 2017  Claire Xenia Wolf <claire@yosyshq.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import re

current_isa = []
isa_database: dict[str, set] = dict()
defaults_cache = None

MISA_A = 1 <<  0 # Atomic
MISA_B = 1 <<  1 # Bit manipulation
MISA_C = 1 <<  2 # Compressed
MISA_D = 1 <<  3 # Double-precision float
MISA_E = 1 <<  4 # RV32E base ISA
MISA_F = 1 <<  5 # Single-precision float
MISA_G = 1 <<  6 # Additional std extensions
MISA_H = 1 <<  7 # -reserved-
MISA_I = 1 <<  8 # RV32I/RV64I/RV128I base ISA
MISA_J = 1 <<  9 # -reserved-
MISA_K = 1 << 10 # -reserved-
MISA_L = 1 << 11 # -reserved-
MISA_M = 1 << 12 # Muliply/Divide
MISA_N = 1 << 13 # User-level interrupts
MISA_O = 1 << 14 # -reserved-
MISA_P = 1 << 15 # -reserved-
MISA_Q = 1 << 16 # Quad-precision float
MISA_R = 1 << 17 # -reserved-
MISA_S = 1 << 18 # Supervisor mode
MISA_T = 1 << 19 # -reserved-
MISA_U = 1 << 20 # User mode
MISA_V = 1 << 21 # -reserved-
MISA_W = 1 << 22 # -reserved-
MISA_X = 1 << 23 # Non-std extensions
MISA_Y = 1 << 24 # -reserved-
MISA_Z = 1 << 25 # -reserved-

def header(f, insn, isa_mode=False):
    if not isa_mode:
        global isa_database
        for isa in current_isa:
            if isa not in isa_database:
                isa_database[isa] = set()
            isa_database[isa].add(insn)

    global defaults_cache
    defaults_cache = dict()

    print("// DO NOT EDIT -- auto-generated from riscv-formal/insns/generate.py", file=f)
    print("", file=f)
    if isa_mode:
        print("module rvfi_isa_%s (" % insn, file=f)
    else:
        print("module rvfi_insn_%s (" % insn, file=f)

    print("  input                                 rvfi_valid,", file=f)
    print("  input  [`RISCV_FORMAL_ILEN   - 1 : 0] rvfi_insn,", file=f)
    print("  input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_pc_rdata,", file=f)
    print("  input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_rs1_rdata,", file=f)
    print("  input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_rs2_rdata,", file=f)
    print("  input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_mem_rdata,", file=f)

    print("`ifdef RISCV_FORMAL_CSR_MISA", file=f)
    print("  input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_csr_misa_rdata,", file=f)
    print("  output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_csr_misa_rmask,", file=f)
    print("`endif", file=f)

    print("", file=f)
    print("  output                                spec_valid,", file=f)
    print("  output                                spec_trap,", file=f)
    print("  output [                       4 : 0] spec_rs1_addr,", file=f)
    print("  output [                       4 : 0] spec_rs2_addr,", file=f)
    print("  output [                       4 : 0] spec_rd_addr,", file=f)
    print("  output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_rd_wdata,", file=f)
    print("  output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_pc_wdata,", file=f)
    print("  output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_mem_addr,", file=f)
    print("  output [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_mem_rmask,", file=f)
    print("  output [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_mem_wmask,", file=f)
    print("  output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_mem_wdata", file=f)

    print(");", file=f)

    defaults_cache["spec_valid"] = "0"
    defaults_cache["spec_rs1_addr"] = "0"
    defaults_cache["spec_rs2_addr"] = "0"
    defaults_cache["spec_rd_addr"] = "0"
    defaults_cache["spec_rd_wdata"] = "0"
    defaults_cache["spec_pc_wdata"] = "0"
    defaults_cache["spec_trap"] = "!misa_ok"
    defaults_cache["spec_mem_addr"] = "0"
    defaults_cache["spec_mem_rmask"] = "0"
    defaults_cache["spec_mem_wmask"] = "0"
    defaults_cache["spec_mem_wdata"] = "0"

def assign(f, sig, val):
    print("  assign %s = %s;" % (sig, val), file=f)

    if sig in defaults_cache:
        del defaults_cache[sig]

def misa_check(f, mask, ialign16=False):
    print("", file=f)
    print("`ifdef RISCV_FORMAL_CSR_MISA", file=f)
    print("  wire misa_ok = (rvfi_csr_misa_rdata & `RISCV_FORMAL_XLEN'h %x) == `RISCV_FORMAL_XLEN'h %x;" % (mask, mask), file=f)
    print("  assign spec_csr_misa_rmask = `RISCV_FORMAL_XLEN'h %x;" % ((mask|MISA_C) if ialign16 else mask), file=f)
    if ialign16:
        print("  wire ialign16 = (rvfi_csr_misa_rdata & `RISCV_FORMAL_XLEN'h %x) != `RISCV_FORMAL_XLEN'h 0;" % (MISA_C), file=f)
    print("`else", file=f)
    print("  wire misa_ok = 1;", file=f)
    if ialign16:
        print("`ifdef RISCV_FORMAL_COMPRESSED", file=f)
        print("  wire ialign16 = 1;", file=f)
        print("`else", file=f)
        print("  wire ialign16 = 0;", file=f)
        print("`endif", file=f)
    print("`endif", file=f)

def footer(f):
    def default_assign(sig):
        if sig in defaults_cache:
            print("  assign %s = %s;" % (sig, defaults_cache[sig]), file=f)

    if len(defaults_cache) != 0:
        print("", file=f)
        print("  // default assignments", file=f)

        default_assign("spec_valid")
        default_assign("spec_rs1_addr")
        default_assign("spec_rs2_addr")
        default_assign("spec_rd_addr")
        default_assign("spec_rd_wdata")
        default_assign("spec_pc_wdata")
        default_assign("spec_trap")
        default_assign("spec_mem_addr")
        default_assign("spec_mem_rmask")
        default_assign("spec_mem_wmask")
        default_assign("spec_mem_wdata")

    print("endmodule", file=f)

def format_r(f):
    print("", file=f)
    print("  // R-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;", file=f)
    print("  wire [6:0] insn_funct7 = rvfi_insn[31:25];", file=f)
    print("  wire [4:0] insn_rs2    = rvfi_insn[24:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[14:12];", file=f)
    print("  wire [4:0] insn_rd     = rvfi_insn[11: 7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_insn[ 6: 0];", file=f)

def format_ra(f):
    print("", file=f)
    print("  // R-type instruction format (atomics variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;", file=f)
    print("  wire [6:0] insn_funct5 = rvfi_insn[31:27];", file=f)
    print("  wire       insn_aq     = rvfi_insn[26];", file=f)
    print("  wire       insn_rl     = rvfi_insn[25];", file=f)
    print("  wire [4:0] insn_rs2    = rvfi_insn[24:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[14:12];", file=f)
    print("  wire [4:0] insn_rd     = rvfi_insn[11: 7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_insn[ 6: 0];", file=f)

def format_rb(f):
    print("", file=f)
    print("  // R-type instruction format (bitwise variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;", file=f)
    print("  wire [6:0] insn_funct6 = rvfi_insn[31:26];", file=f)
    print("  wire [5:0] insn_shamt  = rvfi_insn[25:20];", file=f)
    print("  wire [4:0] insn_rs2    = rvfi_insn[24:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[14:12];", file=f)
    print("  wire [4:0] insn_rd     = rvfi_insn[11: 7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_insn[ 6: 0];", file=f)

def format_i(f):
    print("", file=f)
    print("  // I-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed(rvfi_insn[31:20]);", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[14:12];", file=f)
    print("  wire [4:0] insn_rd     = rvfi_insn[11: 7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_insn[ 6: 0];", file=f)

def format_i_shift(f):
    print("", file=f)
    print("  // I-type instruction format (shift variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;", file=f)
    print("  wire [6:0] insn_funct6 = rvfi_insn[31:26];", file=f)
    print("  wire [5:0] insn_shamt  = rvfi_insn[25:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[14:12];", file=f)
    print("  wire [4:0] insn_rd     = rvfi_insn[11: 7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_insn[ 6: 0];", file=f)

def format_iB(f):
    print("", file=f)
    print("  // I-type instruction format (bytewise variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;", file=f)
    print("  wire [11:0] insn_funct12 = rvfi_insn[31:20];", file=f)
    print("  wire [ 4:0] insn_rs1     = rvfi_insn[19:15];", file=f)
    print("  wire [ 2:0] insn_funct3  = rvfi_insn[14:12];", file=f)
    print("  wire [ 4:0] insn_rd      = rvfi_insn[11: 7];", file=f)
    print("  wire [ 6:0] insn_opcode  = rvfi_insn[ 6: 0];", file=f)

def format_b(f):
    print("", file=f)
    # TODO: figure out if there is an official name for this format
    print("  // B-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;", file=f)
    print("  wire [6:0] insn_funct7 = rvfi_insn[31:25];", file=f)
    print("  wire [4:0] insn_funct5 = rvfi_insn[24:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[14:12];", file=f)
    print("  wire [4:0] insn_rd     = rvfi_insn[11: 7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_insn[ 6: 0];", file=f)

def format_s(f):
    print("", file=f)
    print("  // S-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_insn[31:25], rvfi_insn[11:7]});", file=f)
    print("  wire [4:0] insn_rs2    = rvfi_insn[24:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[14:12];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_insn[ 6: 0];", file=f)

def format_sb(f):
    print("", file=f)
    print("  // SB-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_insn[31], rvfi_insn[7], rvfi_insn[30:25], rvfi_insn[11:8], 1'b0});", file=f)
    print("  wire [4:0] insn_rs2    = rvfi_insn[24:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[14:12];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_insn[ 6: 0];", file=f)

def format_u(f):
    print("", file=f)
    print("  // U-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_insn[31:12], 12'b0});", file=f)
    print("  wire [4:0] insn_rd     = rvfi_insn[11:7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_insn[ 6:0];", file=f)

def format_uj(f):
    print("", file=f)
    print("  // UJ-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16 >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_insn[31], rvfi_insn[19:12], rvfi_insn[20], rvfi_insn[30:21], 1'b0});", file=f)
    print("  wire [4:0] insn_rd     = rvfi_insn[11:7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_insn[6:0];", file=f)

def format_cr(f):
    print("", file=f)
    print("  // CI-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    print("  wire [3:0] insn_funct4 = rvfi_insn[15:12];", file=f)
    print("  wire [4:0] insn_rs1_rd = rvfi_insn[11:7];", file=f)
    print("  wire [4:0] insn_rs2 = rvfi_insn[6:2];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_ci(f):
    print("", file=f)
    print("  // CI-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_insn[12], rvfi_insn[6:2]});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1_rd = rvfi_insn[11:7];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_ci_sp(f):
    print("", file=f)
    print("  // CI-type instruction format (SP variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_insn[12], rvfi_insn[4:3], rvfi_insn[5], rvfi_insn[2], rvfi_insn[6], 4'b0});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1_rd = rvfi_insn[11:7];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_ci_lui(f):
    print("", file=f)
    print("  // CI-type instruction format (LUI variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_insn[12], rvfi_insn[6:2], 12'b0});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1_rd = rvfi_insn[11:7];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_ci_sri(f):
    print("", file=f)
    print("  // CI-type instruction format (SRI variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    print("  wire [5:0] insn_shamt = {rvfi_insn[12], rvfi_insn[6:2]};", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [1:0] insn_funct2 = rvfi_insn[11:10];", file=f)
    print("  wire [4:0] insn_rs1_rd = {1'b1, rvfi_insn[9:7]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_ci_sli(f):
    print("", file=f)
    print("  // CI-type instruction format (SLI variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    print("  wire [5:0] insn_shamt = {rvfi_insn[12], rvfi_insn[6:2]};", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1_rd = rvfi_insn[11:7];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_ci_andi(f):
    print("", file=f)
    print("  // CI-type instruction format (ANDI variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_insn[12], rvfi_insn[6:2]});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [1:0] insn_funct2 = rvfi_insn[11:10];", file=f)
    print("  wire [4:0] insn_rs1_rd = {1'b1, rvfi_insn[9:7]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_ci_lsp(f, numbytes):
    print("", file=f)
    print("  // CI-type instruction format (LSP variation, %d bit version)" % (8*numbytes), file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    if numbytes == 4:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_insn[3:2], rvfi_insn[12], rvfi_insn[6:4], 2'b00};", file=f)
    elif numbytes == 8:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_insn[4:2], rvfi_insn[12], rvfi_insn[6:5], 3'b000};", file=f)
    else:
        assert False
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [4:0] insn_rd = rvfi_insn[11:7];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_cl(f, numbytes):
    print("", file=f)
    print("  // CL-type instruction format (%d bit version)" % (8*numbytes), file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    if numbytes == 4:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_insn[5], rvfi_insn[12:10], rvfi_insn[6], 2'b00};", file=f)
    elif numbytes == 8:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_insn[6:5], rvfi_insn[12:10], 3'b000};", file=f)
    else:
        assert False
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1 = {1'b1, rvfi_insn[9:7]};", file=f)
    print("  wire [4:0] insn_rd = {1'b1, rvfi_insn[4:2]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_css(f, numbytes):
    print("", file=f)
    print("  // CSS-type instruction format (%d bit version)" % (8*numbytes), file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    if numbytes == 4:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_insn[8:7], rvfi_insn[12:9], 2'b00};", file=f)
    elif numbytes == 8:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_insn[9:7], rvfi_insn[12:10], 3'b000};", file=f)
    else:
        assert False
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [4:0] insn_rs2 = rvfi_insn[6:2];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_cs(f, numbytes):
    print("", file=f)
    print("  // CS-type instruction format (%d bit version)" % (8*numbytes), file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    if numbytes == 4:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_insn[5], rvfi_insn[12:10], rvfi_insn[6], 2'b00};", file=f)
    elif numbytes == 8:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_insn[6:5], rvfi_insn[12:10], 3'b000};", file=f)
    else:
        assert False
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1 = {1'b1, rvfi_insn[9:7]};", file=f)
    print("  wire [4:0] insn_rs2 = {1'b1, rvfi_insn[4:2]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_cs_alu(f):
    print("", file=f)
    print("  // CS-type instruction format (ALU version)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    print("  wire [5:0] insn_funct6 = rvfi_insn[15:10];", file=f)
    print("  wire [1:0] insn_funct2 = rvfi_insn[6:5];", file=f)
    print("  wire [4:0] insn_rs1_rd = {1'b1, rvfi_insn[9:7]};", file=f)
    print("  wire [4:0] insn_rs2 = {1'b1, rvfi_insn[4:2]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_ciw(f):
    print("", file=f)
    print("  // CIW-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_insn[10:7], rvfi_insn[12:11], rvfi_insn[5], rvfi_insn[6], 2'b00};", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [4:0] insn_rd = {1'b1, rvfi_insn[4:2]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_cb(f):
    print("", file=f)
    print("  // CB-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_insn[12], rvfi_insn[6:5], rvfi_insn[2], rvfi_insn[11:10], rvfi_insn[4:3], 1'b0});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1 = {1'b1, rvfi_insn[9:7]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def format_cj(f):
    print("", file=f)
    print("  // CJ-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_insn[12], rvfi_insn[8], rvfi_insn[10], rvfi_insn[9],", file=f)
    print("      rvfi_insn[6], rvfi_insn[7], rvfi_insn[2], rvfi_insn[11], rvfi_insn[5], rvfi_insn[4], rvfi_insn[3], 1'b0});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_insn[15:13];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_insn[1:0];", file=f)

def insn_lui(insn="lui", misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_u(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_opcode == 7'b 0110111")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? insn_imm : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_auipc(insn="auipc", misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_u(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_opcode == 7'b 0010111")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? rvfi_pc_rdata + insn_imm : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_jal(insn="jal", misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_uj(f)
        misa_check(f, misa,  ialign16=True)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = rvfi_pc_rdata + insn_imm;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_opcode == 7'b 1101111")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? rvfi_pc_rdata + 4 : 0")
        assign(f, "spec_pc_wdata", "next_pc")
        assign(f, "spec_trap", "(ialign16 ? (next_pc[0] != 0) : (next_pc[1:0] != 0)) || !misa_ok")

        footer(f)

def insn_jalr(insn="jalr", misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_i(f)
        misa_check(f, misa, ialign16=True)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = (rvfi_rs1_rdata + insn_imm) & ~1;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b 000 && insn_opcode == 7'b 1100111")
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? rvfi_pc_rdata + 4 : 0")
        assign(f, "spec_pc_wdata", "next_pc")
        assign(f, "spec_trap", "(ialign16 ? (next_pc[0] != 0) : (next_pc[1:0] != 0)) || !misa_ok")

        footer(f)

def insn_b(insn, funct3, expr, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_sb(f)
        misa_check(f, misa, ialign16=True)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire cond = %s;" % expr, file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = cond ? rvfi_pc_rdata + insn_imm : rvfi_pc_rdata + 4;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 7'b 1100011" % funct3)
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_pc_wdata", "next_pc")
        assign(f, "spec_trap", "(ialign16 ? (next_pc[0] != 0) : (next_pc[1:0] != 0)) || !misa_ok")

        footer(f)

def insn_l(insn, funct3, numbytes, signext, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_i(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_mem_rdata >> (8*(addr-spec_mem_addr));" % (8*numbytes-1), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 7'b 0000011" % funct3)
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "spec_mem_rmask", "((1 << %d)-1) << (addr-spec_mem_addr)" % numbytes)
        if signext:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? $signed(result) : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")
        assign(f, "spec_trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_mem_rdata;" % (8*numbytes-1), file=f)
        assign(f, "spec_valid", "rvfi_valid && insn_funct3 == 3'b %s && insn_opcode == 7'b 0000011" % funct3)
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_mem_addr", "addr")
        assign(f, "spec_mem_rmask", "((1 << %d)-1)" % numbytes)
        if signext:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? $signed(result) : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")
        assign(f, "spec_trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

def insn_s(insn, funct3, numbytes, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_s(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata + insn_imm;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 7'b 0100011" % funct3)
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "spec_mem_wmask", "((1 << %d)-1) << (addr-spec_mem_addr)" % numbytes)
        assign(f, "spec_mem_wdata", "rvfi_rs2_rdata << (8*(addr-spec_mem_addr))")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")
        assign(f, "spec_trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata + insn_imm;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 7'b 0100011" % funct3)
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_mem_addr", "addr")
        assign(f, "spec_mem_wmask", "((1 << %d)-1)" % numbytes)
        assign(f, "spec_mem_wdata", "rvfi_rs2_rdata")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")
        assign(f, "spec_trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

def insn_imm(insn, funct3, expr, wmode=False, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_i(f)
        misa_check(f, misa)

        if wmode:
            result_range = "31:0"
            opcode = "0011011"
        else:
            result_range = "`RISCV_FORMAL_XLEN-1:0"
            opcode = "0010011"

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [%s] result = %s;" % (result_range, expr), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 7'b %s" % (funct3, opcode))
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rd_addr", "insn_rd")
        if wmode:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? {{`RISCV_FORMAL_XLEN-32{result[31]}}, result} : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_shimm(insn, funct6, funct3, expr, wmode=False, uwmode=False, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_i_shift(f)
        misa_check(f, misa)

        if uwmode:
            assert not wmode
            xtra_shamt_check = "1"
            result_range = "`RISCV_FORMAL_XLEN-1:0"
            opcode = "0011011"
        elif wmode:
            xtra_shamt_check = "!insn_shamt[5]"
            result_range = "31:0"
            opcode = "0011011"
        else:
            xtra_shamt_check = "(!insn_shamt[5] || `RISCV_FORMAL_XLEN == 64)"
            result_range = "`RISCV_FORMAL_XLEN-1:0"
            opcode = "0010011"

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [%s] result = %s;" % (result_range, expr), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct6 == 6'b %s && insn_funct3 == 3'b %s && insn_opcode == 7'b %s && %s" % (funct6, funct3, opcode, xtra_shamt_check))
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rd_addr", "insn_rd")
        if wmode:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? {{`RISCV_FORMAL_XLEN-32{result[31]}}, result} : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_alu(insn, funct7, funct3, expr, alt_add=None, alt_sub=None, shamt=False, wmode=False, uwmode=False, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_r(f)
        misa_check(f, misa)

        if uwmode:
            assert not wmode
            result_range = "`RISCV_FORMAL_XLEN-1:0"
            opcode = "0111011"
        elif wmode:
            result_range = "31:0"
            opcode = "0111011"
        else:
            result_range = "`RISCV_FORMAL_XLEN-1:0"
            opcode = "0110011"

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        if shamt:
            if wmode:
                print("  wire [4:0] shamt = rvfi_rs2_rdata[4:0];", file=f)
            else:
                print("  wire [5:0] shamt = `RISCV_FORMAL_XLEN == 64 ? rvfi_rs2_rdata[5:0] : rvfi_rs2_rdata[4:0];", file=f)
        if alt_add is not None or alt_sub is not None:
            print("`ifdef RISCV_FORMAL_ALTOPS", file=f)
            if alt_add is not None:
                print("  wire [%s] altops_bitmask = 64'h%016x;" % (result_range, alt_add), file=f)
                print("  wire [%s] result = (rvfi_rs1_rdata + rvfi_rs2_rdata) ^ altops_bitmask;" % result_range, file=f)
            else:
                print("  wire [%s] altops_bitmask = 64'h%016x;" % (result_range, alt_sub), file=f)
                print("  wire [%s] result = (rvfi_rs1_rdata - rvfi_rs2_rdata) ^ altops_bitmask;" % result_range, file=f)
            print("`else", file=f)
            print("  wire [%s] result = %s;" % (result_range, expr), file=f)
            print("`endif", file=f)
        else:
            print("  wire [%s] result = %s;" % (result_range, expr), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct7 == 7'b %s && insn_funct3 == 3'b %s && insn_opcode == 7'b %s" % (funct7, funct3, opcode))
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_rd_addr", "insn_rd")
        if wmode:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? {{`RISCV_FORMAL_XLEN-32{result[31]}}, result} : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_amo(insn, funct5, funct3, expr, misa=MISA_A):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ra(f)
        misa_check(f, misa)

        if funct3 == "010":
            oprange = "31:0"
            numbytes = 4
        else:
            oprange = "63:0"
            numbytes = 8

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [%s] mem_result = %s;" % (oprange, expr), file=f)
        print("  wire [%s] reg_result = rvfi_mem_rdata[%s];" % (oprange, oprange), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata;", file=f)

        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct5 == 5'b %s && insn_funct3 == 3'b %s && insn_opcode == 7'b 0101111" % (funct5, funct3))
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? $signed(reg_result) : 0")
        assign(f, "spec_mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "spec_mem_wmask", "((1 << %d)-1) << (addr-spec_mem_addr)" % numbytes)
        assign(f, "spec_mem_wdata", "mem_result << (8*(addr-spec_mem_addr))")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")
        assign(f, "spec_trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct5 == 5'b %s && insn_funct3 == 3'b %s && insn_opcode == 7'b 0101111" % (funct5, funct3))
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? $signed(reg_result) : 0")
        assign(f, "spec_mem_addr", "addr")
        assign(f, "spec_mem_wmask", "((1 << %d)-1)" % numbytes)
        assign(f, "spec_mem_wdata", "mem_result")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")
        assign(f, "spec_trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`endif", file=f)

        footer(f)

def insn_c_addi4spn(insn="c_addi4spn", misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ciw(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_rs1_rdata + insn_imm;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b 000 && insn_opcode == 2'b 00 && insn_imm")
        assign(f, "spec_rs1_addr", "2")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")

        footer(f)

def insn_c_l(insn, funct3, numbytes, signext, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cl(f, numbytes)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_mem_rdata >> (8*(addr-spec_mem_addr));" % (8*numbytes-1), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 00" % funct3)
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "spec_mem_rmask", "((1 << %d)-1) << (addr-spec_mem_addr)" % numbytes)
        if signext:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? $signed(result) : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")
        assign(f, "spec_trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_mem_rdata;" % (8*numbytes-1), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 00" % funct3)
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_mem_addr", "addr")
        assign(f, "spec_mem_rmask", "((1 << %d)-1)" % numbytes)
        if signext:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? $signed(result) : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")
        assign(f, "spec_trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

def insn_c_s(insn, funct3, numbytes, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cs(f, numbytes)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata + insn_imm;", file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 00" % funct3)
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "spec_mem_wmask", "((1 << %d)-1) << (addr-spec_mem_addr)" % numbytes)
        assign(f, "spec_mem_wdata", "rvfi_rs2_rdata << (8*(addr-spec_mem_addr))")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")
        assign(f, "spec_trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 00" % funct3)
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_mem_addr", "addr")
        assign(f, "spec_mem_wmask", "((1 << %d)-1)" % numbytes)
        assign(f, "spec_mem_wdata", "rvfi_rs2_rdata")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")
        assign(f, "spec_trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

def insn_c_addi(insn="c_addi", wmode=False, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        if wmode:
            print("  wire [31:0] result = rvfi_rs1_rdata[31:0] + insn_imm[31:0];", file=f)
            assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b 001 && insn_opcode == 2'b 01 && insn_rs1_rd != 5'd 0")
        else:
            print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_rs1_rdata + insn_imm;", file=f)
            assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b 000 && insn_opcode == 2'b 01")
        assign(f, "spec_rs1_addr", "insn_rs1_rd")
        assign(f, "spec_rd_addr", "insn_rs1_rd")
        if wmode:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? {{`RISCV_FORMAL_XLEN-32{result[31]}}, result} : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")

        footer(f)

def insn_c_jal(insn, funct3, link, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cj(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = rvfi_pc_rdata + insn_imm;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 01" % (funct3))
        if link:
            assign(f, "spec_rd_addr", "5'd 1")
            assign(f, "spec_rd_wdata", "rvfi_pc_rdata + 2")
        assign(f, "spec_pc_wdata", "next_pc")

        footer(f)

def insn_c_li(insn="c_li", misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = insn_imm;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b 010 && insn_opcode == 2'b 01")
        assign(f, "spec_rd_addr", "insn_rs1_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")

        footer(f)

def insn_c_addi16sp(insn="c_addi16sp", misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_sp(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_rs1_rdata + insn_imm;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b 011 && insn_opcode == 2'b 01 && insn_rs1_rd == 5'd 2 && insn_imm")
        assign(f, "spec_rs1_addr", "insn_rs1_rd")
        assign(f, "spec_rd_addr", "insn_rs1_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")

        footer(f)

def insn_c_lui(insn="c_lui", misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_lui(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = insn_imm;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b 011 && insn_opcode == 2'b 01 && insn_rs1_rd != 5'd 2 && insn_imm")
        assign(f, "spec_rd_addr", "insn_rs1_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")

        footer(f)

def insn_c_sri(insn, funct2, expr, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_sri(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = %s;" % expr, file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b 100 && insn_funct2 == 2'b %s && insn_opcode == 2'b 01 && (!insn_shamt[5] || `RISCV_FORMAL_XLEN == 64)" % funct2)
        assign(f, "spec_rs1_addr", "insn_rs1_rd")
        assign(f, "spec_rd_addr", "insn_rs1_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")

        footer(f)

def insn_c_andi(insn="c_andi", misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_andi(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_rs1_rdata & insn_imm;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b 100 && insn_funct2 == 2'b 10 && insn_opcode == 2'b 01")
        assign(f, "spec_rs1_addr", "insn_rs1_rd")
        assign(f, "spec_rd_addr", "insn_rs1_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")

        footer(f)

def insn_c_alu(insn, funct6, funct2, expr, wmode=False, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cs_alu(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        if wmode:
            print("  wire [31:0] result = %s;" % expr, file=f)
        else:
            print("  wire [`RISCV_FORMAL_XLEN-1:0] result = %s;" % expr, file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct6 == 6'b %s && insn_funct2 == 2'b %s && insn_opcode == 2'b 01" % (funct6, funct2))
        assign(f, "spec_rs1_addr", "insn_rs1_rd")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_rd_addr", "insn_rs1_rd")
        if wmode:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? {{`RISCV_FORMAL_XLEN-32{result[31]}}, result} : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")

        footer(f)

def insn_c_b(insn, funct3, expr, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cb(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire cond = %s;" % expr, file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = cond ? rvfi_pc_rdata + insn_imm : rvfi_pc_rdata + 2;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 01" % funct3)
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_pc_wdata", "next_pc")
        assign(f, "spec_trap", "(next_pc[0] != 0) || !misa_ok")

        footer(f)

def insn_c_sli(insn, expr, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_sli(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = %s;" % expr, file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b 000 && insn_opcode == 2'b 10 && (!insn_shamt[5] || `RISCV_FORMAL_XLEN == 64)")
        assign(f, "spec_rs1_addr", "insn_rs1_rd")
        assign(f, "spec_rd_addr", "insn_rs1_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")

        footer(f)

def insn_c_lsp(insn, funct3, numbytes, signext, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_lsp(f, numbytes)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_mem_rdata >> (8*(addr-spec_mem_addr));" % (8*numbytes-1), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 10 && insn_rd" % funct3)
        assign(f, "spec_rs1_addr", "2")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "spec_mem_rmask", "((1 << %d)-1) << (addr-spec_mem_addr)" % numbytes)
        if signext:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? $signed(result) : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")
        assign(f, "spec_trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_mem_rdata;" % (8*numbytes-1), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 10 && insn_rd" % funct3)
        assign(f, "spec_rs1_addr", "2")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_mem_addr", "addr")
        assign(f, "spec_mem_rmask", "((1 << %d)-1)" % numbytes)
        if signext:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? $signed(result) : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")
        assign(f, "spec_trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

def insn_c_ssp(insn, funct3, numbytes, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_css(f, numbytes)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata + insn_imm;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 10" % funct3)
        assign(f, "spec_rs1_addr", "2")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "spec_mem_wmask", "((1 << %d)-1) << (addr-spec_mem_addr)" % numbytes)
        assign(f, "spec_mem_wdata", "rvfi_rs2_rdata << (8*(addr-spec_mem_addr))")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")
        assign(f, "spec_trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_rs1_rdata + insn_imm;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 10" % funct3)
        assign(f, "spec_rs1_addr", "2")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_mem_addr", "addr")
        assign(f, "spec_mem_wmask", "((1 << %d)-1)" % numbytes)
        assign(f, "spec_mem_wdata", "rvfi_rs2_rdata")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")
        assign(f, "spec_trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

def insn_c_jalr(insn, funct4, link, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cr(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = rvfi_rs1_rdata & ~1;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct4 == 4'b %s && insn_rs1_rd && !insn_rs2 && insn_opcode == 2'b 10" % funct4)
        assign(f, "spec_rs1_addr", "insn_rs1_rd")
        if link:
            assign(f, "spec_rd_addr", "5'd 1")
            assign(f, "spec_rd_wdata", "rvfi_pc_rdata + 2")
        assign(f, "spec_pc_wdata", "next_pc")
        assign(f, "spec_trap", "(next_pc[0] != 0) || !misa_ok")

        footer(f)

def insn_c_mvadd(insn, funct4, add, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cr(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        if add:
            print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_rs1_rdata + rvfi_rs2_rdata;", file=f)
        else:
            print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_rs2_rdata;", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct4 == 4'b %s && insn_rs2 && insn_opcode == 2'b 10" % funct4)
        if add:
            assign(f, "spec_rs1_addr", "insn_rs1_rd")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_rd_addr", "insn_rs1_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 2")

        footer(f)

def insn_count(insn, funct5, trailing=False, pop=False, wmode=False, misa=MISA_B):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_b(f)
        misa_check(f, misa)

        if wmode:
            result_width = "32"
            result_range = "31:0"
            opcode = "0011011"
        else:
            result_width = "`RISCV_FORMAL_XLEN"
            result_range = "`RISCV_FORMAL_XLEN-1:0"
            opcode = "0010011"

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  integer i;", file=f)
        print("  reg [%s] result;" % result_range, file=f)
        print("  reg found;", file=f)

        print("  always @(rvfi_rs1_rdata)", file=f)
        print("  begin", file=f)
        print("    result = 0;", file=f)
        print("    found = 0;", file=f)
        print(f"    for (i=0; i<{result_width}; i=i+1)", file=f)
        print("    begin", file=f)
        if pop: # count all ones
            assert not trailing
            print("      result = result + rvfi_rs1_rdata[i];", file=f)
        elif trailing: # count trailing zeros
            print("      found = found | rvfi_rs1_rdata[i];", file=f)
            print("      result = result + !(rvfi_rs1_rdata[i] | found);", file=f)
        else: # count leading zeros
            print("      if (rvfi_rs1_rdata[i] == 1'b1)", file=f)
            print("        result = 0;", file=f)
            print("      else", file=f)
            print("        result = result + 1;", file=f)
        print("    end", file=f)
        print("  end", file=f)

        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct7 == 7'b 0110000 && insn_funct5 == 5'b %s && insn_funct3 == 3'b 001 && insn_opcode == 7'b %s" % (funct5, opcode))
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rd_addr", "insn_rd")
        if wmode:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? {{`RISCV_FORMAL_XLEN-32{result[31]}}, result} : 0")
        else:
            assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_ext(insn, funct5, signed=False, bmode=False, misa=MISA_B):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_b(f)
        misa_check(f, misa)

        if bmode:
            result_width = "8"
        else: # hmode
            result_width = "16"

        if signed:
            funct7 = "0110000"
            funct3 = "001"
            opcode = "7'b 0010011"
            result_extension = f"result[{result_width}-1]"
        else:
            funct7 = "0000100"
            funct3 = "100"
            opcode = "{3'b 011, `RISCV_FORMAL_XLEN != 32, 3'b 011}"
            result_extension = "1'b 0"

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [%s-1:0] result = rvfi_rs1_rdata[%s-1:0];" % (result_width, result_width), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct7 == 7'b %s && insn_funct5 == 5'b %s && insn_funct3 == 3'b %s && insn_opcode == %s" % (funct7, funct5, funct3, opcode))
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? {{`RISCV_FORMAL_XLEN-%s{%s}}, result} : 0" % (result_width, result_extension))
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_bit(insn, funct6, funct3, expr, imode=False, misa=MISA_B):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_rb(f)
        misa_check(f, misa)

        if imode:
            opcode = "0010011"
            xtra_shamt_check = "(!insn_shamt[5] || `RISCV_FORMAL_XLEN == 64)"
            index = "insn_shamt & (`RISCV_FORMAL_XLEN - 1)"
        else:
            opcode = "0110011"
            xtra_shamt_check = "!insn_shamt[5]"
            index = "rvfi_rs2_rdata & (`RISCV_FORMAL_XLEN - 1)"

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] index = %s;" % index, file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = %s;" % expr, file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct6 == 6'b %s && insn_funct3 == 3'b %s && insn_opcode == 7'b %s && %s" % (funct6, funct3, opcode, xtra_shamt_check))
        assign(f, "spec_rs1_addr", "insn_rs1")
        if not imode:
            assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_bytes(insn, funct12, funct3, expr, bitwise=False, misa=MISA_B):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_iB(f)
        misa_check(f, misa)

        opcode = "0010011"

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  reg [`RISCV_FORMAL_XLEN-1:0] result;", file=f)
        print("  integer i;", file=f)
        if bitwise:
            print("  integer j;", file=f)

        print("  localparam integer nbytes = `RISCV_FORMAL_XLEN / 8;", file=f)
        print("  always @(rvfi_rs1_rdata)", file=f)
        print("  begin", file=f)
        print("    result = 0;", file=f)
        print("    for (i=0; i<nbytes; i=i+1)", file=f)
        print("    begin", file=f)
        if bitwise:
            print("      for (j=0; j<8; j=j+1)", file=f)
            print("      begin", file=f)
            print(f"        result[i*8+j] = {expr};", file=f)
            print("      end", file=f)
        else:
            print(f"      result[i*8+:8] = {expr};", file=f)
        print("    end", file=f)
        print("  end", file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct12 == %s && insn_funct3 == 3'b %s && insn_opcode == 7'b %s" % (funct12, funct3, opcode))
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_clmul(insn, funct3, expr, index1=False, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_r(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  integer i;", file=f)
        print("  reg [`RISCV_FORMAL_XLEN-1:0] result;", file=f)

        if index1:
            i_first = "1"
            i_last = "`RISCV_FORMAL_XLEN+1"
        else:
            i_first = "0"
            i_last = "`RISCV_FORMAL_XLEN"

        print("  always @(rvfi_rs1_rdata, rvfi_rs2_rdata)", file=f)
        print("  begin", file=f)
        print("    result = 0;", file=f)
        print(f"    for (i={i_first}; i<{i_last}; i=i+1)", file=f)
        print("    begin", file=f)
        print("      if ((rvfi_rs2_rdata >> i) & 1)", file=f)
        print(f"        result = result ^ ({expr});", file=f)
        print("      else", file=f)
        print("        result = result;", file=f)
        print("    end", file=f)
        print("  end", file=f)

        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct7 == 7'b 0000101 && insn_funct3 == 3'b %s && insn_opcode == 7'b 0110011" % funct3)
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_pack(insn="pack", funct3="100", result_width="`RISCV_FORMAL_XLEN", signed=False, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_r(f)
        misa_check(f, misa)

        input_width = f"({result_width}/2)"

        if signed:
            opcode = "01110_11"
            result_extension = f"result[{result_width}-1]"
        else:
            opcode = "0110011"
            result_extension = "1'b 0"

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [%s-1:0] result = {rvfi_rs2_rdata[%s-1:0], rvfi_rs1_rdata[%s-1:0]};" % (result_width, input_width, input_width), file=f)
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct7 == 7'b 0000100 && insn_funct3 == 3'b %s && insn_opcode == 7'b %s" % (funct3, opcode))
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? {{`RISCV_FORMAL_XLEN-%s{%s}}, result} : 0" % (result_width, result_extension))
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_zip(insn, funct3, unzip=False, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_b(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  reg [`RISCV_FORMAL_XLEN-1:0] result;", file=f)
        print("  integer i;", file=f)

        print("  always @(rvfi_rs1_rdata)", file=f)
        print("  begin", file=f)
        print("    result = 0;", file=f)
        print(f"    for (i=0; i<(`RISCV_FORMAL_XLEN/2); i=i+1)", file=f)
        print("    begin", file=f)
        if unzip:
            print("      result[i] = rvfi_rs1_rdata[2*i];", file=f)
            print("      result[i + `RISCV_FORMAL_XLEN/2] = rvfi_rs1_rdata[2*i + 1];", file=f)
        else:
            print("      result[2*i] = rvfi_rs1_rdata[i];", file=f)
            print("      result[2*i + 1] = rvfi_rs1_rdata[i + `RISCV_FORMAL_XLEN/2];", file=f)
        print("    end", file=f)
        print("  end", file=f)

        assign(f, "spec_valid", "rvfi_valid && !insn_padding && `RISCV_FORMAL_XLEN==32 && insn_funct7 == 7'b 0000100 && insn_funct5 == 5'b 01111 && insn_funct3 == 3'b %s && insn_opcode == 7'b 0010011" % (funct3))
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

def insn_xperm(insn, funct3, width, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_r(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  reg [`RISCV_FORMAL_XLEN-1:0] result;", file=f)
        print("  integer i;", file=f)

        print("  always @(rvfi_rs1_rdata, rvfi_rs2_rdata)", file=f)
        print("  begin", file=f)
        print("    result = 0;", file=f)
        print(f"    for (i=0; i<`RISCV_FORMAL_XLEN; i=i+{width})", file=f)
        print("    begin", file=f)
        print(f"      result[i+:{width}] = (rvfi_rs1_rdata >> rvfi_rs2_rdata[i+:{width}]) & {{{width}{{1'b1}}}};", file=f)
        print("    end", file=f)
        print("  end", file=f)
        
        assign(f, "spec_valid", "rvfi_valid && !insn_padding && insn_funct7 == 7'b 0010100 && insn_funct3 == 3'b %s && insn_opcode == 7'b 01100_11" % (funct3))
        assign(f, "spec_rs1_addr", "insn_rs1")
        assign(f, "spec_rs2_addr", "insn_rs2")
        assign(f, "spec_rd_addr", "insn_rd")
        assign(f, "spec_rd_wdata", "spec_rd_addr ? result : 0")
        assign(f, "spec_pc_wdata", "rvfi_pc_rdata + 4")

        footer(f)

## Base Integer ISA (I)

current_isa = ["rv32i"]

insn_lui()
insn_auipc()
insn_jal()
insn_jalr()

insn_b("beq",  "000", "rvfi_rs1_rdata == rvfi_rs2_rdata")
insn_b("bne",  "001", "rvfi_rs1_rdata != rvfi_rs2_rdata")
insn_b("blt",  "100", "$signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)")
insn_b("bge",  "101", "$signed(rvfi_rs1_rdata) >= $signed(rvfi_rs2_rdata)")
insn_b("bltu", "110", "rvfi_rs1_rdata < rvfi_rs2_rdata")
insn_b("bgeu", "111", "rvfi_rs1_rdata >= rvfi_rs2_rdata")

insn_l("lb",  "000", 1, True)
insn_l("lh",  "001", 2, True)
insn_l("lw",  "010", 4, True)
insn_l("lbu", "100", 1, False)
insn_l("lhu", "101", 2, False)

insn_s("sb",  "000", 1)
insn_s("sh",  "001", 2)
insn_s("sw",  "010", 4)

insn_imm("addi",  "000", "rvfi_rs1_rdata + insn_imm")
insn_imm("slti",  "010", "$signed(rvfi_rs1_rdata) < $signed(insn_imm)")
insn_imm("sltiu", "011", "rvfi_rs1_rdata < insn_imm")
insn_imm("xori",  "100", "rvfi_rs1_rdata ^ insn_imm")
insn_imm("ori",   "110", "rvfi_rs1_rdata | insn_imm")
insn_imm("andi",  "111", "rvfi_rs1_rdata & insn_imm")

insn_shimm("slli", "000000", "001", "rvfi_rs1_rdata << insn_shamt")
insn_shimm("srli", "000000", "101", "rvfi_rs1_rdata >> insn_shamt")
insn_shimm("srai", "010000", "101", "$signed(rvfi_rs1_rdata) >>> insn_shamt")

insn_alu("add",  "0000000", "000", "rvfi_rs1_rdata + rvfi_rs2_rdata")
insn_alu("sub",  "0100000", "000", "rvfi_rs1_rdata - rvfi_rs2_rdata")
insn_alu("sll",  "0000000", "001", "rvfi_rs1_rdata << shamt", shamt=True)
insn_alu("slt",  "0000000", "010", "$signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)")
insn_alu("sltu", "0000000", "011", "rvfi_rs1_rdata < rvfi_rs2_rdata")
insn_alu("xor",  "0000000", "100", "rvfi_rs1_rdata ^ rvfi_rs2_rdata")
insn_alu("srl",  "0000000", "101", "rvfi_rs1_rdata >> shamt", shamt=True)
insn_alu("sra",  "0100000", "101", "$signed(rvfi_rs1_rdata) >>> shamt", shamt=True)
insn_alu("or",   "0000000", "110", "rvfi_rs1_rdata | rvfi_rs2_rdata")
insn_alu("and",  "0000000", "111", "rvfi_rs1_rdata & rvfi_rs2_rdata")

current_isa = ["rv64i"]

insn_l("lwu", "110", 4, False)
insn_l("ld",  "011", 8, True)
insn_s("sd",  "011", 8)

insn_imm("addiw",  "000", "rvfi_rs1_rdata[31:0] + insn_imm[31:0]", wmode=True)

insn_shimm("slliw", "000000", "001", "rvfi_rs1_rdata[31:0] << insn_shamt", wmode=True)
insn_shimm("srliw", "000000", "101", "rvfi_rs1_rdata[31:0] >> insn_shamt", wmode=True)
insn_shimm("sraiw", "010000", "101", "$signed(rvfi_rs1_rdata[31:0]) >>> insn_shamt", wmode=True)

insn_alu("addw", "0000000", "000", "rvfi_rs1_rdata[31:0] + rvfi_rs2_rdata[31:0]", wmode=True)
insn_alu("subw", "0100000", "000", "rvfi_rs1_rdata[31:0] - rvfi_rs2_rdata[31:0]", wmode=True)
insn_alu("sllw", "0000000", "001", "rvfi_rs1_rdata[31:0] << shamt", shamt=True, wmode=True)
insn_alu("srlw", "0000000", "101", "rvfi_rs1_rdata[31:0] >> shamt", shamt=True, wmode=True)
insn_alu("sraw", "0100000", "101", "$signed(rvfi_rs1_rdata[31:0]) >>> shamt", shamt=True, wmode=True)

## Multiply/Divide ISA (M)

current_isa = ["rv32im"]

insn_alu("mul",    "0000001", "000", "rvfi_rs1_rdata * rvfi_rs2_rdata", alt_add=0x2cdf52a55876063e, misa=MISA_M)
insn_alu("mulh",   "0000001", "001", "({{`RISCV_FORMAL_XLEN{rvfi_rs1_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs1_rdata} *\n" +
        "\t\t{{`RISCV_FORMAL_XLEN{rvfi_rs2_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_add=0x15d01651f6583fb7, misa=MISA_M)
insn_alu("mulhsu", "0000001", "010", "({{`RISCV_FORMAL_XLEN{rvfi_rs1_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs1_rdata} *\n" +
        "\t\t{`RISCV_FORMAL_XLEN'b0, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_sub=0xea3969edecfbe137, misa=MISA_M)
insn_alu("mulhu",  "0000001", "011", "({`RISCV_FORMAL_XLEN'b0, rvfi_rs1_rdata} * {`RISCV_FORMAL_XLEN'b0, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_add=0xd13db50d949ce5e8, misa=MISA_M)

insn_alu("div",    "0000001", "100", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? {`RISCV_FORMAL_XLEN{1'b1}} :
                                         rvfi_rs1_rdata == {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} && rvfi_rs2_rdata == {`RISCV_FORMAL_XLEN{1'b1}} ? {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} :
                                         $signed(rvfi_rs1_rdata) / $signed(rvfi_rs2_rdata)""", alt_sub=0x29bbf66f7f8529ec, misa=MISA_M)

insn_alu("divu",   "0000001", "101", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? {`RISCV_FORMAL_XLEN{1'b1}} :
                                         rvfi_rs1_rdata / rvfi_rs2_rdata""", alt_sub=0x8c629acb10e8fd70, misa=MISA_M)

insn_alu("rem",    "0000001", "110", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? rvfi_rs1_rdata :
                                         rvfi_rs1_rdata == {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} && rvfi_rs2_rdata == {`RISCV_FORMAL_XLEN{1'b1}} ? {`RISCV_FORMAL_XLEN{1'b0}} :
                                         $signed(rvfi_rs1_rdata) % $signed(rvfi_rs2_rdata)""", alt_sub=0xf5b7d8538da68fa5, misa=MISA_M)

insn_alu("remu",   "0000001", "111", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? rvfi_rs1_rdata :
                                         rvfi_rs1_rdata % rvfi_rs2_rdata""", alt_sub=0xbc4402413138d0e1, misa=MISA_M)

current_isa = ["rv64im"]

insn_alu("mulw",    "0000001", "000", "rvfi_rs1_rdata[31:0] * rvfi_rs2_rdata[31:0]", alt_add=0x2cdf52a55876063e, wmode=True, misa=MISA_M)

insn_alu("divw",    "0000001", "100", """rvfi_rs2_rdata[31:0] == 32'b0 ? {32{1'b1}} :
                       rvfi_rs1_rdata == {1'b1, {31{1'b0}}} && rvfi_rs2_rdata == {32{1'b1}} ? {1'b1, {31{1'b0}}} :
                       $signed(rvfi_rs1_rdata[31:0]) / $signed(rvfi_rs2_rdata[31:0])""", alt_sub=0x29bbf66f7f8529ec, wmode=True, misa=MISA_M)

insn_alu("divuw",   "0000001", "101", """rvfi_rs2_rdata[31:0] == 32'b0 ? {32{1'b1}} :
                       rvfi_rs1_rdata[31:0] / rvfi_rs2_rdata[31:0]""", alt_sub=0x8c629acb10e8fd70, wmode=True, misa=MISA_M)

insn_alu("remw",    "0000001", "110", """rvfi_rs2_rdata == 32'b0 ? rvfi_rs1_rdata :
                       rvfi_rs1_rdata == {1'b1, {31{1'b0}}} && rvfi_rs2_rdata == {32{1'b1}} ? {32{1'b0}} :
                       $signed(rvfi_rs1_rdata[31:0]) % $signed(rvfi_rs2_rdata[31:0])""", alt_sub=0xf5b7d8538da68fa5, wmode=True, misa=MISA_M)

insn_alu("remuw",   "0000001", "111", """rvfi_rs2_rdata == 32'b0 ? rvfi_rs1_rdata :
                       rvfi_rs1_rdata[31:0] % rvfi_rs2_rdata[31:0]""", alt_sub=0xbc4402413138d0e1, wmode=True, misa=MISA_M)

## Atomics ISA (A)

# current_isa = ["rv32ia"]

# FIXME: LR.W / SC.W
# insn_amo("amoswap_w", "00001", "010", "rvfi_rs2_rdata[31:0]")
# insn_amo("amoadd_w",  "00000", "010", "rvfi_mem_extamo ? rvfi_rs2_rdata[31:0] : rvfi_mem_rdata + rvfi_rs2_rdata[31:0]")
# insn_amo("amoxor_w",  "00100", "010", "rvfi_mem_extamo ? rvfi_rs2_rdata[31:0] : rvfi_mem_rdata ^ rvfi_rs2_rdata[31:0]")
# insn_amo("amoand_w",  "01100", "010", "rvfi_mem_extamo ? rvfi_rs2_rdata[31:0] : rvfi_mem_rdata & rvfi_rs2_rdata[31:0]")
# insn_amo("amoor_w",   "01000", "010", "rvfi_mem_extamo ? rvfi_rs2_rdata[31:0] : rvfi_mem_rdata | rvfi_rs2_rdata[31:0]")
# insn_amo("amomin_w",  "10000", "010", "rvfi_mem_extamo ? rvfi_rs2_rdata[31:0] : ($signed(rvfi_mem_rdata) < $signed(rvfi_rs2_rdata[31:0]) ? rvfi_mem_rdata : rvfi_rs2_rdata[31:0])")
# insn_amo("amomax_w",  "10100", "010", "rvfi_mem_extamo ? rvfi_rs2_rdata[31:0] : ($signed(rvfi_mem_rdata) > $signed(rvfi_rs2_rdata[31:0]) ? rvfi_mem_rdata : rvfi_rs2_rdata[31:0])")
# insn_amo("amominu_w", "11000", "010", "rvfi_mem_extamo ? rvfi_rs2_rdata[31:0] : (rvfi_mem_rdata < rvfi_rs2_rdata[31:0] ? rvfi_mem_rdata : rvfi_rs2_rdata[31:0])")
# insn_amo("amomaxu_w", "11100", "010", "rvfi_mem_extamo ? rvfi_rs2_rdata[31:0] : (rvfi_mem_rdata > rvfi_rs2_rdata[31:0] ? rvfi_mem_rdata : rvfi_rs2_rdata[31:0])")

# current_isa = ["rv64ia"]

# FIXME: LR.D / SC.D
# insn_amo("amoswap_d", "00001", "011", "rvfi_rs2_rdata[63:0]")
# insn_amo("amoadd_d",  "00000", "011", "rvfi_mem_extamo ? rvfi_rs2_rdata[63:0] : rvfi_mem_rdata + rvfi_rs2_rdata[63:0]")
# insn_amo("amoxor_d",  "00100", "011", "rvfi_mem_extamo ? rvfi_rs2_rdata[63:0] : rvfi_mem_rdata ^ rvfi_rs2_rdata[63:0]")
# insn_amo("amoand_d",  "01100", "011", "rvfi_mem_extamo ? rvfi_rs2_rdata[63:0] : rvfi_mem_rdata & rvfi_rs2_rdata[63:0]")
# insn_amo("amoor_d",   "01000", "011", "rvfi_mem_extamo ? rvfi_rs2_rdata[63:0] : rvfi_mem_rdata | rvfi_rs2_rdata[63:0]")
# insn_amo("amomin_d",  "10000", "011", "rvfi_mem_extamo ? rvfi_rs2_rdata[63:0] : ($signed(rvfi_mem_rdata) < $signed(rvfi_rs2_rdata[63:0]) ? rvfi_mem_rdata : rvfi_rs2_rdata[63:0])")
# insn_amo("amomax_d",  "10100", "011", "rvfi_mem_extamo ? rvfi_rs2_rdata[63:0] : ($signed(rvfi_mem_rdata) > $signed(rvfi_rs2_rdata[63:0]) ? rvfi_mem_rdata : rvfi_rs2_rdata[63:0])")
# insn_amo("amominu_d", "11000", "011", "rvfi_mem_extamo ? rvfi_rs2_rdata[63:0] : (rvfi_mem_rdata < rvfi_rs2_rdata[63:0] ? rvfi_mem_rdata : rvfi_rs2_rdata[63:0])")
# insn_amo("amomaxu_d", "11100", "011", "rvfi_mem_extamo ? rvfi_rs2_rdata[63:0] : (rvfi_mem_rdata > rvfi_rs2_rdata[63:0] ? rvfi_mem_rdata : rvfi_rs2_rdata[63:0])")

## Bit Manipulation ISA (B)

### Zba: Address generation

current_isa = ["rv32iZba"]

insn_alu("sh1add",  "0010000", "010", "rvfi_rs2_rdata + (rvfi_rs1_rdata << 1)", misa=MISA_B)
insn_alu("sh2add",  "0010000", "100", "rvfi_rs2_rdata + (rvfi_rs1_rdata << 2)", misa=MISA_B)
insn_alu("sh3add",  "0010000", "110", "rvfi_rs2_rdata + (rvfi_rs1_rdata << 3)", misa=MISA_B)

current_isa = ["rv64iZba"]

insn_alu("add_uw",      "0000100", "000", "rvfi_rs2_rdata + rvfi_rs1_rdata[31:0]",          uwmode=True, misa=MISA_B)
insn_alu("sh1add_uw",   "0010000", "010", "rvfi_rs2_rdata + (rvfi_rs1_rdata[31:0] << 1)",   uwmode=True, misa=MISA_B)
insn_alu("sh2add_uw",   "0010000", "100", "rvfi_rs2_rdata + (rvfi_rs1_rdata[31:0] << 2)",   uwmode=True, misa=MISA_B)
insn_alu("sh3add_uw",   "0010000", "110", "rvfi_rs2_rdata + (rvfi_rs1_rdata[31:0] << 3)",   uwmode=True, misa=MISA_B)
insn_shimm("slli_uw",   "000010",  "001", "rvfi_rs1_rdata[31:0] << insn_shamt",             uwmode=True, misa=MISA_B)

### Zbb: Basic bit-manipulation

current_isa = ["rv32iZbb"]

insn_count("clz",   "00000", misa=MISA_B)
insn_count("ctz",   "00001", trailing=True, misa=MISA_B)
insn_count("cpop",  "00010", pop=True, misa=MISA_B)
insn_alu("max",     "0000101", "110", "($signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)) ? rvfi_rs2_rdata : rvfi_rs1_rdata", misa=MISA_B)
insn_alu("maxu",    "0000101", "111", "(rvfi_rs1_rdata < rvfi_rs2_rdata) ? rvfi_rs2_rdata : rvfi_rs1_rdata", misa=MISA_B)
insn_alu("min",     "0000101", "100", "($signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)) ? rvfi_rs1_rdata : rvfi_rs2_rdata", misa=MISA_B)
insn_alu("minu",    "0000101", "101", "(rvfi_rs1_rdata < rvfi_rs2_rdata) ? rvfi_rs1_rdata : rvfi_rs2_rdata", misa=MISA_B)
insn_ext("sext_b",  "00100", signed=True, bmode=True, misa=MISA_B)
insn_ext("sext_h",  "00101", signed=True, misa=MISA_B)
insn_ext("zext_h",  "00000", misa=MISA_B)
insn_bytes("orc_b", "12'b 001010000111", "101", "{8{|rvfi_rs1_rdata[i*8+:8]}}", misa=MISA_B)

current_isa = ["rv32iZbb", "rv32iZbkb"]

insn_alu("andn",    "0100000", "111", "rvfi_rs1_rdata & ~rvfi_rs2_rdata",   misa=MISA_B)
insn_alu("orn",     "0100000", "110", "rvfi_rs1_rdata | ~rvfi_rs2_rdata",   misa=MISA_B)
insn_alu("xnor",    "0100000", "100", "~(rvfi_rs1_rdata ^ rvfi_rs2_rdata)", misa=MISA_B)
insn_alu("rol",     "0110000", "001", "(rvfi_rs1_rdata << shamt) | (rvfi_rs1_rdata >> (`RISCV_FORMAL_XLEN - shamt))", shamt=True, misa=MISA_B)
insn_alu("ror",     "0110000", "101", "(rvfi_rs1_rdata >> shamt) | (rvfi_rs1_rdata << (`RISCV_FORMAL_XLEN - shamt))", shamt=True, misa=MISA_B)
insn_shimm("rori",  "011000", "101", "(rvfi_rs1_rdata >> insn_shamt) | (rvfi_rs1_rdata << (`RISCV_FORMAL_XLEN - insn_shamt))", misa=MISA_B)
insn_bytes("rev8",  "{6'b 011010, `RISCV_FORMAL_XLEN == 64, 5'b 11000}", "101", "rvfi_rs1_rdata[((nbytes-i)*8)-1-:8]", misa=MISA_B)

current_isa = ["rv32iZbkb"]

insn_pack()
insn_pack("packh", "111", result_width=16)
insn_bytes("brev8", "12'b 011010000111", "101", "rvfi_rs1_rdata[(i+1)*8-(j+1)]", bitwise=True, misa=0)
insn_zip("zip",   "001")
insn_zip("unzip", "101", unzip=True)

current_isa = ["rv64iZbb"]

insn_count("clzw",  "00000", wmode=True, misa=MISA_B)
insn_count("ctzw",  "00001", trailing=True, wmode=True, misa=MISA_B)
insn_count("cpopw", "00010", pop=True, wmode=True, misa=MISA_B)

current_isa = ["rv64iZbb", "rv64iZbkb"]

insn_alu("rolw",    "0110000", "001", "(rvfi_rs1_rdata[31:0] << shamt) | (rvfi_rs1_rdata[31:0] >> (32 - shamt))", shamt=True, wmode=True, misa=MISA_B)
insn_alu("rorw",    "0110000", "101", "(rvfi_rs1_rdata[31:0] >> shamt) | (rvfi_rs1_rdata[31:0] << (32 - shamt))", shamt=True, wmode=True, misa=MISA_B)
insn_shimm("roriw", "011000", "101", "(rvfi_rs1_rdata[31:0] >> insn_shamt) | (rvfi_rs1_rdata[31:0] << (32 - insn_shamt))", wmode=True, misa=MISA_B)

current_isa = ["rv64iZbkb"]

insn_pack("packw", "100", result_width=32, signed=True)

### Zbc: Carry-less multiplication

current_isa = ["rv32iZbc", "rv32iZbkc"]
insn_clmul("clmul",  "001", "rvfi_rs1_rdata << i")
insn_clmul("clmulh", "011", "rvfi_rs1_rdata >> (`RISCV_FORMAL_XLEN - i)", index1=True)

current_isa = ["rv32iZbc"]
insn_clmul("clmulr", "010", "rvfi_rs1_rdata >> (`RISCV_FORMAL_XLEN - i - 1)")

### Zbs: Single-bit instructions

current_isa = ["rv32iZbs"]

insn_bit("bclr",    "010010", "001", "rvfi_rs1_rdata & ~(1 << index)", misa=MISA_B)
insn_bit("bclri",   "010010", "001", "rvfi_rs1_rdata & ~(1 << index)", imode=True, misa=MISA_B)
insn_bit("bext",    "010010", "101", "(rvfi_rs1_rdata >> index) & 1",  misa=MISA_B)
insn_bit("bexti",   "010010", "101", "(rvfi_rs1_rdata >> index) & 1",  imode=True, misa=MISA_B)
insn_bit("binv",    "011010", "001", "rvfi_rs1_rdata ^ (1 << index)",  misa=MISA_B)
insn_bit("binvi",   "011010", "001", "rvfi_rs1_rdata ^ (1 << index)",  imode=True, misa=MISA_B)
insn_bit("bset",    "001010", "001", "rvfi_rs1_rdata | (1 << index)",  misa=MISA_B)
insn_bit("bseti",   "001010", "001", "rvfi_rs1_rdata | (1 << index)",  imode=True, misa=MISA_B)

current_isa = ["rv32iZbkx"]

insn_xperm("xperm4", "010", 4)
insn_xperm("xperm8", "100", 8)

## Compressed Integer ISA (IC)

current_isa = ["rv32ic"]

insn_c_addi4spn()
insn_c_l("c_lw", "010", 4, True)
insn_c_s("c_sw", "110", 4)
insn_c_addi()
insn_c_jal("c_jal", "001", True)
insn_c_li()
insn_c_addi16sp()
insn_c_lui()
insn_c_sri("c_srli", "00", "rvfi_rs1_rdata >> insn_shamt")
insn_c_sri("c_srai", "01", "$signed(rvfi_rs1_rdata) >>> insn_shamt")
insn_c_andi()
insn_c_alu("c_sub", "100011", "00", "rvfi_rs1_rdata - rvfi_rs2_rdata")
insn_c_alu("c_xor", "100011", "01", "rvfi_rs1_rdata ^ rvfi_rs2_rdata")
insn_c_alu("c_or",  "100011", "10", "rvfi_rs1_rdata | rvfi_rs2_rdata")
insn_c_alu("c_and", "100011", "11", "rvfi_rs1_rdata & rvfi_rs2_rdata")
insn_c_jal("c_j", "101", False)
insn_c_b("c_beqz", "110", "rvfi_rs1_rdata == 0")
insn_c_b("c_bnez", "111", "rvfi_rs1_rdata != 0")
insn_c_sli("c_slli", "rvfi_rs1_rdata << insn_shamt")
insn_c_lsp("c_lwsp", "010", 4, True)
insn_c_jalr("c_jr", "1000", False)
insn_c_mvadd("c_mv", "1000", False)
insn_c_jalr("c_jalr", "1001", True)
insn_c_mvadd("c_add", "1001", True)
insn_c_ssp("c_swsp", "110", 4)

current_isa = ["rv64ic"]

insn_c_addi("c_addiw", wmode=True)
insn_c_alu("c_subw", "100111", "00", "rvfi_rs1_rdata[31:0] - rvfi_rs2_rdata[31:0]", wmode=True)
insn_c_alu("c_addw", "100111", "01", "rvfi_rs1_rdata[31:0] + rvfi_rs2_rdata[31:0]", wmode=True)

insn_c_l("c_ld", "011", 8, True)
insn_c_s("c_sd", "111", 8)
insn_c_lsp("c_ldsp", "011", 8, True)
insn_c_ssp("c_sdsp", "111", 8)

## ISA Propagate

def isa_propagate_pair(from_isa, to_isa):
     global isa_database
     assert from_isa in isa_database, f'{from_isa} not in {list(isa_database.keys())}'
     if to_isa not in isa_database:
         isa_database[to_isa] = set()
     isa_database[to_isa] |= isa_database[from_isa]

# RISC-V ISA extensions are more than just a single character '[a-z]':
# multi-letter extensions begin with Z X or S (technically Ss Sh Sv or Sm)
# followed by one or more letters '[ZXS][a-z]+'; any extension may also have a
# version number with the 'p' character as major/minor separator '([0-9p]+)?'.
# Case also seems to be variable, so use 're.IGNORECASE'.
rv_ext_pat = r'([ZXS][a-z]+|[a-z])([0-9p]+)?'

def isa_propagate(suffix):
    if suffix:
        isa_propagate_pair("rv32i", "rv32i"+suffix)
        isa_propagate_pair("rv64i", "rv64i"+suffix)
    for match in re.finditer(rv_ext_pat, suffix, flags=re.IGNORECASE):
        src = match.group()
        if src != suffix:
            isa_propagate_pair("rv32i"+src, "rv32i"+suffix)
            isa_propagate_pair("rv64i"+src, "rv64i"+suffix)
    isa_propagate_pair("rv32i"+suffix, "rv64i"+suffix)

isa_propagate("")
isa_propagate("c")
isa_propagate("m")
isa_propagate("mc")

## B extension is Zba, Zbb, and Zbs
for ext in ["Zba", "Zbb", "Zbs"]:
    if "rv32i"+ext not in isa_database:
        continue
    isa_propagate(ext)
    isa_propagate_pair("rv32i"+ext, "rv32ib")
    isa_propagate_pair("rv64i"+ext, "rv64ib")
isa_propagate_pair("rv32ib", "rv64ib")

## Extra B* extensions
for ext in ["Zbc", "Zbkb", "Zbkc", "Zbkx"]:
    if "rv32i"+ext not in isa_database:
        continue
    isa_propagate(ext)


## Additional ISA combinations
isa_propagate("Zba_Zbb_Zbc_Zbs")
isa_propagate("Zbkb_Zbkc_Zbkx")

## ISA Fixup

for isa, insns in isa_database.items():
    if isa.startswith("rv64"):
        insns.discard("c_jal")
        insns -= set(["zip", "unzip"])

## ISA Listings and ISA Models

for isa, insns in isa_database.items():
    with open("isa_%s.txt" % isa, "w") as f:
        for insn in sorted(insns):
            print(insn, file=f)

    with open("isa_%s.v" % isa, "w") as f:
        header(f, isa, isa_mode=True)

        for insn in sorted(insns):
            print("  wire                                spec_insn_%s_valid;"     % insn, file=f)
            print("  wire                                spec_insn_%s_trap;"      % insn, file=f)
            print("  wire [                       4 : 0] spec_insn_%s_rs1_addr;"  % insn, file=f)
            print("  wire [                       4 : 0] spec_insn_%s_rs2_addr;"  % insn, file=f)
            print("  wire [                       4 : 0] spec_insn_%s_rd_addr;"   % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_%s_rd_wdata;"  % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_%s_pc_wdata;"  % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_%s_mem_addr;"  % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_%s_mem_rmask;" % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_insn_%s_mem_wmask;" % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_%s_mem_wdata;"  % insn, file=f)
            print("`ifdef RISCV_FORMAL_CSR_MISA", file=f)
            print("  wire [`RISCV_FORMAL_XLEN   - 1 : 0] spec_insn_%s_csr_misa_rmask;" % insn, file=f)
            print("`endif", file=f)
            print("", file=f)
            print("  rvfi_insn_%s insn_%s (" % (insn, insn), file=f)
            print("    .rvfi_valid(rvfi_valid),", file=f)
            print("    .rvfi_insn(rvfi_insn),", file=f)
            print("    .rvfi_pc_rdata(rvfi_pc_rdata),", file=f)
            print("    .rvfi_rs1_rdata(rvfi_rs1_rdata),", file=f)
            print("    .rvfi_rs2_rdata(rvfi_rs2_rdata),", file=f)
            print("    .rvfi_mem_rdata(rvfi_mem_rdata),", file=f)
            print("`ifdef RISCV_FORMAL_CSR_MISA", file=f)
            print("    .rvfi_csr_misa_rdata(rvfi_csr_misa_rdata),", file=f)
            print("    .spec_csr_misa_rmask(spec_insn_%s_csr_misa_rmask)," % insn, file=f)
            print("`endif", file=f)
            print("    .spec_valid(spec_insn_%s_valid)," % insn, file=f)
            print("    .spec_trap(spec_insn_%s_trap)," % insn, file=f)
            print("    .spec_rs1_addr(spec_insn_%s_rs1_addr)," % insn, file=f)
            print("    .spec_rs2_addr(spec_insn_%s_rs2_addr)," % insn, file=f)
            print("    .spec_rd_addr(spec_insn_%s_rd_addr)," % insn, file=f)
            print("    .spec_rd_wdata(spec_insn_%s_rd_wdata)," % insn, file=f)
            print("    .spec_pc_wdata(spec_insn_%s_pc_wdata)," % insn, file=f)
            print("    .spec_mem_addr(spec_insn_%s_mem_addr)," % insn, file=f)
            print("    .spec_mem_rmask(spec_insn_%s_mem_rmask)," % insn, file=f)
            print("    .spec_mem_wmask(spec_insn_%s_mem_wmask)," % insn, file=f)
            print("    .spec_mem_wdata(spec_insn_%s_mem_wdata)" % insn, file=f)
            print("  );", file=f)
            print("", file=f)

        for port in ["valid", "trap", "rs1_addr", "rs2_addr", "rd_addr", "rd_wdata", "pc_wdata", "mem_addr", "mem_rmask", "mem_wmask", "mem_wdata"]:
            print("  assign spec_%s =\n\t\t%s : 0;" % (port, " :\n\t\t".join(["spec_insn_%s_valid ? spec_insn_%s_%s" % (insn, insn, port) for insn in sorted(insns)])), file=f)

        print("`ifdef RISCV_FORMAL_CSR_MISA", file=f)
        print("  assign spec_csr_misa_rmask =\n\t\t%s : 0;" % (" :\n\t\t".join(["spec_insn_%s_valid ? spec_insn_%s_csr_misa_rmask" % (insn, insn) for insn in sorted(insns)])), file=f)
        print("`endif", file=f)

        print("endmodule", file=f)
