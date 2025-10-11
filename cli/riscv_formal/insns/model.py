from dataclasses import dataclass, field
from typing import Optional, ClassVar, Callable, Iterable
from textwrap import dedent

from riscv_formal.generic_checker import GenericChecker
from ..rvfi import Observer
from ..named_set import NamedSet


@dataclass
class Instruction_format:
    name: Optional[str] = None
    insn_parts: list[tuple[str, int]] = field(default_factory=list)
    imm: Optional[str] = None


@dataclass(kw_only=True)
class Instruction(GenericChecker):
    insn_parts: list[tuple[str, int]] | Instruction_format
    opcode: str

    result: Optional[str] = None
    next_pc: Optional[str] = None
    extension: Optional[str] = None
    shamt: Optional[bool] = None
    sign_extend_from: Optional[int] = None
    zero_extend_from: Optional[int] = None
    read_pc: Optional[bool] = None
    
    op_values: dict[str, str] = field(default_factory=dict)
    raw_code: list[str] = field(default_factory=list)
    spec_map: dict[str, str] = field(default_factory=dict)
    check_valid: list[str] = field(default_factory=list)
    imm: Optional[bool | str] = None
    xlen_min: int = 32
    xlen_max: int = 128
    ilen: int = 32
    opcode_width: int = 7

    _default_pc_increment: str = "rvfi_pc_rdata + 4"
    _next_pc_check: str = "next_pc[1:0] != 0"

    registered_inputs: Optional[NamedSet[Observer]] = None
    registered_outputs: Optional[NamedSet[Observer]] = None

    registered_assigns: ClassVar[dict[str, Callable[['Instruction'], str]]] = {}
    registered_checks: ClassVar[set[str]] = set()

    @classmethod
    def register_assign(cls, name: str, method: Callable[['Instruction'], str]):
        cls.registered_assigns[name] = method

    @classmethod
    def register_check(cls, check: str):
        cls.registered_checks.add(check)

    def _default_inputs(self):
        # rvfi_insn_check.sv compliant inputs
        return NamedSet([
            Observer("valid", "1"),
            Observer("insn", "`RISCV_FORMAL_ILEN"),
            Observer("pc_rdata", "`RISCV_FORMAL_XLEN"),
            Observer("rs1_rdata", "`RISCV_FORMAL_XLEN"),
            Observer("rs2_rdata", "`RISCV_FORMAL_XLEN"),
            Observer("mem_rdata", "`RISCV_FORMAL_XLEN"),
        ])

    def _default_outputs(self):
        # rvfi_insn_check.sv compliant outputs
        return NamedSet([
            Observer("valid", "1"),
            Observer("trap", "1"),
            Observer("rs1_addr", "5"),
            Observer("rs2_addr", "5"),
            Observer("rd_addr", "5"),
            Observer("rd_wdata", "`RISCV_FORMAL_XLEN"),
            Observer("pc_wdata", "`RISCV_FORMAL_XLEN"),
            Observer("mem_addr", "`RISCV_FORMAL_XLEN"),
            Observer("mem_rmask", "`RISCV_FORMAL_XLEN/8"),
            Observer("mem_wmask", "`RISCV_FORMAL_XLEN/8"),
            Observer("mem_wdata", "`RISCV_FORMAL_XLEN"),
        ])

    def get_inputs(self):
        return self.registered_inputs if self.registered_inputs is not None else self._default_inputs()

    def get_outputs(self):
        return self.registered_outputs if self.registered_outputs is not None else self._default_outputs()

    def _inputs_used(self) -> set[str]:
        inputs = set([
            "valid",
            "insn",
        ])
        for used_reg in self._used_regs:
            if used_reg in self._maybe_sources:
                inputs.add(f"{used_reg}_rdata")
        if self.read_pc:
            inputs.add("pc_rdata")
        return inputs

    def _outputs_used(self) -> set[str]:
        outputs = set([
            "valid",
        ])
        for used_reg in self._used_regs:
            outputs.add(f"{used_reg}_addr")
            if used_reg in self._maybe_dests:
                outputs.add(f"{used_reg}_wdata")
        if self.next_pc:
            outputs.add("pc_wdata")
            outputs.add("trap")
        outputs.update(self.spec_map.keys())
        return outputs

    def select_inputs(self, observers: Iterable[Observer]):
        self.registered_inputs = NamedSet()
        inputs_used = self._inputs_used()
        for observer in observers:
            if observer.name in inputs_used:
                self.registered_inputs.add(observer)

    def select_outputs(self, observers: Iterable[Observer]):
        self.registered_outputs = NamedSet()
        outputs_used = self._outputs_used()
        for observer in observers:
            if observer.name in outputs_used:
                self.registered_outputs.add(observer)

    def _insn_fixup(self):
        if isinstance(self.insn_parts, Instruction_format):
            if isinstance(self.imm, bool):
                self.imm = self.insn_parts.imm
            self.insn_parts = self.insn_parts.insn_parts

    def _process_insn_parts(self):
        assert isinstance(self.insn_parts, list)
        self._insn_part_dict = dict(self.insn_parts)

    def _config_used_regs(self):
        self._maybe_sources = ["rs2", "rs1"]
        self._maybe_dests = ["rd"]
        self._used_regs = []
        for maybe_reg in self._maybe_sources + self._maybe_dests:
            if maybe_reg in self._insn_part_dict.keys():
                self._used_regs.append(maybe_reg)

    def _config_widths(self):
        self._result_width = self.sign_extend_from or self.zero_extend_from

    def __post_init__(self):
        self._insn_fixup()
        if isinstance(self.imm, bool):
            raise NotImplementedError()
        self._process_insn_parts()
        self._config_used_regs()
        self._config_widths()

    def valid_xlen(self, xlen: int) -> bool:
        return xlen >= self.xlen_min and xlen <= self.xlen_max

    def _v_xlen_check(self, xlen: int) -> None:
        # check valid xlen
        if not self.valid_xlen(xlen):
            raise NotImplementedError(f"{xlen} not in range ({self.xlen_min}, {self.xlen_max})")

    def _v_modname(self) -> str:
        # module name
        return f"rvfi_insn_{self.name}"

    def _v_io(self) -> str:
        io_sigs: list[str] = []
        for observer in self.get_inputs():
            io_sigs.append(f"input {observer.bitrange()} rvfi_{observer.name}")
        for observer in self.get_outputs():
            io_sigs.append(f"output {observer.bitrange()} spec_{observer.name}")
        return ",\n".join(io_sigs)

    def _v_insn_fmt(self) -> str:
        # insn decode
        upper = self.ilen
        insn_format = "// instruction format\n"
        assert isinstance(self.insn_parts, list)
        for part, width in self.insn_parts:
            lower = upper - width
            insn_format += f"wire [{width-1:2d}:0] insn_{part:<6} = rvfi_insn[{upper-1:2d}:{lower:2d}];\n"
            upper = lower
        if upper != 0:
            raise NotImplementedError(f"{upper} instruction bits unhandled")

        return insn_format

    def _v_insn_map(self, xlen: int) -> str:
        # combined instruction mapping
        insn_map = "// insn map\n"

        # shamt
        if self.shamt:
            result_width = self._result_width or xlen
            shift_width = (result_width-1).bit_length()
            insn_map += f"wire [{shift_width-1}:0] shamt = rvfi_rs2_rdata[{shift_width-1}:0];\n"

        # imm
        if self.imm:
            insn_map += f"wire [{xlen-1}:0] insn_imm = {self.imm};\n"

        insn_map += f"wire illinsn = "
        op_value_checks = []
        for key, bin in self.op_values.items():
            op_value_bits = self._insn_part_dict[key]
            try:
                int(bin, 2)
                bin_str = f"{op_value_bits}'b {bin}"
            except ValueError:
                bin_str = bin
            op_value_checks.append(f"(insn_{key} != {bin_str})")
        if len(op_value_checks):
            insn_map += " || ".join(op_value_checks) + ";"
        else:
            insn_map += "0;"

        return insn_map

    def _v_result(self, result_width: int, result: str) -> str:
        return f"wire [{result_width-1}:0] result = {result};"

    def _v_instantiation(self, xlen: int) -> str:
        instantiation = ""
        result_width = self._result_width or xlen

        # raw code injection
        for code_line in self.raw_code:
            code_line = code_line.replace("%RESULT_WIDTH%", str(result_width))
            instantiation += code_line + "\n"
        if self.result:
            instantiation += self._v_result(result_width, self.result) + "\n"
        if self.next_pc:
            instantiation += f"wire [{xlen-1}:0] next_pc = {self.next_pc};\n"

        return instantiation

    def _v_spec_value(self, spec_sig: str, xlen: int) -> Optional[str]:
        if spec_sig == "pc_wdata":
            if self.next_pc:
                return "next_pc"
            else:
                return self._default_pc_increment
        elif spec_sig == "valid":
            try:
                int(self.opcode, 2)
                opcode = f"{self.opcode_width}'b {self.opcode}"
            except ValueError:
                opcode = self.opcode
            val = f"rvfi_valid && !illinsn && insn_opcode == {opcode}"
            for check in self.check_valid:
                val += f" && ({check})"
            for check in self.registered_checks:
                val += f" && ({check})"
            return val
        elif spec_sig == "trap" and self.next_pc:
            return self._next_pc_check
        else:
            return "0"

    def _v_spec_mapping(self, xlen: int) -> str:
        # map spec values
        spec_mapping = "// spec mapping\n"
        spec_map: dict[str, str] = self.spec_map.copy()
        spec_sigs = self.get_outputs().names()
        for spec_sig in spec_map.keys():
            if spec_sig not in spec_sigs:
                raise NotImplementedError(f"spec_sig {spec_sig}")

        for used_reg in self._used_regs:
            spec_map[f"{used_reg}_addr"] = f"insn_{used_reg}"
            if used_reg in self._maybe_dests:
                extend_from = self.sign_extend_from or self.zero_extend_from or 0
                if extend_from:
                    funct = "signed" if self.sign_extend_from else "unsigned"
                    result = f"${funct}(result[0+:{extend_from}])"
                else:
                    result = "result"
                spec_map[f"{used_reg}_wdata"] = f"spec_{used_reg}_addr ? {result} : 0"

        for assign in self.registered_assigns.values():
            spec_mapping += f"{assign(self)}\n"

        for spec_sig in spec_sigs:
            if spec_sig not in spec_map:
                spec_value = self._v_spec_value(spec_sig, xlen)
                if spec_value is not None:
                    spec_map[spec_sig] = spec_value

        for spec_sig, spec_val in spec_map.items():
            spec_mapping += f"assign spec_{spec_sig} = {spec_val};\n"

        return spec_mapping

    def _v_checks(self, xlen: int) -> None:
        super()._v_checks()
        self._v_xlen_check(xlen)

    def _v_body(self, xlen: int) -> str:
        v_str = self._v_format_block(self._v_insn_fmt())
        v_str += self._v_format_block(self._v_insn_map(xlen))
        v_str += self._v_format_block(self._v_instantiation(xlen))
        v_str += self._v_format_block(self._v_spec_mapping(xlen))
        return v_str

    def to_verilog(self, xlen: int):
        return super().to_verilog(xlen=xlen)

    def included_in(self, isa_mods: Iterable[str]) -> bool:
        if self.extension is None:
            return False
        for ext in self.extension.split():
            if ext in isa_mods:
                return True
        return False

@dataclass(kw_only=True)
class MemoryInstruction(Instruction):
    mem_addr: str
    mem_bytes: int
    mem_wdata: Optional[str] = None

    def _inputs_used(self) -> set[str]:
        inputs = super()._inputs_used()
        if not self.mem_wdata:
            inputs.add("mem_rdata")
        return inputs

    def _outputs_used(self) -> set[str]:
        outputs = super()._outputs_used()
        outputs.add("mem_addr")
        outputs.add("trap")
        if self.mem_wdata:
            outputs.add("mem_wmask")
            outputs.add("mem_wdata")
        else:
            outputs.add("mem_rmask")
        return outputs

    def _v_instantiation(self, xlen: int):
        result_width = self._result_width or xlen

        # memory alignment
        v_str = "`ifdef RISCV_FORMAL_ALIGNED_MEM\n"
        v_str += f"wire [{xlen-1}:0] addr = {self.mem_addr};\n"
        v_str += f"wire [{xlen-1}:0] spec_addr = addr & ~({xlen}/8-1);\n"
        v_str += f"wire [{int(xlen/8)-1}:0] spec_mem_mask = ((1 << {self.mem_bytes})-1) << (addr-spec_addr);\n"
        v_str += f"wire trap = (addr & ({self.mem_bytes}-1)) != 0;\n"
        if self.mem_wdata:
            v_str += f"wire [{xlen-1}:0] mem_wdata = {self.mem_wdata} << (8*(addr-spec_addr));\n"
        else:
            v_str += f"wire [{result_width-1}:0] mem_rdata = rvfi_mem_rdata >> (8*(addr-spec_addr));\n"
        v_str += "`else\n"
        v_str += f"wire [{xlen-1}:0] addr = {self.mem_addr};\n"
        v_str += f"wire [{xlen-1}:0] spec_addr = addr;\n"
        v_str += f"wire [{int(xlen/8)-1}:0] spec_mem_mask = ((1 << {self.mem_bytes})-1);\n"
        v_str += f"wire trap = 0;\n"
        if self.mem_wdata:
            v_str += f"wire [{self.mem_bytes*8-1}:0] mem_wdata = {self.mem_wdata};\n"
        else:
            v_str += f"wire [{result_width-1}:0] mem_rdata = rvfi_mem_rdata;\n"
        v_str += "`endif\n"

        return v_str + super()._v_instantiation(xlen)

    def _v_spec_value(self, spec_sig: str, xlen: int) -> Optional[str]:
        if spec_sig == "mem_addr":
            return "spec_addr"
        elif spec_sig == "mem_rmask" and not self.mem_wdata:
            return "spec_mem_mask"
        elif spec_sig == "mem_wmask" and self.mem_wdata:
            return "spec_mem_mask"
        elif spec_sig == "mem_wdata" and self.mem_wdata:
            return "mem_wdata"
        elif spec_sig == "trap":
            return "trap"
        else:
            return super()._v_spec_value(spec_sig, xlen)

@dataclass(kw_only=True)
class AltopsInstruction(Instruction):
    def _alt_vars(self) -> list[str]:
        return []

    def _altops_fixup(self) -> None:
        for alt_var in self._alt_vars():
            alt_val = self.__getattribute__(alt_var)
            if isinstance(alt_val, int):
                self.__dict__[alt_var] = hex(alt_val)

    def __post_init__(self):
        super().__post_init__()
        self._altops_fixup()

    def _get_alt_result_and_mask(self) -> Optional[tuple[str, str | int]]:
        return None

    def _mask_alt_result(self) -> Optional[str]:
        try:
            alt_result, alt_mask = self._get_alt_result_and_mask()
        except ValueError:
            return None
        
        if isinstance(alt_mask, str):
            alt_mask = int(alt_mask, 16)

        return f"({alt_result}) ^ 64'h{alt_mask:016x}"

    def _v_result(self, result_width: int, result: str) -> str:
        result_str = super()._v_result(result_width, result)

        masked_alt_result = self._mask_alt_result()
        if masked_alt_result is None:
            return result_str

        alt_str = super()._v_result(result_width, masked_alt_result)
        return dedent(f"""\
            `ifdef RISCV_FORMAL_ALTOPS
                {alt_str}
            `else
                {result_str}
            `endif""")
