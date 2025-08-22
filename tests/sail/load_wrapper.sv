module rvfi_insn_load (
input                                 rvfi_valid,
input  [`RISCV_FORMAL_ILEN   - 1 : 0] rvfi_insn,
input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_pc_rdata,
input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_rs1_rdata,
input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_rs2_rdata,
input  [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_mem_rdata,

output                                spec_valid,
output                                spec_trap,
output [                       4 : 0] spec_rs1_addr,
output [                       4 : 0] spec_rs2_addr,
output [                       4 : 0] spec_rd_addr,
output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_rd_wdata,
output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_pc_wdata,
output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_mem_addr,
output [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_mem_rmask,
output [`RISCV_FORMAL_XLEN/8 - 1 : 0] spec_mem_wmask,
output [`RISCV_FORMAL_XLEN   - 1 : 0] spec_mem_wdata
);

    // instruction format
    wire [11:0] insn_imm    = rvfi_insn[31:20];
    wire [ 4:0] insn_rs1    = rvfi_insn[19:15];
    wire [ 0:0] insn_is_unsigned = rvfi_insn[14:14];
    wire [ 1:0] insn_width  = rvfi_insn[13:12];
    wire [ 4:0] insn_rd     = rvfi_insn[11: 7];
    wire [ 6:0] insn_opcode = rvfi_insn[ 6: 0];

    // register wrapping
    logic [31:0] x_in[31:1];
    logic [31:0] x_out[31:1];
    localparam rs1_0 = 5'd1, rd_0 = 5'd2;
    assign x_in[rs1_0] = rvfi_rs1_rdata;
    wire [31:0] result = x_out[rd_0];

    // extra signals
    t_ExecutionResult sail_return_2;
    bit sail_have_exception_2;
    t_exception sail_current_exception_2;

    // insn check
    logic [63:0] width_0;
    bit is_unsigned_0;
    reg illinsn;
    always @* begin
        illinsn <= 0;
        case ({insn_width, insn_is_unsigned})
            3'b 000: {width_0, is_unsigned_0} <= {1, 0};
            3'b 001: {width_0, is_unsigned_0} <= {1, 1};
            3'b 010: {width_0, is_unsigned_0} <= {2, 0};
            3'b 011: {width_0, is_unsigned_0} <= {2, 1};
            3'b 100: {width_0, is_unsigned_0} <= {4, 0};
            3'b 101: {width_0, is_unsigned_0} <= {4, 1};
            3'b 110: {width_0, is_unsigned_0} <= {8, 0};
            3'b 111: {width_0, is_unsigned_0} <= {8, 1};
            default: illinsn <= 1;
        endcase
    end

    // is_unsigned instance
    execute_LOAD wrapped_checker(insn_imm, rs1_0, rd_0, is_unsigned_0, width_0, x_in[1], x_in[2], x_in[3], x_in[4], x_in[5], x_in[6], x_in[7], x_in[8], x_in[9], x_in[10], x_in[11], x_in[12], x_in[13], x_in[14], x_in[15], x_in[16], x_in[17], x_in[18], x_in[19], x_in[20], x_in[21], x_in[22], x_in[23], x_in[24], x_in[25], x_in[26], x_in[27], x_in[28], x_in[29], x_in[30], x_in[31], sail_return_2, x_out[1], x_out[2], x_out[3], x_out[4], x_out[5], x_out[6], x_out[7], x_out[8], x_out[9], x_out[10], x_out[11], x_out[12], x_out[13], x_out[14], x_out[15], x_out[16], x_out[17], x_out[18], x_out[19], x_out[20], x_out[21], x_out[22], x_out[23], x_out[24], x_out[25], x_out[26], x_out[27], x_out[28], x_out[29], x_out[30], x_out[31], sail_have_exception_2, sail_current_exception_2);

    // spec mapping
    assign spec_rs1_addr = insn_rs1;
    assign spec_rd_addr = insn_rd;
    assign spec_rd_wdata = spec_rd_addr ? result : 0;
    assign spec_valid = rvfi_valid && !illinsn && insn_opcode == 7'b 0000011;
    assign spec_rs2_addr = 0;
    assign spec_pc_wdata = rvfi_pc_rdata + 4;
    assign spec_trap = 0;
    assign spec_mem_addr = 0;
    assign spec_mem_rmask = 0;
    assign spec_mem_wmask = 0;
    assign spec_mem_wdata = 0;

endmodule
