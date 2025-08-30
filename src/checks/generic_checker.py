from dataclasses import dataclass
from textwrap import indent, dedent

@dataclass(kw_only=True)
class GenericChecker:
    name: str
    body: str = ""

    def _v_modname(self) -> str:
        # module name
        return f"rvfi_insn_{self.name}"

    def _v_io(self) -> str:
        # macro defined RVFI inputs
        return dedent("""\
            input clock, reset, check,
            `RVFI_INPUTS
            `RVFI_BUS_INPUTS""")

    def _v_format_block(self, s: str) -> str:
        return indent(s, '    ') + '\n'

    def _v_body(self) -> str:
        # module body
        return self._v_format_block(self.body)

    def to_verilog(self, **kwargs) -> str:
        v_str = f"module {self._v_modname()} (\n{self._v_format_block(self._v_io())});\n\n"
        v_str += self._v_body(**kwargs)
        v_str += "endmodule"
        return v_str
