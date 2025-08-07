from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Literal

import yosys_mau.config_parser as cfg
from yosys_mau import task_loop as tl
from yosys_mau.source_str import report, read_file


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

    parser.set_defaults(command="setup", proof_args=[])

    return parser


@tl.task_context
class App:
    raw_args: argparse.Namespace

    debug: bool = False
    debug_events: bool = False

    command: Literal["setup"]

    cfg_file: Path
    work_dir: Path

    config: RvfConfig


class FlagPresent(cfg.ValueParser[bool]):  # TODO move to mau
    allow_empty = True

    def parse(self, input: str) -> bool:
        if input:
            raise report.InputError(input, "option takes no argument")
        return True


class RvfOptions(cfg.ConfigOptions):
    nret = cfg.Option(cfg.IntValue(min=1), default=1)
    isa = cfg.Option(cfg.StrValue(), default="rv32i")  # TODO validate value?
    blackbox = cfg.Option(FlagPresent(), default=False)
    solver = cfg.Option(cfg.StrValue(), default="boolector")
    dumpsmt2 = cfg.Option(FlagPresent(), default=False)
    abspath = cfg.Option(FlagPresent(), default=False)  # TODO what is this?
    mode = cfg.Option(cfg.EnumValue("bmc", "prove", "cover"), default="bmc")
    buslen = cfg.Option(cfg.IntValue(), default=32)  # TODO valid values?
    nbus = cfg.Option(cfg.IntValue(min=1), default=1)
    csr_spec = cfg.Option(cfg.StrValue(), default=None)  # TODO validate value?


class RvfConfig(cfg.ConfigParser):
    options = cfg.OptionsSection(RvfOptions)

    defines = cfg.StrSection(concat=True).with_arguments(cfg.StrValue(allow_empty=True))
    script_defines = cfg.StrSection(concat=True).with_arguments(cfg.StrValue(allow_empty=True))
    script_defines.attr_name = "script-defines"  # TODO some sections use - some _
    script_sources = cfg.StrSection(concat=True).with_arguments(cfg.StrValue(allow_empty=True))
    script_sources.attr_name = "script-sources"  # TODO some sections use - some _
    script_links = cfg.StrSection(concat=True).with_arguments(cfg.StrValue(allow_empty=True))
    script_links.attr_name = "script-links"  # TODO some sections use - some _

    verilog_files = cfg.FilesSection()
    verilog_files.attr_name = "verilog-files"  # TODO some sections use - some _
    vhdl_files = cfg.FilesSection()
    vhdl_files.attr_name = "vhdl-files"  # TODO some sections use - some _

    # filter_checks = TODO
    # filter_checks.attr_name = "filter-checks"  # TODO some sections use - some _

    # csrs = TODO
    # custom_csrs = TODO
    # illegal_csrs = TODO

    # sort = TODO
    # groups = TODO
    # assume = TODO
    # cover = TODO
    # depth = TODO

    unhandled = cfg.RawSection(all_sections=True)


def parse_config():
    cfg_file = App.cfg_file
    tl.log_debug("parsing config file", cfg_file)
    if not cfg_file.name.endswith(".cfg"):
        tl.log_error("A riscv-formal configuration file name has to end with '.cfg'")
    try:
        App.config = RvfConfig(read_file(App.cfg_file))
    except BaseException:
        tl.log_error("Failed to parse config:", raise_error=False)
        raise
