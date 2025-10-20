from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
import re
from typing import Any, Iterable, Literal, Mapping, NoReturn, Self

import yosys_mau.config_parser as cfg
from yosys_mau import task_loop as tl
from yosys_mau.source_str import report, read_file, re as ssre

from riscv_formal.insns import Isa
from riscv_formal.csrs import CsrSpec, CsrConfig
from riscv_formal.rvfi import Rvfi


def sphinx_docs_arg_parser() -> argparse.ArgumentParser:
    return arg_parser(sphinx_docs=True)


def arg_parser(sphinx_docs=False) -> argparse.ArgumentParser:
    global_options = argparse.ArgumentParser(add_help=False)
    usage = "%(prog)s [options] <config>.cfg"
    parser = argparse.ArgumentParser(prog="riscv_formal", usage=usage, parents=[global_options])

    # This is a workaround to have options that can be used before and after the subcommand
    def global_argument(*args: Any, **kwargs: Any):
        global_options.add_argument(
            *args,  # type: ignore
            **{**kwargs, "default": argparse.SUPPRESS},  # type: ignore
        )
        parser.add_argument(*args, **kwargs)

    global_argument("--debug", action="store_true", help="enable debug logging")
    global_argument("--debug-events", action="store_true", help="enable debug event logging")

    global_argument(
        "-j",
        metavar="<N>",
        type=int,
        dest="jobs",
        help="maximum number of processes to run in parallel",
        default=None,
    )

    global_argument(
        "--load",
        metavar="EXTENSION",
        type=Path,
        action="append",
        dest="extensions",
        help="python script for loading custom ISA extension, can be specified multiple times",
        default=[],
    )

    parents = [] if sphinx_docs else [global_options]

    parser.add_argument(
        "cfg_file", metavar="<config>.cfg", help="riscv-formal config file", type=Path
    )

    commands = parser.add_subparsers(
        help="command to run:", required=False, metavar="<command>", dest="command"
    )

    commands.add_parser(
        "setup",
        usage="%(prog)s",
        parents=parents,
        help="TODO",
    )

    commands.add_parser(
        "genchecks",
        usage="%(prog)s",
        parents=parents,
        help="TODO",
    )

    parser.set_defaults(command="setup", proof_args=[])

    return parser


@tl.task_context
class App:
    raw_args: argparse.Namespace

    debug: bool = False
    debug_events: bool = False

    command: Literal["setup"]

    extensions: list[Path]

    cfg_file: Path
    work_dir: Path
    base_dir: Path

    config: RvfConfig

    rvfi: Rvfi


class FlagPresent(cfg.ValueParser[bool]):  # TODO move to mau
    allow_empty = True

    def parse(self, input: str) -> bool:
        if input:
            raise report.InputError(input, "option takes no argument")
        return True


class IsaValue(cfg.ValueParser[Isa]):
    def parse(self, input: str) -> Isa:
        return Isa(str=input)


class CsrSpecValue(cfg.ValueParser[CsrSpec]):
    def parse(self, input: str) -> CsrSpec:
        return CsrSpec(str=input)


class RvfOptions(cfg.ConfigOptions):
    nret = cfg.Option(cfg.IntValue(min=1), default=1)
    isa = cfg.Option(IsaValue(), default=Isa("rv32i"))
    blackbox = cfg.Option(FlagPresent(), default=False)
    solver = cfg.Option(cfg.StrValue(), default="boolector")
    dumpsmt2 = cfg.Option(FlagPresent(), default=False)
    abspath = cfg.Option(FlagPresent(), default=False)  # TODO what is this?
    mode = cfg.Option(cfg.EnumValue("bmc", "prove", "cover"), default="bmc")
    buslen = cfg.Option(cfg.IntValue(), default=32)  # TODO valid values?
    nbus = cfg.Option(cfg.IntValue(min=1), default=1)
    csr_spec = cfg.Option(CsrSpecValue(), default=CsrSpec())

    def validate(self):
        self.isa.generate()
        if "Zicsr" in self.isa.mods:
            self.csr_spec.generate(self.isa)
        elif self.csr_spec.str is not None:
            # TODO can we input error on the option rather than the value?
            raise report.InputError(self.isa.str, "isa must include Zicsr to enable csr checks")


def compile_re(pattern: str) -> re.Pattern[str]:
    # TODO provide a re.compile wrapper like this in mau
    try:
        return re.compile(pattern)
    except re.error as err:
        if err.pos is None:
            raise report.InputError(pattern, "regex error: " + err.msg)
        else:
            raise report.InputError(pattern[err.pos : err.pos + 1], "regex error: " + err.msg)


@dataclass
class CheckFilter:
    mode: Literal["-", "+"]
    pattern: re.Pattern[str]

    @classmethod
    def parse(cls, line: str) -> Self:
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise report.InputError(line, "expected filter mode followed by a regular expression")
        mode, pattern_str = parts
        if mode not in ("+", "-"):
            raise report.InputError(mode, "expected `+` for inclusion or `-` for exclusion")

        return cls(mode, compile_re(pattern_str))


@dataclass
class CheckFilters:
    filters: list[CheckFilter]

    def is_enabled(self, name: str) -> bool:
        for filter in self.filters:
            if filter.pattern.match(name):
                return filter.mode == "+"
        return True


@dataclass
class CheckSorting:
    patterns: list[re.Pattern[str]]

    def sort_key(self, name: str) -> tuple[int, str]:
        for i, pattern in enumerate(self.patterns):
            if pattern.fullmatch(name):
                return i, name
        return len(self.patterns), name


@dataclass
class AssumeStatement:
    pattern: re.Pattern[str]
    invert_pattern: bool
    sv_statement: str

    @classmethod
    def parse(cls, subsection: str, line: str) -> Self:
        if subsection == "":
            parts = line.split(None, 1)
        else:
            parts = subsection, line
        if len(parts) != 2:
            raise report.InputError(
                line, "expected regular expression followed by a SystemVerilog statement"
            )
        pattern_str, sv_statement = parts
        invert_pattern = pattern_str.startswith("!")
        if invert_pattern:
            pattern_str = pattern_str[1:]

        return cls(compile_re(pattern_str), invert_pattern, sv_statement)

    def is_enabled(self, check: str) -> bool:
        return bool(self.pattern.match(check)) ^ self.invert_pattern

@dataclass
class AssumeStatements:
    statements: list[AssumeStatement]

    def __len__(self):
        return len(self.statements)


@dataclass
class CheckDepth:
    pattern: re.Pattern[str]
    depths: tuple[int, ...]

    parts: tuple[str, ...]  # for error reporting

    @classmethod
    def parse(cls, line: str) -> Self:
        parts = line.split()
        if len(parts) < 2:
            raise report.InputError(
                line, "expected regular expression followed by a list of cycle counts"
            )
        pattern_str, *depths_str = parts
        depth_parser = cfg.IntValue(min=0)
        depths = tuple(map(depth_parser.parse, depths_str))
        return cls(compile_re(pattern_str), depths, tuple(parts))

    def excess_depths(self, n: int) -> NoReturn:
        raise report.InputError(self.parts[n + 1], "unexpected extra depth value")

    def missing_depths(self, n: int) -> NoReturn:
        raise report.InputError(self.parts[-1][-1:], f"expected {n} depth values")

    def incorrect_depths(self, n: int) -> NoReturn:
        assert len(self.depths) != n
        if len(self.depths) < n:
            self.missing_depths(n)
        else:
            self.excess_depths(n)


@dataclass
class CheckDepths:
    depths: list[CheckDepth]

    def __getitem__(self, key: Iterable[str]) -> CheckDepth | None:
        for depth in self.depths:
            for alternative in key:
                if depth.pattern.fullmatch(alternative):
                    return depth


def parse_csr_addr_and_mode(
    addr_str: str, modes_str: str
) -> tuple[int, set[Literal["m", "s", "u"]]]:
    try:
        addr = int(addr_str, base=16)
    except ValueError:
        raise report.InputError(addr_str, "expected hexadecimal csr address")

    modes = set()
    for mode in ssre.findall(r".", modes_str):
        if mode in ("m", "s", "u"):
            modes.add(mode)
        else:
            raise report.InputError(mode, f"unsupported privilege mode `{mode}`")

    return addr, modes


@dataclass
class CustomCsrConfig(CsrConfig):
    addr: int
    modes: set[Literal["m", "s", "u"]]

    @classmethod
    def parse(cls, line: str, **kwds) -> Self:
        match line.split(maxsplit=2):
            case [addr_str, modes_str, csr_str]:
                addr, modes = parse_csr_addr_and_mode(addr_str, modes_str)
                return super().parse(csr_str, addr=addr, modes=modes, **kwds)
            case _:
                raise report.InputError(
                    line,
                    "expected a csr addr, a list of privilege modes and a csr name "
                    "followed by an optional list of csr tsts",
                )


@dataclass
class IllegalCsrConfig:
    addr: int
    modes: set[Literal["m", "s", "u"]]
    rw: set[Literal["r", "w"]]

    @classmethod
    def parse(cls, line: str) -> Self:
        match line.split():
            case [addr_str, modes_str, rw_str]:
                addr, modes = parse_csr_addr_and_mode(addr_str, modes_str)

                rw = set()
                for c in ssre.findall(r".", rw_str):
                    if c in ("r", "w"):
                        rw.add(c)
                    else:
                        raise report.InputError(c, f"unsupported access mode `{c}`")
                return cls(addr, modes, rw)
            case _:
                raise report.InputError(
                    line,
                    "expected a csr addr, a list of privilege modes and a list of access modes",
                )


class RvfConfig(cfg.ConfigParser):
    options = cfg.OptionsSection(RvfOptions)

    defines = cfg.StrSection(concat=True).with_arguments(cfg.StrValue(allow_empty=True))
    script_defines = cfg.StrSection(concat=True).with_arguments(cfg.StrValue(allow_empty=True))
    script_defines.attr_name = "script-defines"  # TODO some sections use - some _
    script_sources = cfg.StrSection(concat=True, default="")
    script_sources.attr_name = "script-sources"  # TODO some sections use - some _
    script_link = cfg.StrSection(concat=True, default="")
    script_link.attr_name = "script-link"  # TODO some sections use - some _

    verilog_files = cfg.FilesSection()
    verilog_files.attr_name = "verilog-files"  # TODO some sections use - some _
    vhdl_files = cfg.FilesSection()
    vhdl_files.attr_name = "vhdl-files"  # TODO some sections use - some _

    @cfg.postprocess_section(
        cfg.FilesSection()
    )  # TODO there should be a separate LinesSection in mau
    def filter_checks(self, lines: list[str]) -> CheckFilters:
        return CheckFilters([CheckFilter.parse(line) for line in lines])

    filter_checks.attr_name = "filter-checks"  # TODO some sections use - some _

    @cfg.postprocess_section(
        cfg.FilesSection()
    )  # TODO there should be a separate LinesSection in mau
    def csrs(self, lines: list[str]) -> list[CsrConfig]:
        return [CsrConfig.parse(line) for line in lines]

    @cfg.postprocess_section(
        cfg.FilesSection()
    )  # TODO there should be a separate LinesSection in mau
    def custom_csrs(self, lines: list[str]) -> list[CustomCsrConfig]:
        return [CustomCsrConfig.parse(line) for line in lines]

    @cfg.postprocess_section(
        cfg.FilesSection()
    )  # TODO there should be a separate LinesSection in mau
    def illegal_csrs(self, lines: list[str]) -> list[IllegalCsrConfig]:
        return [IllegalCsrConfig.parse(line) for line in lines]

    @cfg.postprocess_section(
        cfg.FilesSection()
    )  # TODO there should be a separate LinesSection in mau
    def sort(self, lines: list[str]) -> CheckSorting:
        return CheckSorting([compile_re(line) for line in lines])

    @cfg.postprocess_section(
        cfg.FilesSection()
    )  # TODO there should be a separate LinesSection in mau
    def groups(self, lines: list[str]) -> list[str | None]:
        return [None] + [line.strip() for line in lines]

    @cfg.postprocess_section(
        cfg.FilesSection().with_arguments(cfg.StrValue(allow_empty=True))
    )  # TODO there should be a separate LinesSection in mau
    def assume(self, lines_per_subsection: Mapping[str, list[str]]) -> AssumeStatements:
        return AssumeStatements(
            [
                AssumeStatement.parse(subsection, line)
                for subsection, lines in lines_per_subsection.items()
                for line in lines
            ]
        )

    cover = cfg.StrSection(default="")

    @cfg.postprocess_section(
        cfg.FilesSection()
    )  # TODO there should be a separate LinesSection in mau
    def depth(self, lines: list[str]) -> CheckDepths:
        return CheckDepths([CheckDepth.parse(line) for line in lines])

    def validate(self):
        # there shouldn't be any csr sections if the core doesn't have Zicsr
        if "Zicsr" not in self.options.isa.mods:
            for csr in [
                *self.csrs,
                *self.custom_csrs,
                *self.illegal_csrs,
            ]:
                # TODO what is the correct way to report this?  Can we InputError on two locations?
                raise report.InputError(self.options.isa.str, "isa must include Zicsr to enable csr checks")


def parse_config():
    App.cfg_file
    tl.log_debug("parsing config file", App.cfg_file)
    if not App.cfg_file.name.endswith(".cfg"):
        # the old genchecks.py unconditionally appends '.cfg'
        App.cfg_file = App.cfg_file.with_suffix(".cfg")

    App.work_dir = App.cfg_file.with_suffix("")
    try:
        App.config = RvfConfig(read_file(App.cfg_file))
    except BaseException:
        tl.log_error("Failed to parse config:", raise_error=False)
        raise

    # add config defined CSRs to CSR spec
    for csr in App.config.csrs:
        App.config.options.csr_spec.config_csr(csr)

    # TODO what happens to the privilege levels on custom CSRs?
    # Csr class auto determines based on address range
    for csr in App.config.custom_csrs:
        App.config.options.csr_spec.add_csr(csr.addr, csr.name)
        App.config.options.csr_spec.config_csr(csr)

    for csr in App.config.illegal_csrs:
        App.config.options.csr_spec.add_csr(csr.addr)
        App.config.options.csr_spec.mark_illegal(csr.addr)

    App.rvfi = Rvfi()
    for csr in App.config.options.csr_spec.csrs:
        for obs in csr.make_observers():
            App.rvfi.add_observer(obs)
