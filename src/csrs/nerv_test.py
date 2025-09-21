import click

from .model import Csr

def custom_csr():
    return Csr(
        name = "custom",
        width = "xlen",
        privilege = "URW",
        index = 0xBC0,
        has_rvfi = True,
    )

@click.command
def nerv_test():
    csr = custom_csr()
    print(csr.to_verilog(xlen=32))

if __name__ == "__main__":
    nerv_test()
