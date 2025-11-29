from dataclasses import dataclass

from riscv_formal.generic_checker import GenericChecker

@dataclass(kw_only=True)
class Cons(GenericChecker):
    has_start: bool = False
    has_trig: bool = False

    def __post_init__(self):
        super().__post_init__()
        if self.has_trig and not self.has_start:
            raise NotImplementedError("has_trig only valid if has_start")
