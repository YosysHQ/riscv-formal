from dataclasses import dataclass
from textwrap import dedent

from . import GenericGroupChecker
from ..csrs import Csr
from ..named_set import NamedSet

@dataclass
class CsrChecker(GenericGroupChecker):
    csrs: NamedSet[Csr]

    def _subchecks(self) -> NamedSet[Csr]:
        return self.csrs
