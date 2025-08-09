"""sv_rewriter"""
import os
from pathlib import Path
import re
import shutil
import click

@click.command()
@click.option('-f', '--force', is_flag=True)
@click.argument('file', type=click.Path(exists=True, path_type=Path))
def rewrite(force: bool, file: Path = None):
    """main function"""
    if file.suffix == ".sv":
        file_old = file.with_suffix('.sv.old')
        click.echo(f'Moving {file} to {file_old}')
        shutil.move(file, file_old)
    if file.suffix == ".old":
        file_old = file
        file = file.with_suffix("")

    click.echo(f'Writing to {file}')
    with open(file_old, 'rt', encoding='utf-8') as in_f:
        with open(file, 'wt', encoding='utf-8') as out_f:
            skip_module = False
            let_vars: set[str] = set()
            for line in in_f:
                # catch localparam definitions
                m = re.fullmatch(r'(\s*)(logic \[[0-9:]+\]|bit|t_\w+) (\S+);\n', line)
                if m:
                    space, _, let_var = m.groups()
                    let_vars.add(let_var)
                    if len(space) == 0:
                        skip_module = True

                m = re.fullmatch(r'module sail_setup_let_\d+;\n', line)
                if m:
                    skip_module = True

                # get localparam value
                m = re.fullmatch(r'\s+(\S+) = (\S+);\n', line)
                if m and skip_module:
                    let_var, let_val = m.groups()
                    if let_var.endswith("_1"): let_var = let_var[:-2]
                    try:
                        let_vars.remove(let_var)
                    except KeyError:
                        pass
                    else:
                        click.echo(f'localparam {let_var} = {let_val};', out_f)

                # skip setup module
                if skip_module:
                    if 'endmodule' in line:
                        skip_module = False
                    continue
                m = re.match(r'\s+()sail_setup_let_\d+ sail_inst_let_\d+', line)
                if m:
                    continue

                # echo line
                click.echo(line, out_f, nl=False)

                # inject BUF_MAX
                m = re.match(r'localparam SAIL_BITS_WIDTH = (\d+);', line)
                if m:
                    click.echo('localparam SAIL_BUF_MAX = (SAIL_BITS_WIDTH+1)>>3;', out_f)
    if force:
        click.echo(f'Removing {file_old}')
        os.remove(file_old)

if __name__ == '__main__':
    rewrite()
