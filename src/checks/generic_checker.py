from dataclasses import dataclass, asdict
import json
from textwrap import indent, dedent
from typing import Any, Optional

import json_fix

from ..named_set import NamedClass

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
class GenericChecker(NamedClass):
    name: str
    body: str = ""

    channel: Optional[int] = None
    channelized: bool = False

    def __post_init__(self):
        if self.channel is not None:
            self.channelized = True

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

    def _v_rvfi_channel(self) -> str:
        if self.channelized:
            return "begin:rvfi `RVFI_GETCHANNEL(channel_idx) end\n"
        else:
            return "`RVFI_CHANNEL(rvfi, `RISCV_FORMAL_CHANNEL_IDX)\n"

    def _v_format_block(self, s: str) -> str:
        return indent(s, '    ') + '\n'

    def _v_checks(self, **kwargs) -> None:
        pass

    def _v_body(self) -> str:
        # module body
        return self._v_format_block(self.body)

    def _v_channelizer(self, body: str) -> str:
        if self.channel is None:
            v_str = "    genvar channel_idx;\n"
            v_str += "    generate for (channel_idx = 0; channel_idx < `RISCV_FORMAL_NRET; channel_idx=channel_idx+1) begin:channel\n"
            v_str += self._v_format_block(body)
            v_str += "    end endgenerate\n"
        else:
            v_str = f"    localparam integer channel_idx = {self.channel};\n"
            v_str += body
        return v_str

    def to_verilog(self, **kwargs) -> str:
        self._v_checks(**kwargs)
        v_str = f"module {self._v_modname()} (\n{self._v_format_block(self._v_io())});\n\n"
        body = self._v_body(**kwargs)
        if self.channelized:
            v_str += self._v_channelizer(body)
        else:
            v_str += body
        v_str += "endmodule"
        return v_str
