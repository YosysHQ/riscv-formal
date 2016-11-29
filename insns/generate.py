#!/usr/bin/env python3

def header(f):
    print("// DO NOT EDIT -- auto-generated from generate.py", file=f)
    print("", file=f)

def format_r(f):
    print("// R-type instruction format", file=f)
    print("wire [6:0] insn_funct7 = insn[31:25];", file=f)
    print("wire [4:0] insn_rs2 = insn[24:20];", file=f)
    print("wire [4:0] insn_rs1 = insn[19:15];", file=f)
    print("wire [4:0] insn_funct3 = insn[14:12];", file=f)
    print("wire [4:0] insn_rd = insn[11:7];", file=f)
    print("wire [6:0] insn_opcode = insn[6:0];", file=f)
    print("", file=f)

def format_i(f):
    print("// I-type instruction format", file=f)
    print("wire [XLEN-1:0] insn_imm = $signed(insn[31:20]);", file=f)
    print("wire [4:0] insn_rs1 = insn[19:15];", file=f)
    print("wire [4:0] insn_funct3 = insn[14:12];", file=f)
    print("wire [4:0] insn_rd = insn[11:7];", file=f)
    print("wire [6:0] insn_opcode = insn[6:0];", file=f)
    print("", file=f)

def format_i_shift(f):
    print("// I-type instruction format (shift variation)", file=f)
    print("wire [6:0] insn_funct7 = insn[31:25];", file=f)
    print("wire [4:0] insn_shamt = insn[24:20];", file=f)
    print("wire [4:0] insn_rs1 = insn[19:15];", file=f)
    print("wire [4:0] insn_funct3 = insn[14:12];", file=f)
    print("wire [4:0] insn_rd = insn[11:7];", file=f)
    print("wire [6:0] insn_opcode = insn[6:0];", file=f)
    print("", file=f)

def insn_imm(insn, funct3, expr):
	with open("%s.vh" % insn, "w") as f:
		header(f)
		format_i(f)
		print("// %s instruction" % insn.upper(), file=f)
		print("wire [XLEN-1:0] result = %s;" % expr, file=f)
		print("always @(posedge clk) begin", file=f)
		print("  if (valid && insn_funct3 == 3'b %s && insn_opcode == 7'b 0010011) begin" % funct3, file=f)
		print("    assert(rs1 == insn_rs1);", file=f)
		print("    assert(rd == insn_rd);", file=f)
		print("    assert(post_pc == pre_pc + 4);", file=f)
		print("    assert(post_rd == (rd ? result : 0));", file=f)
		print("  end", file=f)
		print("end", file=f)

def insn_shimm(insn, funct7, funct3, expr):
	with open("%s.vh" % insn, "w") as f:
		header(f)
		format_i_shift(f)
		print("// %s instruction" % insn.upper(), file=f)
		print("wire [XLEN-1:0] result = %s;" % expr, file=f)
		print("always @(posedge clk) begin", file=f)
		print("  if (valid && insn_funct7 == 7'b %s && insn_funct3 == 3'b %s && insn_opcode == 7'b 0010011) begin" % (funct7, funct3), file=f)
		print("    assert(rs1 == insn_rs1);", file=f)
		print("    assert(rd == insn_rd);", file=f)
		print("    assert(post_pc == pre_pc + 4);", file=f)
		print("    assert(post_rd == (rd ? result : 0));", file=f)
		print("  end", file=f)
		print("end", file=f)

def insn_alu(insn, funct7, funct3, expr):
	with open("%s.vh" % insn, "w") as f:
		header(f)
		format_r(f)
		print("// %s instruction" % insn.upper(), file=f)
		print("wire [XLEN-1:0] result = %s;" % expr, file=f)
		print("always @(posedge clk) begin", file=f)
		print("  if (valid && insn_funct7 == 7'b %s && insn_funct3 == 3'b %s && insn_opcode == 7'b 0110011) begin" % (funct7, funct3), file=f)
		print("    assert(rs1 == insn_rs1);", file=f)
		print("    assert(rs2 == insn_rs2);", file=f)
		print("    assert(rd == insn_rd);", file=f)
		print("    assert(post_pc == pre_pc + 4);", file=f)
		print("    assert(post_rd == (rd ? result : 0));", file=f)
		print("  end", file=f)
		print("end", file=f)

insn_imm("addi",  "000", "pre_rs1 + insn_imm")
insn_imm("slti",  "010", "$signed(pre_rs1) < $signed(insn_imm)")
insn_imm("sltiu", "011", "pre_rs1 < insn_imm")
insn_imm("xori",  "100", "pre_rs1 ^ insn_imm")
insn_imm("ori",   "110", "pre_rs1 | insn_imm")
insn_imm("andi",  "111", "pre_rs1 & insn_imm")

insn_shimm("slli", "0000000", "001", "pre_rs1 << insn_shamt")
insn_shimm("srli", "0000000", "101", "pre_rs1 >> insn_shamt")
insn_shimm("srai", "0100000", "101", "$signed(pre_rs1) >>> insn_shamt")

insn_alu("add",  "0000000", "000", "pre_rs1 + pre_rs2")
insn_alu("sub",  "0100000", "000", "pre_rs1 - pre_rs2")
insn_alu("sll",  "0000000", "001", "pre_rs1 << pre_rs2[4:0]")
insn_alu("slt",  "0000000", "010", "$signed(pre_rs1) < $signed(pre_rs2)")
insn_alu("sltu", "0000000", "011", "pre_rs1 < pre_rs2")
insn_alu("xor",  "0000000", "100", "pre_rs1 ^ pre_rs2")
insn_alu("srl",  "0000000", "101", "pre_rs1 >> pre_rs2[4:0]")
insn_alu("sra",  "0100000", "101", "$signed(pre_rs1) >>> pre_rs2[4:0]")
insn_alu("or",   "0000000", "110", "pre_rs1 | pre_rs2")
insn_alu("and",  "0000000", "111", "pre_rs1 & pre_rs2")
