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

from .csr import hpm_csr
def mhpmevent5_csr(rvfi: bool, rw_test: bool):
    hpm5 = hpm_csr(
        "mhpmevent5", "xlen", "MRW", 0x325,
        "mhpmcounter5", "64", "MRW", 0xB05, 0xB85,
        "hpmcounter5",        "URO", 0xC05, 0xC85,
    )
    for csr in hpm5:
        csr.has_rvfi = rvfi
        csr.rw_test = rw_test
    mhpmevent5, _, _ = hpm5
    mhpmevent5.event_counter_map["csr_hpmevent_shadow == 1"] = "assert(hpmcounter_rdata > csr_hpmcounter_shadow);"
    mhpmevent5.event_counter_map["csr_hpmevent_shadow == 2"] = "assert(hpmcounter_rdata > csr_hpmcounter_shadow);"
    mhpmevent5.event_counter_map["csr_hpmevent_shadow == 3"] = "cover(hpmcounter_rdata > csr_hpmcounter_shadow);"
    return mhpmevent5

@click.option('-r', '--rvfi', is_flag=True)
@click.option('-w', '--rw_test', is_flag=True)
@click.command
def nerv_test(rvfi: bool, rw_test: bool):
    # csr = custom_csr(rvfi)
    # csr = mcycle_csr(rvfi)
    # csr = mhpmcounter5_csr(rvfi, rw_test)
    csr = mhpmevent5_csr(rvfi, rw_test)
    # csr = custom_ro_csr(rvfi)
    print(csr.to_verilog(xlen=32))

if __name__ == "__main__":
    nerv_test()
