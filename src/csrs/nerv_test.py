import click

from .model import Csr

def custom_csr(rvfi: bool):
    return Csr(
        name = "custom",
        width = "xlen",
        privilege = "URW",
        index = 0xBC0,
        has_rvfi = rvfi,
        read_insn = True,
    )

@click.option('-r', '--rvfi', is_flag=True)
@click.command
def nerv_test(rvfi: bool):
    csr = custom_csr(rvfi)
    print(csr.to_verilog(xlen=32))

if __name__ == "__main__":
    nerv_test()
