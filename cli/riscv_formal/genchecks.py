from __future__ import annotations
import re
import shutil
from pathlib import Path
from typing import TextIO, Iterable

from yosys_mau import task_loop as tl
from yosys_mau.source_str import SourceStr

from riscv_formal.config import IllegalCsrConfig, arg_parser, App, parse_config
from riscv_formal.generic_checker import GenericChecker
from riscv_formal.checks import InstructionChecker
from riscv_formal.checks.base_isa import base_checks
from riscv_formal.csrs import Csr
from riscv_formal.insns import Instruction
from riscv_formal.named_set import NamedSet
from riscv_formal.cons import ConsSpec, Cons


def hfmt(text, **kwargs):
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


def print_hfmt(f, text, **kwargs):
    for line in hfmt(text, **kwargs):
        print(line, file=f)


@tl.task_context
class Check:
    group: str | None
    checker: GenericChecker
    chanidx: int

    hargs: dict[str, str]

    instruction_checks: set[str]
    consistency_checks: set[str]

    @property
    def prefix(self) -> str:
        return "" if self.group is None else f"{self.group}_"

    @property
    def name(self) -> str:
        return self.filter_names[-1]

    @property
    def filter_names(self) -> list[str]:
        pf, chanidx = self.prefix, self.chanidx

        if isinstance(self.checker, Csr):
            if self.checker.behavior is not None:
                short_name = self.checker.behavior.short_name
                check = f"csrc_{short_name}"
            elif self.checker.is_accessible:
                check = "csrw"
            else:
                check = "csr_ill"
        elif isinstance(self.checker, Cons):
            return [
                f"{pf}{self.checker.name}",
                f"{pf}{self.checker.name}_ch{chanidx:d}",
            ]
        else:
            check = "insn"

        insn = self.checker.name
        
        if isinstance(self.checker, Csr) and self.checker.behavior is not None:
            short_name = self.checker.behavior.short_name
            return [
                f"{pf}{check}",
                f"{pf}{check}_ch{chanidx:d}",
                f"{pf}{check}_{insn}",
                f"{pf}{check}_{insn}_ch{chanidx:d}",
                f"{pf}csrc_{short_name}",
                f"{pf}csrc_{short_name}_ch{chanidx:d}",
                f"{pf}csrc_{short_name}_{insn}",
                f"{pf}csrc_{short_name}_{insn}_ch{chanidx:d}",
            ]
        else:
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

        for grp in App.config.groups:
            tl.log_debug(f"instructions for group {grp!r}")
            for checker in [
                *App.config.options.isa.insns,
                *App.config.options.csr_spec.csrs,
            ]:
                for chanidx in range(App.config.options.nret):
                    gen_check = GenInsnCheck()
                    with gen_check.as_current_task():
                        Check.group = grp
                        Check.checker = checker
                        Check.chanidx = chanidx
                        Check.hargs = hargs
                    await gen_check.finished

            tl.log_debug(f"consistency checks for group {grp!r}")
            cons_spec = ConsSpec()
            cons_spec.generate(App.config.options.isa)
            for checker in cons_spec.cons:
                for chanidx in range(App.config.options.nret):
                    gen_check = GenConsCheck()
                    with gen_check.as_current_task():
                        Check.group = grp
                        Check.checker = checker
                        Check.chanidx = chanidx
                        Check.hargs = hargs
                    await gen_check.finished

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


class GenConsCheck(tl.Task):
    async def on_prepare(self) -> None:
        tl.LogContext.scope = f"genchecks[{Check.name}]"

    async def on_run(self):
        filter_names = Check.filter_names
        name = filter_names[-1]
        depth_cfg = App.config.depth[filter_names]
        if depth_cfg is None:
            tl.log_debug(f"no depth configured")
            return

        assert isinstance(Check.checker, Cons)
        expect_depth = 1
        if Check.checker.has_start:
            expect_depth += 1
        if Check.checker.has_trig:
            expect_depth += 1
        if len(depth_cfg.depths) != expect_depth:
            depth_cfg.incorrect_depths(expect_depth)

        if not App.config.filter_checks.is_enabled(name):
            tl.log_debug(f"disabled by filter")
            return

        tl.log_warning("not yet configured")

        return


class GenInsnCheck(tl.Task):
    async def on_prepare(self) -> None:
        tl.LogContext.scope = f"genchecks[{Check.name}]"

    async def on_run(self):
        filter_names = Check.filter_names
        name = filter_names[-1]

        depth_cfg = App.config.depth[filter_names]
        if depth_cfg is None:
            tl.log_debug(f"no depth configured")
            return
        if len(depth_cfg.depths) != 1:
            depth_cfg.incorrect_depths(1)
        if not App.config.filter_checks.is_enabled(name):
            tl.log_debug(f"disabled by filter")
            return
        Check.instruction_checks.add(name)

        hargs = dict(Check.hargs)

        hargs["insn"] = Check.checker.name
        hargs["checkch"] = name
        hargs["channel"] = str(Check.chanidx)
        hargs["depth"] = str(depth_cfg.depths[0])
        hargs["depth_plus"] = str(depth_cfg.depths[0] + 1)
        hargs["skip"] = str(depth_cfg.depths[0])

        if isinstance(Check.checker, Instruction):
            insn_check_wrapper = InstructionChecker(
                name = "insn_check",
                instructions = NamedSet([Check.checker]),
                observers = App.rvfi.observers,
                defined_checks = base_checks(),
                channel = Check.chanidx,
            )
            insn_check_wrapper.configure_io()
            checker_module = "rvfi_insn_check"
            checker_dir = "insns"
            legal_csr = True
        else:
            assert isinstance(Check.checker, Csr)
            insn_check_wrapper = None
            checker_module = "rvfi_csr_check"
            checker_dir = "csrs"
            legal_csr = Check.checker.is_accessible

        (App.work_dir / checker_dir).mkdir(exist_ok=True)
        checker_name = Check.checker.name + '.sv'
        if isinstance(checker_name, SourceStr):
            # convert SourceStr to str
            checker_name = checker_name.as_plain_str()
        checker_src = Path(checker_dir) / checker_name
        with (App.work_dir / checker_src).open("w") as checker_file:
            checker = insn_check_wrapper or Check.checker
            print(checker.to_verilog(), file=checker_file)

        with (App.work_dir / f"{name}.sby").open("w") as sby_file:
            print_hfmt(
                sby_file,
                """
                : [options]
                : mode @mode@
                : expect pass
                : append @append@
                : depth @depth_plus@
                : #skip @skip@
                :
                : [engines]
                : @engine@
                :
                : [script]
            """,
                **hargs,
            )

            if App.config.script_defines:
                print_hfmt(sby_file, App.config.script_defines, **hargs)

            sv_files = [f"{name}.sv"]
            if App.config.verilog_files:
                sv_files += hfmt(App.config.verilog_files, **hargs)

            vhdl_files = []
            if App.config.vhdl_files:
                vhdl_files += hfmt(App.config.vhdl_files, **hargs)

            if len(sv_files):
                print(f"read -sv {' '.join(sv_files)}", file=sby_file)

            if len(vhdl_files):
                print(f"read -vhdl {' '.join(vhdl_files)}", file=sby_file)

            if App.config.script_sources:
                print_hfmt(sby_file, App.config.script_sources, **hargs)

            print_hfmt(
                sby_file,
                """
                : prep -flatten -nordff -top rvfi_testbench
                """,
                **hargs,
            )

            if App.config.script_link:
                print_hfmt(sby_file, App.config.script_link, **hargs)

            print_hfmt(
                sby_file,
                """
                : chformal -early
                :
                : [files]
                : @basedir@/checks/rvfi_macros.vh
                : @pkgdir@/checks/rvfi_channel.sv
                : @pkgdir@/checks/rvfi_testbench.sv
                """,
                **hargs,
            )

            print_hfmt(sby_file, str(checker_src), **hargs)

            print_hfmt(
                sby_file,
                """
                :
                : [file defines.sv]
                : `define RISCV_FORMAL
                : `define RISCV_FORMAL_NRET @nret@
                : `define RISCV_FORMAL_XLEN @xlen@
                : `define RISCV_FORMAL_ILEN @ilen@
                : `define RISCV_FORMAL_RESET_CYCLES 1
                : `define RISCV_FORMAL_CHECK_CYCLE @depth@
                : `define RISCV_FORMAL_CHANNEL_IDX @channel@
                """,
                **hargs,
            )

            if App.config.assume:
                print("`define RISCV_FORMAL_ASSUME", file=sby_file)

            if App.config.options.mode == "prove":
                print("`define RISCV_FORMAL_UNBOUNDED", file=sby_file)

            if insn_check_wrapper is not None:
                csr_list = set()
                for obs in insn_check_wrapper.get_used_io().names():
                    m = re.match(r"csr_([a-z0-9]+)_\w+", obs)
                    if m:
                        csr_list.add(m.group(1))
            else:
                # TODO do we need an option to always define all enabled CSRs
                # e.g. if someone has hardcoded their interfaces instead of using the macros
                csr_list = [Check.checker.name]

            custom_csrs: set[str] = set()
            for csr in sorted(csr_list):
                if csr in App.config.options.csr_spec.custom_csrs:
                    if legal_csr:
                        custom_csrs.add(csr)
                else:
                    print(f"`define RISCV_FORMAL_CSR_{csr.upper()}", file=sby_file)

            if custom_csrs:
                print_custom_csrs(custom_csrs, sby_file)

            # TODO figure out illegal csr modes
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

            print_hfmt(
                sby_file,
                f"""
                : `define RISCV_FORMAL_CHECKER {checker_module}
                """,
                **hargs,
            )

            if App.config.options.blackbox:
                print("`define RISCV_FORMAL_BLACKBOX_REGS", file=sby_file)

            if App.config.options.isa.compressed:
                print("`define RISCV_FORMAL_COMPRESSED", file=sby_file)

            if App.config.defines.get("", ""):
                print_hfmt(sby_file, App.config.defines[""], **hargs)

            print_hfmt(
                sby_file,
                """
                : `include "rvfi_macros.vh"
                :
                : [file @checkch@.sv]
                : `include "defines.sv"
                : `include "rvfi_channel.sv"
                : `include "rvfi_testbench.sv"
                """,
                **hargs,
            )

            print_hfmt(
                sby_file,
                f"""
                : `include "{checker_src.name}"
                """,
                **hargs,
            )

            if App.config.assume:
                print("", file=sby_file)
                print("[file assume_stmts.vh]", file=sby_file)
                for statement in App.config.assume.statements:
                    if statement.is_enabled(name):
                        print(statement.sv_statement, file=sby_file)


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
