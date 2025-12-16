from dataclasses import dataclass
from textwrap import indent, dedent
from typing import Optional, TypeVar, Generic, ClassVar, Iterable

from riscv_formal.named_set import NamedClass, NamedSet


class MissingVerilogArgError(Exception):
    cls: type
    missing_arg: str

    def __init__(self, cls: type, missing_arg: str, *args: object) -> None:
        super().__init__(*args)
        self.cls = cls
        self.missing_arg = missing_arg

    def __str__(self) -> str:
        return f"{self.cls.__name__}.to_verilog() called without setting required argument {self.missing_arg!r}"


@dataclass(kw_only=True)
class GenericChecker(NamedClass):
    """Generic checker base class.

    Accepts keyword args only so that subclasses can provide additional required
    args that get picked up correctly by a type checker.  ``name`` is required,
    others are optional.

    Currently ``GenericChecker.xlen`` must be set to the integer value of XLEN
    checks are generated for (typically one of 32, 64, or 128).  Generating
    Verilog without setting this value is an error.  Subclasses may provide
    additional required arguments in the class declaration, e.g. ``class
    MyChecker(GenericChecker, required_v_args=["my_field"])``.

    :param name: Name of the check; appended to ``rvfi_`` as the module name for
        generated Verilog by default
    :param body: SystemVerilog code providing the body of the check; typically
        overridden by subclasses to generate from class-specific fields
    :param can_channelize: If the current check is able to be channelized; it is
        an error to set ``channelized`` if unset
    :param channelized: If the channelizing should be handled by this class
        (i.e. at generation time) or by macro expansion of
        ``RISCV_FORMAL_CHANNEL_IDX`` (i.e. at test run time); setting
        ``channel`` will automatically set this to ``True``
    :param channel: If set, the currently selected channel; if unset and
        ``channelized=True`` then the check body will be generated for each
        channel
    """
    #TODO formalize compile-time vs run-time terms/definitions
    name: str
    body: str = ""

    can_channelize: bool = True
    channel: Optional[int] = None
    channelized: bool = False

    _required_v_args: ClassVar[set[str]] = set(("xlen",))
    xlen: ClassVar[int]

    @classmethod
    def __init_subclass__(cls, required_v_args: Iterable[str] = [], **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        cls._required_v_args = cls._required_v_args.union(required_v_args)

    @classmethod
    def check_v_args(cls) -> None:
        for arg in cls._required_v_args:
            if not hasattr(cls, arg):
                raise MissingVerilogArgError(cls, arg)

    def __post_init__(self):
        if self.channel is not None:
            self.channelized = True

        if self.channelized and not self.can_channelize:
            raise NotImplementedError(f"Check {self.name!r} channelized")

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

    def _v_checks(self) -> None:
        self.check_v_args()

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

    def to_verilog(self) -> str:
        """Return a SystemVerilog module for the current check.

        Will raise an error if any required arguments (e.g. xlen) are not set on
        the class.
        """
        self._v_checks()
        v_str = f"module {self._v_modname()} (\n{self._v_format_block(self._v_io())});\n\n"
        body = self._v_body()
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

    def to_verilog(self):
        v_str = ""
        for check in self._subchecks():
            v_str += check.to_verilog() + '\n\n'
        return v_str + super().to_verilog()
