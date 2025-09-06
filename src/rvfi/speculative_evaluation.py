from dataclasses import dataclass, field

@dataclass
class SpeculativeEvaluation:
    evaluation: str
    speculates_about: list[str] = field(default_factory=list)
    ignore_trap: bool = False
