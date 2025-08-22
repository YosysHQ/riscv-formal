"""insn_config_generator"""
from pathlib import Path
import string
import click
import json

VALID_XLEN = [32, 64, 128]

@click.command()
@click.option('-f', '--force', is_flag=True)
@click.argument('cfg', type=click.Path(exists=True, path_type=Path))
def generate(force: bool, cfg: Path):
    """Generate instruction configurations"""
    # load cfg
    with open(cfg, 'rt', encoding='utf-8') as f:
        cfg_json: dict[str] = json.load(f)

    insn_parts: list[tuple[str, int]] = cfg_json.pop('insn_parts')
    extension: str = cfg_json.pop('extension', "I")
    xlen_min: int = cfg_json.pop('xlen_min', 32)
    xlen_max: int = cfg_json.pop('xlen_max', 128)
    xlen: int = cfg_json.pop('xlen', None)
    raw_code: list[str] = cfg_json.pop('raw_code', [])
    spec_map: dict[str, str] = cfg_json.pop('spec_map', {})
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
            'xlen_min': xlen_min,
            'xlen_max': xlen_max,
            'xlen': xlen,
            'op_values': op_values,
            'opcode': opcode,
            'extension': extension,
        }

        # substitute instruction specific raw code
        replacement_vars: list[str] = []
        if raw_code:
            out_cfg['raw_code'] = []
            for raw_line in raw_code:
                out_cfg['raw_code'].append(raw_line.format_map(mappings))
                replacement_vars.extend([fn for _, fn, _, _ in string.Formatter().parse(raw_line) if fn is not None])

        # speculative value map
        if spec_map: out_cfg['spec_map'] = spec_map

        # remap for instruction config
        for key, val in mappings.items():
            if key in insn_part_keys:
                # instruction parts go into op_values for checking instruction validity
                op_values[key] = val
            elif key in replacement_vars:
                # ignore raw code replacement variables
                pass
            else:
                # include the rest verbatim
                out_cfg[key] = val

        # check xlen value(s)
        if out_cfg['xlen'] is not None:
            out_cfg['xlen_min'] = out_cfg['xlen']
            out_cfg['xlen_max'] = out_cfg['xlen']

        for txlen in [out_cfg['xlen_min'], out_cfg['xlen_max']]:
            if txlen not in VALID_XLEN:
                raise NotImplementedError(f"xlen={txlen} not supported for {insn}")

        supported_xlens = []
        for txlen in VALID_XLEN:
            if txlen >= out_cfg['xlen_min'] and txlen <= out_cfg['xlen_max']:
                supported_xlens.append(txlen)

        if len(supported_xlens) == 0:
            raise NotImplementedError(f"Unsupported xlen range [{xlen_min}, {xlen_max}] for {insn}")

        if out_cfg['xlen']:
            del out_cfg['xlen_min']
            del out_cfg['xlen_max']
        else:
            del out_cfg['xlen']

        # sanity check format
        insn_fmt = []
        for insn_key in insn_part_keys:
            if insn_key == "opcode":
                insn_val = opcode
            else:
                insn_val = op_values.get(insn_key, insn_key)
            insn_fmt.append(insn_val)

        if len(supported_xlens) == 1:
            xlen_str = supported_xlens[0]
        else:
            xlen_str = '{' + ','.join(str(x) for x in supported_xlens) + '}'

        ext_str = out_cfg['extension']

        click.echo(f"Found insn {insn!r:>9}: {{{', '.join(insn_fmt)}}} for RV{xlen_str}{ext_str}")

        # write to output
        with open(out_files[insn], 'wt', encoding='utf-8') as f:
            json.dump(out_cfg, f, indent=4)

if __name__ == "__main__":
    generate()