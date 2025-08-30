"""insn_wrapper"""

from pathlib import Path
import click

from .model import Instruction

@click.command()
@click.option('-f', '--force', is_flag=True)
@click.option('-i', '--ilen', type=int, default=32)
@click.option('-x', '--xlen', type=int, default=32)
@click.argument('cfg', type=click.Path(exists=True, path_type=Path))
@click.argument('out_file', type=click.Path(path_type=Path))
def wrap(force: bool, ilen: int, xlen: int, cfg: Path, out_file: Path = None):
    """main function"""
    # load cfg
    click.echo(f"Loading from {cfg}")
    with open(cfg, 'r', encoding='utf-8') as f:
        insn = Instruction.from_json(f.read())

    # get output file
    if out_file is None:
        out_file = Path(f"{insn.name}_wrapper.sv")
    if out_file.exists() and not force:
        raise FileExistsError(out_file)

    v_str = insn.to_verilog(xlen, ilen)

    # write out to file
    with open(out_file, 'wt', encoding='utf-8') as f:
        click.echo(v_str, f)

if __name__ == '__main__':
    wrap()
