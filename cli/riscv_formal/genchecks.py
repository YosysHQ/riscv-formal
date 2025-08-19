from __future__ import annotations
import re
import shutil

from yosys_mau import task_loop as tl

from riscv_formal.config import IllegalCsrConfig, arg_parser, App, parse_config


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
    insn: str
    chanidx: int

    csr_mode: bool = False  # TODO use fewer boolean flags
    illegal_csr: IllegalCsrConfig | None = None

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
        if self.illegal_csr:
            ill_addr = self.illegal_csr.addr
            return [
                f"{pf}csr_ill",
                f"{pf}csr_ill_ch{chanidx:d}",
                f"{pf}csr_ill_{ill_addr:03x}",
                f"{pf}csr_ill_{ill_addr:03x}_ch{chanidx:d}",
            ]
        elif self.csr_mode:
            check = "csrw"
        else:
            check = "insn"

        insn = self.insn
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

        corename = App.cfg_file.parent.resolve().relative_to((App.base_dir / "cores").resolve())

        hargs = dict()
        hargs["basedir"] = App.base_dir
        hargs["core"] = corename
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

        # TODO refactor solver selection
        if App.config.options.solver == "bmc3":
            hargs["engine"] = "abc bmc3"
            hargs["ilang_file"] = f"{corename}-gates.il"
        elif App.config.options.solver == "btormc":
            hargs["engine"] = "btor btormc"
            hargs["ilang_file"] = f"{corename}-hier.il"
        else:
            hargs["engine"] = (
                f"smtbmc {'--dumpsmt2 ' if App.config.options.dumpsmt2 else ''}{App.config.options.solver}"
            )
            hargs["ilang_file"] = f"{corename}-hier.il"

        for grp in App.config.groups:
            tl.log_debug(f"instructions for group {grp!r}")
            for insn in App.config.options.isa.insns:
                for chanidx in range(App.config.options.nret):
                    gen_check = GenInsnCheck()
                    with gen_check.as_current_task():
                        Check.group = grp
                        Check.insn = insn
                        Check.chanidx = chanidx
                        Check.hargs = hargs
                    await gen_check.finished

            for csr in sorted(App.config.csrs.configs):
                for chanidx in range(App.config.options.nret):
                    gen_check = GenInsnCheck()
                    with gen_check.as_current_task():
                        Check.group = grp
                        Check.insn = csr
                        Check.chanidx = chanidx
                        Check.hargs = hargs
                        Check.csr_mode = True
                    await gen_check.finished

            for ill_csr in sorted(App.config.illegal_csrs, key=lambda csr: csr.addr):
                for chanidx in range(App.config.options.nret):
                    gen_check = GenInsnCheck()
                    with gen_check.as_current_task():
                        Check.group = grp
                        Check.insn = f"12'h{ill_csr.addr:03X}"
                        Check.illegal_csr = ill_csr
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

        tl.log_warning("generation of consistency checks not yet implemented!")

        tl.log(f"Generated {len(Check.consistency_checks) + len(Check.instruction_checks)} checks.")


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

        hargs["insn"] = Check.insn
        hargs["checkch"] = name
        hargs["channel"] = str(Check.chanidx)
        hargs["depth"] = str(depth_cfg.depths[0])
        hargs["depth_plus"] = str(depth_cfg.depths[0] + 1)
        hargs["skip"] = str(depth_cfg.depths[0])

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
                : @basedir@/checks/rvfi_channel.sv
                : @basedir@/checks/rvfi_testbench.sv
                """,
                **hargs,
            )

            if Check.illegal_csr:
                print_hfmt(
                    sby_file,
                    """
                    : @basedir@/checks/rvfi_csr_ill_check.sv
                    """,
                    **hargs,
                )
            elif Check.csr_mode:
                print_hfmt(
                    sby_file,
                    """
                    : @basedir@/checks/rvfi_csrw_check.sv
                    """,
                    **hargs,
                )
            else:
                print_hfmt(
                    sby_file,
                    """
                    : @basedir@/checks/rvfi_insn_check.sv
                    : @basedir@/insns/insn_@insn@.v
                    """,
                    **hargs,
                )

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

            for csr in sorted(App.config.csrs.configs.keys()):
                print(f"`define RISCV_FORMAL_CSR_{csr.upper()}", file=sby_file)

            if Check.csr_mode and Check.insn in ("mcycle", "minstret"):
                print("`define RISCV_FORMAL_CSRWH", file=sby_file)

            if Check.illegal_csr:
                print_hfmt(
                    sby_file,
                    """
                    : `define RISCV_FORMAL_CHECKER rvfi_csr_ill_check
                    : `define RISCV_FORMAL_ILL_CSR_ADDR @insn@
                    """,
                    **hargs,
                )
                if "m" in Check.illegal_csr.modes:
                    print("`define RISCV_FORMAL_ILL_MMODE", file=sby_file)
                if "s" in Check.illegal_csr.modes:
                    print("`define RISCV_FORMAL_ILL_SMODE", file=sby_file)
                if "u" in Check.illegal_csr.modes:
                    print("`define RISCV_FORMAL_ILL_UMODE", file=sby_file)
                if "r" in Check.illegal_csr.rw:
                    print("`define RISCV_FORMAL_ILL_READ", file=sby_file)
                if "w" in Check.illegal_csr.rw:
                    print("`define RISCV_FORMAL_ILL_WRITE", file=sby_file)
            elif Check.csr_mode:
                print_hfmt(
                    sby_file,
                    """
                    : `define RISCV_FORMAL_CHECKER rvfi_csrw_check
                    : `define RISCV_FORMAL_CSRW_NAME @insn@
                    """,
                    **hargs,
                )
            else:
                print_hfmt(
                    sby_file,
                    """
                    : `define RISCV_FORMAL_CHECKER rvfi_insn_check
                    : `define RISCV_FORMAL_INSN_MODEL rvfi_insn_@insn@
                    """,
                    **hargs,
                )

            if App.config.custom_csrs:
                self.print_custom_csrs(sby_file)

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

            if Check.illegal_csr:
                print_hfmt(
                    sby_file,
                    """
                    : `include "rvfi_csr_ill_check.sv"
                    """,
                    **hargs,
                )
            elif Check.csr_mode:
                print_hfmt(
                    sby_file,
                    """
                    : `include "rvfi_csrw_check.sv"
                    """,
                    **hargs,
                )
            else:
                print_hfmt(
                    sby_file,
                    """
                    : `include "rvfi_insn_check.sv"
                    : `include "insn_@insn@.v"
                    """,
                    **hargs,
                )

            if App.config.assume:
                print("", file=sby_file)
                print("[file assume_stmts.vh]", file=sby_file)
                for statement in App.config.assume.statements:
                    if statement.is_enabled(name):
                        print(statement.sv_statement, file=sby_file)

    def print_custom_csrs(self, sby_file):
        fstrings = {
            "inputs": "  ,input [`RISCV_FORMAL_NRET * `RISCV_FORMAL_XLEN - 1 : 0] rvfi_csr_{csr}_{signal} \\",
            "wires": "  (* keep *) wire [`RISCV_FORMAL_NRET * `RISCV_FORMAL_XLEN - 1 : 0] rvfi_csr_{csr}_{signal}; \\",
            "conn": "  ,.rvfi_csr_{csr}_{signal} (rvfi_csr_{csr}_{signal}) \\",
            "channel": "  wire [`RISCV_FORMAL_XLEN - 1 : 0] csr_{csr}_{signal} = rvfi_csr_{csr}_{signal} [(_idx)*(`RISCV_FORMAL_XLEN) +: `RISCV_FORMAL_XLEN]; \\",
            "signals": "`RISCV_FORMAL_CHANNEL_SIGNAL(`RISCV_FORMAL_NRET, `RISCV_FORMAL_XLEN, csr_{csr}_{signal}) \\",
            "outputs": "  ,output [`RISCV_FORMAL_NRET * `RISCV_FORMAL_XLEN - 1 : 0] rvfi_csr_{csr}_{signal} \\",
            "indices": "  localparam [11:0] csr_{level}index_{name} = 12'h{index:03X}; \\",
        }
        for macro, fstring in fstrings.items():
            if macro == "channel":
                print(f"`define RISCV_FORMAL_CUSTOM_CSR_{macro.upper()}(_idx) \\", file=sby_file)
            else:
                print(f"`define RISCV_FORMAL_CUSTOM_CSR_{macro.upper()} \\", file=sby_file)
            for custom_csr in App.config.custom_csrs:
                name = custom_csr.name
                addr = custom_csr.addr
                levels = custom_csr.modes
                if macro == "indices":
                    for level in ["m", "s", "u"]:
                        if level in levels:
                            macro_string = fstring.format(level=level, name=name, index=addr)
                        else:
                            macro_string = fstring.format(level=level, name=name, index=0xFFF)
                        print(macro_string, file=sby_file)
                else:
                    for signal in ["rmask", "wmask", "rdata", "wdata"]:
                        macro_string = fstring.format(csr=name, signal=signal)
                        print(macro_string, file=sby_file)
            print("", file=sby_file)
