import json
from pathlib import Path
import click

from .builtins import builtins

@click.command()
@click.option('-c', '--with_C', is_flag=True)
@click.option('-x', '--xlen', type=int, default=32)
@click.option('--format', type=click.Choice(['json', 'verilog', 'isa', 'auto']), default='auto')
@click.argument('out_file', type=click.Path(path_type=Path))
@click.argument('insn', type=str, default = "")
def generate(with_c: bool, xlen: int, format: str, out_file: Path, insn: str):
    insns = builtins()
    if with_c:
        from .cext import cext
        insns.update(cext())

    extensions = set()
    for instr in insns:
        extensions.update(instr.extension.split(" "))

    if insn and insn not in insns:
        raise NotImplementedError(f"{insn} instruction")

    if insn:
        if format == "auto":
            if out_file.suffix == ".json":
                format = "json"
            elif out_file.suffix in [".v", ".sv"]:
                format = "verilog"
        
        instruction = insns[insn]
        if format == "json":
            data = instruction.to_json(skip_empty=True, indent=2)
        elif format == "verilog":
            data = instruction.to_verilog(xlen)
        else:
            raise NotImplementedError(f"{out_file.suffix!r} not supported")
    else:
        if format in ["json", "auto"]:
            data = json.dumps(insns)
        elif format == "isa":
            data = json.dumps(extensions)
        else:
            raise NotImplementedError(f"{format!r} not supported")
    with open(out_file, 'wt', encoding='utf-8') as f:
        click.echo(data, f)


if __name__ == "__main__":
    generate()
