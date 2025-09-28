import json
import click

from . import CsrIllChecker
from ..csrs import Csr, base_csrs, hpm_csrs
from ..named_set import NamedSet

def dump_csr_ill(name: str, csrs: NamedSet[Csr], xlen: int, format: str) -> str:
    csr_checker = CsrIllChecker(
        name = name,
        csrs = csrs,
    )

    if format == "json":
        return json.dumps(csr_checker)
    elif format == "verilog":
        return csr_checker.to_verilog(xlen=xlen)

@click.option('-x', '--xlen', type=int, default=32)
@click.option('--format', type=click.Choice(['json', 'verilog']), default='json')
@click.command()
def base_csr(xlen: int, format: str):
    nerv_csrs = base_csrs()
    nerv_csrs.update(hpm_csrs())
    csrs: NamedSet[Csr] = NamedSet()
    for csr in nerv_csrs:
        csrs.add(csr)

    # custom NERV CSRs
    csrs.add(Csr(
        name = "custom",
        width = "xlen",
        privilege = "URW",
        index = 0xBC0,
    ))
    csrs.add(Csr(
        name = "custom_ro",
        width = "xlen",
        privilege = "MRO",
        index = 0xFC0,
    ))

    click.echo(dump_csr_ill("csr_ill_check", csrs, xlen, format))

if __name__ == "__main__":
    base_csr()
