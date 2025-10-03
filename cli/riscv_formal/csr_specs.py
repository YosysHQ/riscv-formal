from __future__ import annotations
import functools
from yosys_mau.source_str import report
import riscv_formal.config


def mask_bits(test: str, bits: "list[int]", mask_len: int, invert=False):
    mask = functools.reduce(lambda x, y: x | 1 << y, bits, 0)
    return f"{test}_mask={'~' if invert else ''}{mask_len}'b{mask:0{mask_len}b}"


def extend_config_with_csr_spec(config: riscv_formal.config.RvfConfig):
    from riscv_formal.config import CsrConfig, IllegalCsrConfig

    xlen = config.options.isa.xlen

    def csr_line(name, *tests: str):
        csr = config.csrs.configs.setdefault(name, CsrConfig(name, {}))
        for test in tests:
            csr.parse_and_add_test(test)

    def illegal_csr_line(*items: str):
        config.illegal_csrs.append(IllegalCsrConfig.parse(" ".join(map(str, items))))

    match config.options.csr_spec:
        case None:
            return
        case "1.12":
            csr_line("mvendorid", "const")
            csr_line("marchid", "const")
            csr_line("mimpid", "const")
            csr_line("mhartid", "const")
            csr_line("mconfigptr", "const")
            csr_line(
                "mstatus",
                mask_bits(
                    "zero",
                    [0, 2, 4, *range(23, 31)] + ([31, *range(38, 63)] if xlen == 64 else []),
                    xlen,
                ),
            )
            csr_line(
                "misa",
                mask_bits(
                    "zero",
                    [6, 10, 11, 14, 17, 19, 22, 24, 25, *range(26, xlen - 2)],
                    xlen,
                ),
            )
            csr_line("mie")
            csr_line("mtvec")
            csr_line("mscratch", "any")
            csr_line("mepc")
            csr_line("mcause")
            csr_line("mtval")
            csr_line("mip")
            csr_line("mcycle", "inc")
            csr_line("minstret", "inc")

            for name in ["mhpmcounter", "mhpmevent"]:
                for i in range(3, 32):
                    csr_line(f"{name}{i}")

            restricted_csrs = {
                "medeleg": ("s", "302", []),
                "mideleg": ("s", "303", []),
                "mcounteren": ("u", "306", []),
                "mstatush": ("32", "310", [mask_bits("zero", [4, 5], xlen, invert=True)]),
                "mtinst": ("h", "34A", []),
                "mtval2": ("h", "34B", []),
                "menvcfg": ("u", "30A", []),
                "menvcfgh": ("u", "31A", []),  # u-mode only *and* 32bit only
            }

            for name, data in restricted_csrs.items():
                if data[0] in config.options.isa.mods:
                    csr_line(name, *data[2])
                else:
                    illegal_csr_line(data[1], "m", "rw")

        case spec:
            raise report.InputError(spec, f"unsupport CSR spec {spec!r}")
