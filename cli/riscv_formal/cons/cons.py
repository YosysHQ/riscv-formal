from dataclasses import dataclass

from riscv_formal.generic_checker import GenericChecker

@dataclass(kw_only=True)
class Cons(GenericChecker):
    has_start: bool = False
    has_trig: bool = False
