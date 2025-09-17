from .observer import Observer, SpeculativeObserver, ZeroedObserver

def base_observers() -> dict[str, Observer]:
    return {o.name: o for o in [
        SpeculativeObserver("valid", "1"),
                   Observer("order", "64"),
                   Observer("insn", "`RISCV_FORMAL_ILEN"),
        SpeculativeObserver("trap", "1"),
                   Observer("halt", "1"),
                   Observer("intr", "1"),
                   Observer("mode", "2"),
                   Observer("ixl", "2"),
        SpeculativeObserver("rs1_addr", "5", "rvfi.rs1_addr"),
        SpeculativeObserver("rs2_addr", "5", "rvfi.rs2_addr"),
             ZeroedObserver("rs1_rdata", "`RISCV_FORMAL_XLEN", "spec_rs1_addr == 0"),
             ZeroedObserver("rs2_rdata", "`RISCV_FORMAL_XLEN", "spec_rs2_addr == 0"),
        SpeculativeObserver("rd_addr", "5"),
        SpeculativeObserver("rd_wdata", "`RISCV_FORMAL_XLEN"),
                   Observer("pc_rdata", "`RISCV_FORMAL_XLEN"),
        SpeculativeObserver("pc_wdata", "`RISCV_FORMAL_XLEN", "rvfi.pc_rdata + 4"),
        SpeculativeObserver("mem_addr", "`RISCV_FORMAL_XLEN"),
        SpeculativeObserver("mem_rmask", "`RISCV_FORMAL_XLEN/8"),
        SpeculativeObserver("mem_wmask", "`RISCV_FORMAL_XLEN/8"),
                   Observer("mem_rdata", "`RISCV_FORMAL_XLEN"),
        SpeculativeObserver("mem_wdata", "`RISCV_FORMAL_XLEN"),
    ]}
