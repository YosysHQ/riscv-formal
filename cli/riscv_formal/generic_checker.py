from dataclasses import dataclass
from textwrap import indent, dedent
from typing import Optional, TypeVar, Generic

from riscv_formal.named_set import NamedClass, NamedSet

@dataclass(kw_only=True)
class GenericChecker(NamedClass):
    name: str
    body: str = ""

    channel: Optional[int] = None
    channelized: bool = False

    def __post_init__(self):
        if self.channel is not None:
            self.channelized = True

    def _v_modname(self) -> str:
        # module name
        return f"rvfi_{self.name}"

    def _v_io(self) -> str:
        # macro defined RVFI inputs
        return dedent("""\
            input clock, reset, check,
            `RVFI_INPUTS""")

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

CT = TypeVar("CT", bound=GenericChecker)

@dataclass
class GenericGroupChecker(GenericChecker, Generic[CT]):

    def _subchecks(self) -> NamedSet[CT]:
        raise NotImplementedError()

    def to_verilog(self, **kwargs):
        v_str = ""
        for check in self._subchecks():
            v_str += check.to_verilog(**kwargs) + '\n\n'
        return v_str + super().to_verilog()
