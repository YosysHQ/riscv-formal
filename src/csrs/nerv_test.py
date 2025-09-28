import click

from .csr import MachineCsr, Csr
from .behavior import (
    AnyValue,
    ConstValue,
    ZeroValue,
    UpcntValue,
    IncValue,
)

def custom_csr(rvfi: bool):
    return Csr(
        name = "custom",
        width = "xlen",
        privilege = "URW",
        index = 0xBC0,
        has_rvfi = rvfi,
        read_insn = True,
        behavior = AnyValue(),
    )

def custom_ro_csr(rvfi: bool):
    return Csr(
        name = "custom_ro",
        width = "xlen",
        privilege = "MRO",
        index = 0xFC0,
        has_rvfi = rvfi,
        read_insn = True,
        behavior = ConstValue(),
    )

def mcycle_csr(rvfi: bool):
    return MachineCsr(
        name = "mcycle",
        width = "64",
        privilege = "MRW",
        index = 0xB00,
        indexh = 0xB80,
        has_rvfi = rvfi,
        read_insn = True,
        behavior = UpcntValue(),
    )

def mhpmcounter5_csr(rvfi: bool, rw_test: bool):
    return MachineCsr(
        name = "mhpmcounter5",
        width = "xlen",
        privilege = "MRW",
        index = 0xB05,
        has_rvfi = rvfi,
        read_insn = True,
        rw_test = rw_test,
        behavior = IncValue(),
    )

@click.option('-r', '--rvfi', is_flag=True)
@click.option('-w', '--rw_test', is_flag=True)
@click.command
def nerv_test(rvfi: bool, rw_test: bool):
    # csr = custom_csr(rvfi)
    # csr = mcycle_csr(rvfi)
    csr = mhpmcounter5_csr(rvfi, rw_test)
    # csr = custom_ro_csr(rvfi)
    print(csr.to_verilog(xlen=32))

if __name__ == "__main__":
    nerv_test()
