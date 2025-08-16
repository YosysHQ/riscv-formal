"""insn_config_generator"""
from pathlib import Path
import click
import json

@click.command()
@click.option('-f', '--force', is_flag=True)
@click.argument('cfg', type=click.Path(exists=True, path_type=Path))
def generate(force: bool, cfg: Path):
    """Generate instruction configurations"""
    # load cfg
    with open(cfg, 'rt', encoding='utf-8') as f:
        cfg_json: dict[str] = json.load(f)

    insn_parts: list[tuple[str, int]] = cfg_json.pop('insn_parts')
    instructions: dict[str, dict[str, str]] = cfg_json.pop('instructions')
    opcode: str = cfg_json.pop('opcode')

    for key in cfg_json.keys():
        raise NotImplementedError(key)

    out_files: dict[str, Path] = {}
    # check output files
    for insn in instructions.keys():
        out_file = Path(f"insn_{insn}.json")
        if out_file.exists() and not force:
            raise FileExistsError(out_file)
        out_files[insn] = out_file

    insn_part_keys = [k for k, _ in insn_parts]

    # generate configs
    for insn, mappings in instructions.items():
        op_values = {}
        out_cfg = {
            'name': insn,
            'insn_parts': insn_parts,
            'op_values': op_values,
            'opcode': opcode,
        }

        # remap for instruction config
        for key, val in mappings.items():
            if key in insn_part_keys:
                op_values[key] = val
            else:
                out_cfg[key] = val

        # sanity check format
        insn_fmt = []
        for insn_key in insn_part_keys:
            if insn_key == "opcode":
                insn_val = opcode
            else:
                insn_val = op_values.get(insn_key, insn_key)
            insn_fmt.append(insn_val)
        click.echo(f"Found insn {insn!r}: {{{', '.join(insn_fmt)}}}")

        # write to output
        with open(out_files[insn], 'wt', encoding='utf-8') as f:
            json.dump(out_cfg, f, indent=4)

if __name__ == "__main__":
    generate()