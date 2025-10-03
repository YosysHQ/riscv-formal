from dataclasses import dataclass
from textwrap import dedent

from . import GenericGroupChecker
from ..csrs import Csr
from ..named_set import NamedSet

@dataclass
class CsrIllChecker(GenericGroupChecker):
    csrs: NamedSet[Csr]

    def _v_insn_check(self) -> str:
        v_str = dedent("""\
            // insn mapping
            wire csr_insn_valid = rvfi.valid && (rvfi.insn[6:0] == 7'b 1110011) && (rvfi.insn[13:12] != 0) && ((rvfi.insn >> 16 >> 16) == 0);
            wire [11:0] csr_insn_addr = rvfi.insn[31:20];

            wire csr_write = !rvfi.insn[13] || rvfi.insn[19:15];
            wire csr_read = rvfi.insn[11:7] != 0;
            """)
        return v_str

    def _v_csr_addr_check(self) -> str:
        v_str = dedent("""\
            // legal CSRs
            wire legal_addr = (""")
        legal_addrs: list[str] = []
        for csr in self.csrs:
            legal_addrs.append(f"({csr._v_insn_csr_idx(False)} /* {csr.name} */)")
            if csr.indexh:
                legal_addrs.append(f"({csr._v_insn_csr_idx(True)} /* {csr.name}h */ && rvfi.ixl == 1)")
        v_str += "\n    || ".join(legal_addrs)
        v_str += dedent("""\
            );

            always @* begin
                if (!reset && check) begin
                    assume(csr_insn_valid);
                    if (!legal_addr && (csr_write || csr_read)) assert(rvfi.trap);
                end
            end
            """)

        return v_str

    def _v_body(self) -> str:
        v_str = self._v_format_block(self._v_rvfi_channel())
        v_str += self._v_format_block(self._v_insn_check())
        v_str += self._v_format_block(self._v_csr_addr_check())
        return v_str

    def _subchecks(self) -> NamedSet[Csr]:
        return NamedSet()
