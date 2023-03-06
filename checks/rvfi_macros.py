#!/usr/bin/env python3
#
# Copyright (C) 2017  Claire Xenia Wolf <claire@yosyshq.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

@dataclass
class Group:
    name: str
    signals: List[Tuple[str, str]]
    channels: Optional[str] = None
    condition: Optional[str] = None
    nosep: bool = False
    csr_conn32: bool = False
    append: List['Group'] = field(default_factory=list)

    def __post_init__(self):
        self._cw = max(len(width) for width, name in self.signals)
        self._cn = max(len(name) for width, name in self.signals)
        self._has_conn32 = self.csr_conn32 or any(g._has_conn32 for g in self.append)

    def bitrange(self, width, no_channel=False):
        if no_channel or self.channels is None:
            if str(width).strip() == '1':
                return f"[{'':>{self._cw}}   0 : 0]"
            else:
                return f"[{width:>{self._cw}} - 1 : 0]"
        elif str(width).strip() == '1':
            return f"[{self.channels}   {'':>{self._cw}} - 1 : 0]"
        else:
            return f"[{self.channels} * {width:>{self._cw}} - 1 : 0]"

    def channel_idx(self, width):
        if str(width).strip() == '1':
            return f"[ _idx   {'':>{self._cw}}  +: {width:>{self._cw}}]"
        else:
            return f"[(_idx)*({width:>{self._cw}}) +: {width:>{self._cw}}]"

    def macro_name(self, s, extra=""):
        if self.name.upper() == self.name:
            if s == "channel":
                return f"{self.name}_GETCHANNEL{extra.upper()}(_idx)"
            else:
                return f"{self.name}_{s.upper()}{extra.upper()}"
        else:
            if s == "channel":
                return f"{self.name}_channel{extra}(_idx)"
            else:
                return f"{self.name}_{s}{extra}"

    def macro_name_nosep(self, s):
        if self.nosep:
            return self.macro_name(s, extra="_nosep")
        else:
            return self.macro_name(s)

    def commas(self, parts, suffix=()):
        if (self.condition and not self.nosep) or len(parts) < 2:
            return " \\\n  ".join([", \\\n  ".join(parts), *suffix])
        else:
            first, *parts = parts
            return " \\\n  ".join([first, ", \\\n  ".join(parts), *suffix])

    def high_name(self, name):
        parts = name.split('_')
        parts[-2] += 'h'
        return '_'.join(parts)

    def print_macros(self):
        if self.condition:
            print(f"`ifdef {self.condition}")
        print(self.commas([f"`define {self.macro_name('wires')}"], [
            f"(* keep *) wire {self.bitrange(width)} rvfi_{name:<{self._cn}};"
            for width, name in self.signals
        ] + [
            "`" + group.macro_name('wires') for group in self.append
        ]))
        print(self.commas([f"`define {self.macro_name_nosep('outputs')}"] + [
            f"output {self.bitrange(width)} rvfi_{name:<{self._cn}}"
            for width, name in self.signals
        ], [
            "`" + group.macro_name('outputs') for group in self.append
        ]))
        print(self.commas([f"`define {self.macro_name_nosep('inputs')}"] + [
            f"input {self.bitrange(width)} rvfi_{name:<{self._cn}}"
            for width, name in self.signals
        ], [
            "`" + group.macro_name('inputs') for group in self.append
        ]))
        print(self.commas([f"`define {self.macro_name_nosep('conn')}"] + [
            f".rvfi_{name:<{self._cn}} (rvfi_{name:<{self._cn}})"
            for width, name in self.signals
        ], [
            "`" + group.macro_name('conn') for group in self.append
        ]))
        if self.csr_conn32:
            cn = self._cn + self.csr_conn32
            print(self.commas([f"`define {self.macro_name_nosep('conn32')}"] + [
                f".rvfi_{name:<{cn}} (rvfi_{name:<{self._cn}}[31: 0])"
                for width, name in self.signals
            ] + [
                f".rvfi_{self.high_name(name):<{cn}} (rvfi_{name:<{self._cn}}[63:32])"
                for width, name in self.signals
            ], [
                "`" + group.macro_name('conn32') for group in self.append
            ]))
        elif self._has_conn32:
            print(self.commas([f"`define {self.macro_name_nosep('conn32')}"] + [
                f".rvfi_{name:<{self._cn}} (rvfi_{name:<{self._cn}})"
                for width, name in self.signals
            ], [
                "`" + group.macro_name('conn32') for group in self.append if group._has_conn32
            ]))
        if self.channels:
            print(self.commas([f"`define {self.macro_name('channel')}"], [
                f"wire {self.bitrange(width, True)} {name:<{self._cn}} = "
                f"rvfi_{name:<{self._cn}} {self.channel_idx(width)};"
                for width, name in self.signals
            ] + [
                "`" + group.macro_name('channel') for group in self.append if group.channels
            ]))
            print(self.commas([f"`define {self.macro_name('signals')}"], [
                f"`RISCV_FORMAL_CHANNEL_SIGNAL({self.channels}, {width:>{self._cw}}, {name:<{self._cn}})"
                for width, name in self.signals
            ] + [
                "`" + group.macro_name('signals') for group in self.append if group.channels
            ]))

        if self.nosep:
            print(f"`define {self.macro_name('outputs')} , `{self.macro_name_nosep('outputs')}")
            print(f"`define {self.macro_name('inputs')} , `{self.macro_name_nosep('inputs')}")
            print(f"`define {self.macro_name('conn')}  , `{self.macro_name_nosep('conn')}")
            if self._has_conn32:
                print(f"`define {self.macro_name('conn32')}")


        if self.condition:
            print("`else")
            print(f"`define {self.macro_name('wires')}")
            print(f"`define {self.macro_name('outputs')}")
            print(f"`define {self.macro_name('inputs')}")
            print(f"`define {self.macro_name('conn')}")
            if self._has_conn32:
                print(f"`define {self.macro_name('conn32')}")
            if self.channels:
                print(f"`define {self.macro_name('channel')}")
            print("`endif")


        if self.name.upper() == self.name:
            print("")
            print(f"`define {self.name}_CHANNEL(_name, _idx) \\")
            print("generate if(1) begin:_name \\")
            print(f"  `{self.name}_GETCHANNEL(_idx) \\")
            print("end endgenerate")

        return self


print("// Generated by rvfi_macros.py")
print("")
print("`ifdef YOSYS")
print("`define rvformal_rand_reg rand reg")
print("`define rvformal_rand_const_reg rand const reg")
print("`else")
print("`ifdef SIMULATION")
print("`define rvformal_rand_reg reg")
print("`define rvformal_rand_const_reg reg")
print("`else")
print("`define rvformal_rand_reg wire")
print("`define rvformal_rand_const_reg reg")
print("`endif")
print("`endif")
print("")
print("`ifndef RISCV_FORMAL_VALIDADDR")
print("`define RISCV_FORMAL_VALIDADDR(addr) 1")
print("`endif")
print("")
print("`define rvformal_addr_valid(a) (`RISCV_FORMAL_VALIDADDR(a))")
print("`define rvformal_addr_eq(a, b) ((`rvformal_addr_valid(a) == `rvformal_addr_valid(b)) && (!`rvformal_addr_valid(a) || (a == b)))")

csrs_xlen = list()
csrs_64 = list()

csrs_xlen += "fflags frm fcsr".split()
csrs_xlen += "mvendorid marchid mimpid mhartid".split()
csrs_xlen += "mstatus misa medeleg mideleg mie mtvec mcounteren".split()
csrs_xlen += "mscratch mepc mcause mtval mip".split()
csrs_xlen += "pmpcfg0 pmpcfg1 pmpcfg2 pmpcfg3".split()
csrs_xlen += "pmpaddr0 pmpaddr1 pmpaddr2 pmpaddr3".split()
csrs_xlen += "pmpaddr4 pmpaddr5 pmpaddr6 pmpaddr7".split()
csrs_xlen += "pmpaddr8 pmpaddr9 pmpaddr10 pmpaddr11".split()
csrs_xlen += "pmpaddr12 pmpaddr13 pmpaddr14 pmpaddr15".split()

csrs_64 += "time mcycle minstret mhpmcounter3".split()
csrs_64 += "mhpmcounter4 mhpmcounter5 mhpmcounter6 mhpmcounter7".split()
csrs_64 += "mhpmcounter8 mhpmcounter9 mhpmcounter10 mhpmcounter11".split()
csrs_64 += "mhpmcounter12 mhpmcounter13 mhpmcounter14 mhpmcounter15".split()
csrs_64 += "mhpmcounter16 mhpmcounter17 mhpmcounter18 mhpmcounter19".split()
csrs_64 += "mhpmcounter20 mhpmcounter21 mhpmcounter22 mhpmcounter23".split()
csrs_64 += "mhpmcounter24 mhpmcounter25 mhpmcounter26 mhpmcounter27".split()
csrs_64 += "mhpmcounter28 mhpmcounter29 mhpmcounter30 mhpmcounter31".split()

csrs_xlen += "mcountinhibit mhpmevent3".split()
csrs_xlen += "mhpmevent4 mhpmevent5 mhpmevent6 mhpmevent7".split()
csrs_xlen += "mhpmevent8 mhpmevent9 mhpmevent10 mhpmevent11".split()
csrs_xlen += "mhpmevent12 mhpmevent13 mhpmevent14 mhpmevent15".split()
csrs_xlen += "mhpmevent16 mhpmevent17 mhpmevent18 mhpmevent19".split()
csrs_xlen += "mhpmevent20 mhpmevent21 mhpmevent22 mhpmevent23".split()
csrs_xlen += "mhpmevent24 mhpmevent25 mhpmevent26 mhpmevent27".split()
csrs_xlen += "mhpmevent28 mhpmevent29 mhpmevent30 mhpmevent31".split()

all_csrs = csrs_xlen + csrs_64

csr_groups = []

for csr in all_csrs:
    width = "64" if csr in csrs_64 else "`RISCV_FORMAL_XLEN"
    csr_groups.append(Group(
        condition=f"RISCV_FORMAL_CSR_{csr.upper()}",
        name=f"rvformal_csr_{csr}",
        channels="`RISCV_FORMAL_NRET",
        csr_conn32=csr in csrs_64,
        signals=[
            (width, f"csr_{csr}_rmask"),
            (width, f"csr_{csr}_wmask"),
            (width, f"csr_{csr}_rdata"),
            (width, f"csr_{csr}_wdata"),
        ]
    ).print_macros())

group_rollback = Group(
    condition="RISCV_FORMAL_ROLLBACK",
    name="rvformal_rollback",
    signals=[
        (" 1", "rollback_valid"),
        ("64", "rollback_order"),
    ]
).print_macros()

group_extamo = Group(
    condition="RISCV_FORMAL_EXTAMO",
    name="rvformal_extamo",
    channels="`RISCV_FORMAL_NRET",
    signals=[
        ("1", "mem_extamo"),
    ]
).print_macros()

rvfi = Group(
    name="RVFI",
    channels="`RISCV_FORMAL_NRET",
    signals=[
        ("                 1  ", "valid    "),
        ("                64  ", "order    "),
        ("`RISCV_FORMAL_ILEN  ", "insn     "),
        ("                 1  ", "trap     "),
        ("                 1  ", "halt     "),
        ("                 1  ", "intr     "),
        ("                 2  ", "mode     "),
        ("                 2  ", "ixl      "),
        ("                 5  ", "rs1_addr "),
        ("                 5  ", "rs2_addr "),
        ("`RISCV_FORMAL_XLEN  ", "rs1_rdata"),
        ("`RISCV_FORMAL_XLEN  ", "rs2_rdata"),
        ("                 5  ", "rd_addr  "),
        ("`RISCV_FORMAL_XLEN  ", "rd_wdata "),
        ("`RISCV_FORMAL_XLEN  ", "pc_rdata "),
        ("`RISCV_FORMAL_XLEN  ", "pc_wdata "),
        ("`RISCV_FORMAL_XLEN  ", "mem_addr "),
        ("`RISCV_FORMAL_XLEN/8", "mem_rmask"),
        ("`RISCV_FORMAL_XLEN/8", "mem_wmask"),
        ("`RISCV_FORMAL_XLEN  ", "mem_rdata"),
        ("`RISCV_FORMAL_XLEN  ", "mem_wdata"),
    ],
    append = [group_extamo, group_rollback, *csr_groups]
).print_macros()

rvfi = Group(
    condition="RISCV_FORMAL_BUS",
    name="RVFI_BUS",
    channels="`RISCV_FORMAL_NBUS",
    nosep=True,
    signals=[
        ("                   1  ", "bus_valid"),
        ("                   1  ", "bus_insn "),
        ("                   1  ", "bus_data "),
        ("  `RISCV_FORMAL_XLEN  ", "bus_addr "),
        ("`RISCV_FORMAL_BUSLEN/8", "bus_rmask"),
        ("`RISCV_FORMAL_BUSLEN/8", "bus_wmask"),
        ("`RISCV_FORMAL_BUSLEN  ", "bus_rdata"),
        ("`RISCV_FORMAL_BUSLEN  ", "bus_wdata"),
    ],
).print_macros()
