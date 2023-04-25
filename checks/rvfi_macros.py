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
        self._cw = max((len(width) for width, name in self.signals), default=0)
        self._cn = max((len(name) for width, name in self.signals), default=0)
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
            elif s == "channel_conn":
                return f"{self.name}_CHANNEL_CONN{extra.upper()}(_idx)"
            else:
                return f"{self.name}_{s.upper()}{extra.upper()}"
        else:
            if s == "channel":
                return f"{self.name}_channel{extra}(_idx)"
            elif s == "channel_conn":
                return f"{self.name}_channel_conn{extra}(_idx)"
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
        print(self.commas([f"`define {self.macro_name_nosep('channel_outputs')}"] + [
            f"output {self.bitrange(width, no_channel=True)} rvfi_{name:<{self._cn}}"
            for width, name in self.signals
        ], [
            "`" + group.macro_name('channel_outputs') for group in self.append
        ]))
        print(self.commas([f"`define {self.macro_name_nosep('inputs')}"] + [
            f"input {self.bitrange(width)} rvfi_{name:<{self._cn}}"
            for width, name in self.signals
        ], [
            "`" + group.macro_name('inputs') for group in self.append
        ]))
        print(self.commas([f"`define {self.macro_name_nosep('channel_inputs')}"] + [
            f"input {self.bitrange(width, no_channel=True)} rvfi_{name:<{self._cn}}"
            for width, name in self.signals
        ], [
            "`" + group.macro_name('channel_inputs') for group in self.append
        ]))
        print(self.commas([f"`define {self.macro_name_nosep('conn')}"] + [
            f".rvfi_{name:<{self._cn}} (rvfi_{name:<{self._cn}})"
            for width, name in self.signals
        ], [
            "`" + group.macro_name('conn') for group in self.append
        ]))
        print(self.commas([f"`define {self.macro_name_nosep('channel_conn')}"] + [
            f".rvfi_{name:<{self._cn}} (rvfi_{name:<{self._cn}} {self.channel_idx(width)})"
            for width, name in self.signals
        ], [
            "`" + group.macro_name('channel_conn') for group in self.append
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
                "`" + group.macro_name('conn32' if group._has_conn32 else 'conn') for group in self.append
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
            print(f"`define {self.macro_name('channel_outputs')} , `{self.macro_name_nosep('channel_outputs')}")
            print(f"`define {self.macro_name('channel_inputs')} , `{self.macro_name_nosep('channel_inputs')}")
            print(f"`define {self.macro_name('channel_conn')}  , `{self.macro_name_nosep('channel_conn')}")
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


@dataclass
class Csr:
    len: str
    name: str
    mindex: Optional[int] = None
    sindex: Optional[int] = None
    uindex: Optional[int] = None

    hmindex: Optional[int] = None
    hsindex: Optional[int] = None
    huindex: Optional[int] = None


csrs = [
    Csr("xlen", "fflags",             None,  None,  None),
    Csr("xlen", "frm",                None,  None,  None),
    Csr("xlen", "fcsr",               None,  None,  None),
    Csr("xlen", "mvendorid",         0xF11,  None,  None),
    Csr("xlen", "marchid",           0xF12,  None,  None),
    Csr("xlen", "mimpid",            0xF13,  None,  None),
    Csr("xlen", "mhartid",           0xF14,  None,  None),
    Csr("xlen", "mconfigptr",        0xF15,  None,  None),
    Csr("xlen", "mstatus",           0x300,  None,  None),
    Csr("xlen", "mstatush",          0x310,  None,  None),
    Csr("xlen", "misa",              0x301,  None,  None),
    Csr("xlen", "medeleg",           0x302,  None,  None),
    Csr("xlen", "mideleg",           0x303,  None,  None),
    Csr("xlen", "mie",               0x304,  None,  None),
    Csr("xlen", "mtvec",             0x305,  None,  None),
    Csr("xlen", "mcounteren",        0x306,  None,  None),
    Csr("xlen", "mscratch",          0x340,  None,  None),
    Csr("xlen", "mepc",              0x341,  None,  None),
    Csr("xlen", "mcause",            0x342,  None,  None),
    Csr("xlen", "mtval",             0x343,  None,  None),
    Csr("xlen", "mip",               0x344,  None,  None),
    Csr("xlen", "mtinst",            0x34A,  None,  None),
    Csr("xlen", "mtval2",            0x34B,  None,  None),
    Csr("xlen", "mcountinhibit",     0x320,  None,  None),
    Csr("xlen", "menvcfg",           0x30A,  None,  None),
    Csr("xlen", "menvcfgh",          0x31A,  None,  None),
    *(
        Csr("xlen", f"pmpcfg{i}",    0x3A0 + i,  None,  None)
        for i in range(16)
    ),
    *(
        Csr("xlen", f"pmpaddr{i}",   0x3B0 + i,  None,  None)
        for i in range(64)
    ),
    *(
        Csr("xlen", f"mhpmevent{i}",  0x320 + i,  None,  None)
        for i in range(3, 32)
    ),
    Csr("64",   "mcycle",            0xB00,  None, 0xC00,
                                     0xB80,  None, 0xC80),
    Csr("64",   "time",               None,  None, 0xC01,
                                      None,  None, 0xC01),
    Csr("64",   "minstret",          0xB02,  None, 0xC02,
                                     0xB82,  None, 0xC82),
    *(
        Csr("64", f"mhpmcounter{i}", 0xB00 + i, None, 0xC00 + i,
                                     0xB80 + i, None, 0xC80 + i)
        for i in range(3, 32)
    ),
]

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
print("`ifndef RISCV_FORMAL_IOADDR")
print("`define RISCV_FORMAL_IOADDR(addr) 1")
print("`endif")
print("")
print("`define rvformal_addr_valid(a) (`RISCV_FORMAL_VALIDADDR(a))")
print("`define rvformal_addr_io(a) (`rvformal_addr_valid(a) && (`RISCV_FORMAL_IOADDR(a)))")
print("`define rvformal_addr_eq(a, b) ((`rvformal_addr_valid(a) == `rvformal_addr_valid(b)) && (!`rvformal_addr_valid(a) || (a == b)))")
print("`define rvformal_addr_eq_io(a, b) (`rvformal_addr_io(a) ? `rvformal_addr_io(b) : `rvformal_addr_eq(a, b))")
print("")

csr_groups = []

def csr_index(index):
    if index is None:
        return "12'hFFF"
    else:
        return f"12'h{index:03X}"

for csr in csrs:
    width = {"64": "64", "xlen": "`RISCV_FORMAL_XLEN"}[csr.len]
    csr_groups.append(Group(
        condition=f"RISCV_FORMAL_CSR_{csr.name.upper()}",
        name=f"rvformal_csr_{csr.name}",
        channels="`RISCV_FORMAL_NRET",
        csr_conn32=csr.len == "64",
        signals=[
            (width, f"csr_{csr.name}_rmask"),
            (width, f"csr_{csr.name}_wmask"),
            (width, f"csr_{csr.name}_rdata"),
            (width, f"csr_{csr.name}_wdata"),
        ]
    ).print_macros())

    print(f"`define rvformal_csr_{csr.name}_indices \\")
    print(f"localparam [11:0] csr_mindex_{csr.name} = {csr_index(csr.mindex)}; \\")
    print(f"localparam [11:0] csr_sindex_{csr.name} = {csr_index(csr.sindex)}; \\")
    print(f"localparam [11:0] csr_uindex_{csr.name} = {csr_index(csr.uindex)}; \\")
    if csr.len == "64":
        print(f"localparam [11:0] csr_mindex_{csr.name}h = {csr_index(csr.hmindex)}; \\")
        print(f"localparam [11:0] csr_sindex_{csr.name}h = {csr_index(csr.hsindex)}; \\")
        print(f"localparam [11:0] csr_uindex_{csr.name}h = {csr_index(csr.huindex)}; \\")
    print()

print("`define RVFI_INDICES \\")
for csr in csrs:
    print(f"`rvformal_csr_{csr.name}_indices \\")
print("`rvformal_custom_csr_indices")
print()

# Do not print this group, we'll use user macros when defined instead
custom_csr = Group(name="rvformal_custom_csr", signals=[], channels="`RISCV_FORMAL_NRET",)

for macro in ["inputs", "wires", "conn", "channel", "signals", "outputs", "indices"]:
    print(f"`ifdef RISCV_FORMAL_CUSTOM_CSR_{macro.upper()}")
    if (macro == "channel"):
        print(f"`define rvformal_custom_csr_{macro}(_idx) `RISCV_FORMAL_CUSTOM_CSR_{macro.upper()}(_idx)")
        print(f"`else")
        print(f"`define rvformal_custom_csr_{macro}(_idx)")
    else:
        print(f"`define rvformal_custom_csr_{macro} `RISCV_FORMAL_CUSTOM_CSR_{macro.upper()}")
        print(f"`else")
        print(f"`define rvformal_custom_csr_{macro}")
    print(f"`endif")

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

group_fault = Group(
    condition="RISCV_FORMAL_MEM_FAULT",
    name="rvformal_mem_fault",
    channels="`RISCV_FORMAL_NRET",
    signals=[
        ("                 1  ", "mem_fault"),
        ("`RISCV_FORMAL_XLEN/8", "mem_fault_rmask"),
        ("`RISCV_FORMAL_XLEN/8", "mem_fault_wmask"),
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
    append = [group_extamo, group_rollback, group_fault, *csr_groups, custom_csr]
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
        ("                   1  ", "bus_fault"),
        ("  `RISCV_FORMAL_XLEN  ", "bus_addr "),
        ("`RISCV_FORMAL_BUSLEN/8", "bus_rmask"),
        ("`RISCV_FORMAL_BUSLEN/8", "bus_wmask"),
        ("`RISCV_FORMAL_BUSLEN  ", "bus_rdata"),
        ("`RISCV_FORMAL_BUSLEN  ", "bus_wdata"),
    ],
).print_macros()
