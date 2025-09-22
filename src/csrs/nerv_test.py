import click

from .csr import MachineCsr, Csr
from .behavior import AnyValue, UpcntValue

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

@click.option('-r', '--rvfi', is_flag=True)
@click.command
def nerv_test(rvfi: bool):
    csr = mcycle_csr(rvfi)
    print(csr.to_verilog(xlen=32))

if __name__ == "__main__":
    nerv_test()
