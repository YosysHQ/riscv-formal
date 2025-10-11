from .model import (
    Instruction,
    MemoryInstruction,
    AltopsInstruction,
)

from .wrapped_model import WrappedInstruction

from .isa import Isa

from .ext_mapper import (
    register_ext_composition,
    register_ext_generator,
    map_ext,
)

from .builtins import builtins
from .bext import bext
from .cext import cext
from .mext import mext
