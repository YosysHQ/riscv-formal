from dataclasses import dataclass, asdict
import json
from textwrap import indent, dedent
from typing import Any

import json_fix

def skip_empty_factory(mapping: list[tuple[str, Any]]) -> dict:
    """dictionary factory which skips empty values"""
    result = {}
    for key, val in mapping:
        if isinstance(val, bool):
            result[key] = val
        elif val:
            # skip falsy non-boolean values
            result[key] = val
    return result

@dataclass(kw_only=True)
class GenericChecker:
    name: str
    body: str = ""

    @classmethod
    def from_json(cls, s: str):
        mapping = json.loads(s)
        return cls(**mapping)

    def __json__(self, skip_empty: bool = True) -> dict:
        if skip_empty:
            return asdict(self, dict_factory=skip_empty_factory)
        else:
            return asdict(self)

    def to_json(self, skip_empty: bool = True, indent: int | str | None = None) -> str:
        return json.dumps(self.__json__(skip_empty), indent=indent)

    def _v_modname(self) -> str:
        # module name
        return f"rvfi_{self.name}"

    def _v_io(self) -> str:
        # macro defined RVFI inputs
        return dedent("""\
            input clock, reset, check,
            `RVFI_INPUTS
            `RVFI_BUS_INPUTS""")

    def _v_format_block(self, s: str) -> str:
        return indent(s, '    ') + '\n'

    def _v_checks(self, **kwargs) -> None:
        pass

    def _v_body(self) -> str:
        # module body
        return self._v_format_block(self.body)

    def to_verilog(self, **kwargs) -> str:
        self._v_checks(**kwargs)
        v_str = f"module {self._v_modname()} (\n{self._v_format_block(self._v_io())});\n\n"
        v_str += self._v_body(**kwargs)
        v_str += "endmodule"
        return v_str
