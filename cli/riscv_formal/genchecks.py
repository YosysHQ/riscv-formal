from __future__ import annotations
import re
import shutil
from pathlib import Path
from textwrap import dedent
from typing import TextIO, Iterable, Callable

from yosys_mau import task_loop as tl
from yosys_mau.source_str import SourceStr

from riscv_formal.config import App, CheckDepth
from riscv_formal.generic_checker import GenericChecker
from riscv_formal.checks import InstructionChecker
from riscv_formal.checks.base_isa import base_checks
from riscv_formal.csrs import Csr
from riscv_formal.insns import Instruction
from riscv_formal.named_set import NamedSet
from riscv_formal.cons import ConsSpec, Cons, BusCons

from riscv_formal.csrs import ConstValue


def hfmt(text: str | Iterable[str], **kwargs: str):
    lines = []
    text_lines = text.split("\n") if isinstance(text, str) else text
    for line in text_lines:
        match = re.match(r"^\s*: ?(.*)", line)
        if match:
            line = match.group(1)
        elif line.strip() == "":
            continue
        lines.append(re.sub(r"@([a-zA-Z0-9_]+)@", lambda match: str(kwargs[match.group(1)]), line))
    return lines


def print_hfmt(f: TextIO, text: str | Iterable[str], **kwargs: str):
    for line in hfmt(text, **kwargs):
        print(line, file=f)


@tl.task_context
class Check:
    group: str | None
    checker: GenericChecker
    chanidx: int | None

    hargs: dict[str, str]

    instruction_checks: set[str]
    consistency_checks: set[str]

    @property
    def prefix(self) -> str:
        return "" if self.group is None else f"{self.group}_"

    @property
    def check(self) -> str:
        try:
            return self.filter_names[-2]
        except IndexError:
            return self.name

    @property
    def name(self) -> str:
        return self.filter_names[-1]

    @property
    def filter_names(self) -> list[str]:
        pf, chanidx = self.prefix, self.chanidx

        def maybe_channel(name: str) -> Iterable[str]:
            yield name
            if self.chanidx is not None:
                yield name + f"_ch{self.chanidx:d}"

        if isinstance(self.checker, Csr):
            if self.checker.behavior is not None:
                check = f"csrc_{self.checker.behavior.NAME}"
            elif self.checker.is_accessible:
                check = "csrw"
            else:
                check = "csr_ill"
        elif isinstance(self.checker, Cons):
            return [
                *maybe_channel(f"{pf}{self.checker.name}"),
            ]
        else:
            check = "insn"

        assert chanidx is not None
        insn = self.checker.name

        return [
            f"{pf}{check}",
            f"{pf}{check}_ch{chanidx:d}",
            f"{pf}{check}_{insn}",
            f"{pf}{check}_{insn}_ch{chanidx:d}",
        ]


class GenChecks(tl.Task):
    async def on_prepare(self) -> None:
        tl.LogContext.scope = "genchecks"

    async def on_run(self):
        tl.log(f"Creating {App.work_dir} directory.")
        if App.work_dir.exists():
            tl.log("Removing old work directory.")
            shutil.rmtree(App.work_dir)
        App.work_dir.mkdir()

        hargs = dict()
        # TODO error on basedir
        hargs["basedir"] = App.base_dir
        hargs["cfgdir"] = App.cfg_file.resolve().parent
        hargs["pkgdir"] = App.pkg_dir
        hargs["coredir"] = App.core_dir
        hargs["core"] = App.core_name
        hargs["nret"] = App.config.options.nret
        hargs["xlen"] = App.config.options.isa.xlen
        hargs["ilen"] = 32
        hargs["buslen"] = App.config.options.buslen
        hargs["nbus"] = App.config.options.nbus
        hargs["append"] = 0
        hargs["mode"] = App.config.options.mode

        if App.config.cover:
            hargs["cover"] = App.config.cover

        Check.instruction_checks = set()
        Check.consistency_checks = set()

        defines = App.config.defines.get("", "")
        if "`define RISCV_FORMAL_MEM_FAULT" in defines:
            from riscv_formal.rvfi import mem_fault

        # TODO refactor solver selection
        if App.config.options.solver == "bmc3":
            hargs["engine"] = "abc bmc3"
            hargs["ilang_file"] = f"{App.core_name}-gates.il"
        elif App.config.options.solver == "btormc":
            hargs["engine"] = "btor btormc"
            hargs["ilang_file"] = f"{App.core_name}-hier.il"
        else:
            hargs["engine"] = (
                f"smtbmc {'--dumpsmt2 ' if App.config.options.dumpsmt2 else ''}{App.config.options.solver}"
            )
            hargs["ilang_file"] = f"{App.core_name}-hier.il"

        cons_spec = ConsSpec()
        cons_spec.generate(App.config.options.isa)

        async def generate(grp: str | None, checker: GenericChecker):
            channels = range(App.config.options.nret) if checker.can_channelize else [None]
            for chanidx in channels:
                if isinstance(checker, Cons):
                    gen_check = GenConsCheck()
                else:
                    gen_check = GenInsnCheck()
                with gen_check.as_current_task():
                    Check.group = grp
                    Check.checker = checker
                    Check.chanidx = chanidx
                    Check.hargs = hargs
                await gen_check.finished

        for grp in App.config.groups:
            tl.log_debug(f"instruction checks for group {grp!r}")
            for insn in App.config.options.isa.insns:
                await generate(grp, insn)

            tl.log_debug(f"csr checks for group {grp!r}")
            csr_spec = App.config.options.csr_spec
            for csr in csr_spec.csrs:
                # store defaults
                default_behavior = csr.behavior

                # don't do RW testing in behavior tests
                rw_test = csr.rw_test
                csr.rw_test = False

                # test default behavior (if there is one)
                if csr.behavior is not None:
                    await generate(grp, csr)

                # test behaviors from config
                config = csr_spec.csr_configs[csr.name]
                for test, value in config.tests.items():
                    # TODO catch unknown behaviors
                    behavior_type = csr_spec.get_behavior(test)
                    if value is None:
                        csr.behavior = behavior_type()
                    else:
                        # TODO catch invalid args
                        csr.behavior = behavior_type(value) # type: ignore
                    await generate(grp, csr)

                # test RW access
                if rw_test:
                    csr.rw_test = True
                    csr.behavior = None
                    await generate(grp, csr)

                # restore defaults
                csr.behavior = default_behavior

            tl.log_debug(f"consistency checks for group {grp!r}")
            for checker in cons_spec.cons:
                await generate(grp, checker)

        checks = sorted(
            Check.consistency_checks | Check.instruction_checks,
            key=lambda name: App.config.sort.sort_key(name),
        )

        with (App.work_dir / f"makefile").open("w") as mkfile:
            print("all:", end="", file=mkfile)

            for check in checks:
                print(f" {check}", end="", file=mkfile)
            print(file=mkfile)

            sbycmd = "sby"  # TODO configurable?

            for check in checks:
                print(f"{check}: {check}/status", file=mkfile)
                print(f"{check}/status:", file=mkfile)
                if App.config.options.abspath:
                    print(f"\t{sbycmd} $(shell pwd)/{check}.sby", file=mkfile)
                else:
                    print(f"\t{sbycmd} {check}.sby", file=mkfile)
                print(f".PHONY: {check}", file=mkfile)

        tl.log(f"Generated {len(checks)} checks.")


class GenShared(tl.Task):
    sby_file: TextIO
    hargs: dict[str, str]
    def print_hfmt(self, text: str | Iterable[str]):
        print_hfmt(self.sby_file, text, **self.hargs)

    async def on_prepare(self) -> None:
        tl.LogContext.scope = f"genchecks[{Check.name}]"

    @property
    def _expected_depth(self) -> int:
        raise NotImplementedError()

    @property
    def _register(self) -> Callable[[str], None]:
        raise NotImplementedError()

    def _config_hargs(self, depth_cfg: CheckDepth):
        self.hargs = dict(Check.hargs)
        self.hargs.update({
            "checkch": Check.name,
            "channel": str(Check.chanidx),
            "depth": str(depth_cfg.depths[-1]),
            "depth_plus": str(depth_cfg.depths[-1] + 1),
            "skip": str(depth_cfg.depths[-1]),
            "start": "1",
        })

    def _options_section(self) -> None:
        self.print_hfmt(dedent("""
            mode @mode@
            expect pass,fail
            append @append@
            depth @depth_plus@
            #skip @skip@
        """))

    def _engines_section(self) -> None:
        return self.print_hfmt("@engine@")

    def _script_section(self) -> None:
        # [script-defines]
        if "" in App.config.script_defines:
            self.print_hfmt(App.config.script_defines[""].rstrip())
        filter_names = list(Check.filter_names)
        filter_names.reverse()
        # [script-defines <check>]
        # most-specific match only
        for check_name in filter_names:
            if check_name in App.config.script_defines:
                self.print_hfmt(App.config.script_defines[check_name].rstrip())
                break

        # read [verilog-files] and [vhdl-files]
        sv_files = [
            f"{Check.name}.sv",
            *App.config.verilog_files,
        ]
        vhdl_files = [
            *App.config.vhdl_files,
        ]
        if sv_files:
            self.print_hfmt(f"read -sv {' '.join(sv_files)}")
        if vhdl_files:
            self.print_hfmt(f"read -vhdl {' '.join(sv_files)}")

        # [script-sources] before prep
        self.print_hfmt(App.config.script_sources.rstrip())
        self.print_hfmt("prep -flatten -nordff -top rvfi_testbench")

        # [script-link] before chformal
        self.print_hfmt(App.config.script_link.rstrip())
        self.print_hfmt("chformal -early")

    def _files_section(self) -> None:
        self.print_hfmt(dedent("""
            @basedir@/checks/rvfi_macros.vh
            @pkgdir@/cons/rvfi_channel.sv
            @pkgdir@/cons/rvfi_testbench.sv
        """))

    @property
    def _sby_section_map(self) -> dict[str, Callable[[], None]]:
        return {
            "options": self._options_section,
            "engines": self._engines_section,
            "script": self._script_section,
            "files": self._files_section,
        }

    @property
    def _defined_csrs(self) -> NamedSet[Csr]:
        return NamedSet(App.config.options.csr_spec.csrs)

    def _file_defines_section(self) -> None:
        # base riscv-formal defines
        self.print_hfmt(dedent("""
            `define RISCV_FORMAL
            `define RISCV_FORMAL_NRET @nret@
            `define RISCV_FORMAL_XLEN @xlen@
            `define RISCV_FORMAL_ILEN @ilen@
            `define RISCV_FORMAL_CHECKER rvfi_@check@_check
            `define RISCV_FORMAL_RESET_CYCLES @start@
            `define RISCV_FORMAL_CHECK_CYCLE @depth@
            `define RISCV_FORMAL_CHANNEL_IDX @channel@
        """))

        # use assumptions
        if App.config.assume:
            self.print_hfmt("`define RISCV_FORMAL_ASSUME\n")

        # unbounded model checking
        if App.config.options.mode == "prove":
            self.print_hfmt("`define RISCV_FORMAL_UNBOUNDED\n")

        # csrs
        custom_csrs: set[str] = set()
        for csr in self._defined_csrs:
            if not csr.is_accessible:
                continue
            csr = csr.name
            if csr in App.config.options.csr_spec.custom_csrs:
                custom_csrs.add(csr)
            else:
                self.print_hfmt(f"`define RISCV_FORMAL_CSR_{csr.upper()}")
        if custom_csrs:
            print_custom_csrs(custom_csrs, self.sby_file)

        # control blackboxes
        if App.config.options.blackbox:
            if Check.check != "liveness":
                self.print_hfmt("`define RISCV_FORMAL_BLACKBOX_ALU\n")
            if Check.check != "reg":
                self.print_hfmt("`define RISCV_FORMAL_BLACKBOX_REGS\n")

        # enable fairness guarantees
        if Check.check in ("liveness", "hang"):
            self.print_hfmt("`define RISCV_FORMAL_FAIRNESS\n")

        # [defines]
        if "" in App.config.defines:
            self.print_hfmt(App.config.defines[""])
        filter_names = list(Check.filter_names)
        filter_names.reverse()
        # [defines <check>]
        # most-specific match only
        for check_name in filter_names:
            if check_name in App.config.defines:
                self.print_hfmt(App.config.defines[check_name])
                break

    def _file_assumes_section(self) -> None:
        for statement in App.config.assume.statements:
            if statement.is_enabled(Check.name):
                print(statement.sv_statement, file=self.sby_file)

    def _file_check_section(self) -> None:
        self.print_hfmt(dedent("""
            `include "defines.sv"
            `include "rvfi_channel.sv"
            `include "rvfi_testbench.sv"
        """))

    @property
    def _sby_files_map(self) -> dict[str, Callable[[], None]]:
        files_map = {
            "defines.sv": self._file_defines_section,
            f"{Check.name}.sv": self._file_check_section,
        }

        if App.config.assume:
            files_map["assume_stmts.vh"] = self._file_assumes_section

        return files_map

    async def on_run(self) -> None:
        depth_cfg = App.config.depth[Check.filter_names]
        if depth_cfg is None:
            tl.log_debug(f"no depth configured")
            return

        expect_depth = self._expected_depth
        if len(depth_cfg.depths) != expect_depth:
            depth_cfg.incorrect_depths(expect_depth)

        if not App.config.filter_checks.is_enabled(Check.name):
            tl.log_debug(f"disabled by filter")
            return

        self._register(Check.name)
        self._config_hargs(depth_cfg)

        with (App.work_dir / f"{Check.name}.sby").open("w") as sby_file:
            self.sby_file = sby_file
            for sect, fun in self._sby_section_map.items():
                print(f"[{sect}]", file=sby_file)
                fun()
                print("", file=sby_file)

            for file, fun in self._sby_files_map.items():
                print(f"[file {file}]", file=sby_file)
                fun()
                if file == "defines.sv":
                    # rvfi_macros.vh is always last
                    print('`include "rvfi_macros.vh"', file=sby_file)
                print("", file=sby_file)
            tl.log_debug(f"generated {sby_file.name}")
            del self.sby_file
                

class GenConsCheck(GenShared):
    @property
    def _expected_depth(self) -> int:
        assert isinstance(Check.checker, Cons)
        expect_depth = 1
        if Check.checker.has_start:
            expect_depth += 1
        if Check.checker.has_trig:
            expect_depth += 1
        return expect_depth

    @property
    def _register(self) -> Callable[[str], None]:
        return Check.consistency_checks.add

    def _config_hargs(self, depth_cfg: CheckDepth):
        super()._config_hargs(depth_cfg)
        assert isinstance(Check.checker, Cons)

        # depth_cfg.depths possible configurations:
        # start, trig, depth
        # start, depth
        # depth
        depths = list(depth_cfg.depths)
        depth = depths.pop()
        trig = depths.pop() if Check.checker.has_trig else None
        start = depths.pop() if Check.checker.has_start else 1

        # sanity checking
        # TODO use InputError
        if depth <= start:
            raise NotImplementedError(f"Expected start ({start}) before depth ({depth})")
        if trig is not None and depth <= trig:
            raise NotImplementedError(f"Expected trig ({trig}) before depth ({depth})")

        self.hargs["check"] = Check.check
        self.hargs["start"] = str(start)
        if trig is not None:
            self.hargs["trig"] = str(trig)

        if Check.check == "cover" or "csrc_hpm" in Check.check:
            self.hargs["mode"] = "cover"

    def _files_section(self) -> None:
        # TODO custom consistency checks
        super()._files_section()
        self.print_hfmt('@pkgdir@/cons/rvfi_@check@_check.sv')

    def _file_defines_section(self) -> None:
        super()._file_defines_section()
        assert isinstance(Check.checker, Cons)

        if Check.checker.has_trig:
            self.print_hfmt("`define RISCV_FORMAL_TRIG_CYCLE @trig@")

        if isinstance(Check.checker, BusCons):
            self.print_hfmt(dedent("""
                `define RISCV_FORMAL_BUS
                `define RISCV_FORMAL_NBUS @nbus@
                `define RISCV_FORMAL_BUSLEN @buslen@
            """))

    def _file_check_section(self) -> None:
        super()._file_check_section()
        self.print_hfmt('`include "rvfi_@check@_check.sv"')

    def _file_cover_section(self) -> None:
        self.print_hfmt(App.config.cover)

    @property
    def _sby_files_map(self) -> dict[str, Callable[[], None]]:
        files_map = super()._sby_files_map

        if Check.check == "cover":
            files_map["cover_stmts.vh"] = self._file_cover_section

        return files_map


class GenInsnCheck(GenShared):
    _insn_check_wrapper: InstructionChecker | None = None
    _legal_csr: bool = True

    @property
    def _check_type(self) -> str:
        return "insn" if isinstance(Check.checker, Instruction) else "csr"

    @property
    def _check_dir(self) -> str:
        return self._check_type + "s"

    @property
    def _expected_depth(self) -> int:
        if isinstance(Check.checker, Csr) and Check.checker.behavior is not None:
            return 2
        else:
            return 1

    @property
    def _register(self) -> Callable[[str], None]:
        return Check.instruction_checks.add

    def _config_hargs(self, depth_cfg: CheckDepth):
        super()._config_hargs(depth_cfg)
        self.hargs["check"] = self._check_type
        self.hargs["insn"] = Check.checker.name
        if len(depth_cfg.depths) > 1:
            self.hargs["start"] = str(depth_cfg.depths[0])

    def _files_section(self) -> None:
        super()._files_section()
        self.print_hfmt(f'{self._check_dir}/{Check.check}.sv')

    def _file_check_section(self) -> None:
        super()._file_check_section()
        self.print_hfmt(f'`include "{Check.check}.sv"\n')

    async def _gen_check_source(self):
        # TODO can we limit this to only running once instead of for every channel?
        if isinstance(Check.checker, Instruction):
            self._insn_check_wrapper = InstructionChecker(
                name = "insn_check",
                instructions = NamedSet([Check.checker]),
                observers = App.rvfi.observers,
                defined_checks = base_checks(),
                channel = Check.chanidx,
            )
            self._insn_check_wrapper.configure_io()
        else:
            assert isinstance(Check.checker, Csr)
            self._legal_csr = Check.checker.is_accessible

        (App.work_dir / self._check_dir).mkdir(exist_ok=True)
        checker_name = Check.check + '.sv'
        checker_src = Path(self._check_dir) / checker_name
        with (App.work_dir / checker_src).open("w") as checker_file:
            checker = self._insn_check_wrapper or Check.checker
            print(checker.to_verilog(), file=checker_file)

    @property
    def _defined_csrs(self) -> NamedSet[Csr]:
        csrs = super()._defined_csrs
        if self._insn_check_wrapper is not None:
            used_csrs = set()
            for obs in self._insn_check_wrapper.get_used_io().names():
                m = re.match(r"csr_([a-z0-9]+)_\w+", obs)
                if m:
                    used_csrs.add(m.group(1))
        else:
            # TODO do we need an option to always define all enabled CSRs
            # e.g. if someone has hardcoded their interfaces instead of using the macros
            used_csrs = [Check.checker.name]

        available_csrs = list(csrs.names())
        for csr in available_csrs:
            if csr not in used_csrs:
                csrs.pop(csr)

        # TODO figure out illegal_csrs
        # if Check.illegal_csr:
        #     print_hfmt(
        #         sby_file,
        #         """
        #         : `define RISCV_FORMAL_CHECKER rvfi_csr_ill_check
        #         : `define RISCV_FORMAL_ILL_CSR_ADDR @insn@
        #         """,
        #         **hargs,
        #     )
        #     if "m" in Check.illegal_csr.modes:
        #         print("`define RISCV_FORMAL_ILL_MMODE", file=sby_file)
        #     if "s" in Check.illegal_csr.modes:
        #         print("`define RISCV_FORMAL_ILL_SMODE", file=sby_file)
        #     if "u" in Check.illegal_csr.modes:
        #         print("`define RISCV_FORMAL_ILL_UMODE", file=sby_file)
        #     if "r" in Check.illegal_csr.rw:
        #         print("`define RISCV_FORMAL_ILL_READ", file=sby_file)
        #     if "w" in Check.illegal_csr.rw:
        #         print("`define RISCV_FORMAL_ILL_WRITE", file=sby_file)

        return csrs

    async def on_run(self):
        await self._gen_check_source()
        await super().on_run()


def print_custom_csrs(custom_csrs: Iterable[str], sby_file: TextIO):
    fstrings = {
        "inputs": "  ,input [`RISCV_FORMAL_NRET * `RISCV_FORMAL_XLEN - 1 : 0] rvfi_csr_{csr}_{signal} \\",
        "wires": "  (* keep *) wire [`RISCV_FORMAL_NRET * `RISCV_FORMAL_XLEN - 1 : 0] rvfi_csr_{csr}_{signal}; \\",
        "conn": "  ,.rvfi_csr_{csr}_{signal} (rvfi_csr_{csr}_{signal}) \\",
        "channel": "  wire [`RISCV_FORMAL_XLEN - 1 : 0] csr_{csr}_{signal} = rvfi_csr_{csr}_{signal} [(_idx)*(`RISCV_FORMAL_XLEN) +: `RISCV_FORMAL_XLEN]; \\",
        "signals": "`RISCV_FORMAL_CHANNEL_SIGNAL(`RISCV_FORMAL_NRET, `RISCV_FORMAL_XLEN, csr_{csr}_{signal}) \\",
        "outputs": "  ,output [`RISCV_FORMAL_NRET * `RISCV_FORMAL_XLEN - 1 : 0] rvfi_csr_{csr}_{signal} \\",
    }
    for macro, fstring in fstrings.items():
        if macro == "channel":
            print(f"`define RISCV_FORMAL_CUSTOM_CSR_{macro.upper()}(_idx) \\", file=sby_file)
        else:
            print(f"`define RISCV_FORMAL_CUSTOM_CSR_{macro.upper()} \\", file=sby_file)
        for name in custom_csrs:
            for signal in ["rmask", "wmask", "rdata", "wdata"]:
                macro_string = fstring.format(csr=name, signal=signal)
                print(macro_string, file=sby_file)
        print("", file=sby_file)
