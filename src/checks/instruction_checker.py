from dataclasses import dataclass, field
from textwrap import dedent, indent

from . import GenericChecker
from ..insns import Instruction
from ..rvfi import Observer, SpeculativeObserver, ZeroedObserver

@dataclass(kw_only=True)
class InstructionChecker(GenericChecker):
    instructions: dict[str, Instruction] = field(default_factory=dict)
    observers: dict[str, Observer] = field(default_factory=dict)

    def configure_io(self):
        for insn in self.instructions.values():
            insn.select_inputs(self.observers.values())
            insn.select_outputs([o for o in self.observers.values() if isinstance(o, SpeculativeObserver)])

    def _v_io(self) -> str:
        # macro defined RVFI inputs
        return dedent("""\
            input clock, reset, check,
            `RVFI_INPUTS""")

    def _v_rvfi_channel(self) -> str:
        return "`RVFI_CHANNEL(rvfi, `RISCV_FORMAL_CHANNEL_IDX)\n"

    def _v_instantiation(self) -> str:
        v_str = ""

        # instantiate insns
        insn_inst_map: list[str] = []
        spec_map = {}
        for mnemonic, insn in self.instructions.items():
            insn_prefix = "insn_" + mnemonic

            spec_map[insn_prefix] = spec_list = []

            # map observers to signals
            inst_sig_map: dict[str, str] = {}
            inst_sig_decls: list[str] = []
            for name, obs in insn.get_inputs().items():
                if isinstance(obs, ZeroedObserver):
                    #TODO: substitute insn specific signals in zero_condition
                    inst_sig = f"{insn_prefix}_{name}_or_zero"
                    inst_sig_map[f"rvfi_{name}"] = inst_sig
                    inst_sig_decls.append(f"(* keep *) wire {obs.bitrange()} {inst_sig} = {obs.zero_condition} ? 0 : rvfi.{name};")
                else:
                    inst_sig_map[f"rvfi_{name}"] = f"rvfi.{name}"
            for name, obs in insn.get_outputs().items():
                if isinstance(obs, SpeculativeObserver):
                    if name != "valid": spec_list.append(name)
                    inst_sig = f"{insn_prefix}_spec_{name}"
                    inst_sig_map[f"spec_{name}"] = inst_sig
                    inst_sig_decls.append(f"(* keep *) wire {obs.bitrange()} {inst_sig};")
                else:
                    raise NotImplementedError(type(obs))

            # compose instance
            insn_inst = '\n'.join(inst_sig_decls)
            insn_inst += f"\n{insn._v_modname()} {insn_prefix}_inst (\n"
            insn_inst += ',\n'.join(f"    .{sig} ({inst_sig})" for sig, inst_sig in inst_sig_map.items())
            insn_inst += "\n);\n"
            insn_inst_map.append(insn_inst)

        v_str += '\n'.join(insn_inst_map) + '\n'

        # assign speculative values for valid insn
        for name, obs in self.observers.items():
            if isinstance(obs, SpeculativeObserver):
                v_str += f"(* keep *) reg {obs.bitrange()} spec_{name};\n"
        v_str += "always @* begin\n"
        for name, obs in self.observers.items():
            if isinstance(obs, SpeculativeObserver):
                v_str += f"    spec_{name} <= {obs.spec_value};\n"
        is_first = True
        for insn_prefix, spec_list in spec_map.items():
            conditional = "    if" if is_first else " else if"
            is_first = False
            v_str += f"{conditional} ({insn_prefix}_spec_valid) begin\n        spec_valid <= 1;\n"
            for name in spec_list:
                v_str += f"        spec_{name} <= {insn_prefix}_spec_{name};\n"
            v_str += "    end"
        v_str += "\nend"

        return v_str

    def _v_spec_check(self) -> str:
        spec_body: list[str] = []
        for name, obs in self.observers.items():
            if isinstance(obs, SpeculativeObserver) and name not in ["valid", "trap"]:
                #TODO: maskable memory/byte enables
                #TODO: `rvformal_addr_eq addresses
                spec_body.append(f"assert(spec_{name} == rvfi.{name});")
        body_str = "\n".join(spec_body)
        v_str = dedent(f"""\
            integer i;
            always @* begin
                if (!reset && check) begin
                    assume(spec_valid);
                    if (rvfi.rs1_addr == 0)
                        assert(rvfi.rs1_rdata == 0);
                    if (rvfi.rs2_addr == 0)
                        assert(rvfi.rs2_rdata == 0);
                    assert (spec_trap == rvfi.trap);
                    if (!spec_trap) begin\n{indent(body_str, "                        ")}
                    end
                end
            end
            """
        )
        return v_str

    def _v_body(self) -> str:
        v_str = self._v_format_block(self._v_rvfi_channel())
        v_str += self._v_format_block(self._v_instantiation())
        v_str += self._v_format_block(self._v_spec_check())
        return v_str

    def to_verilog(self, xlen: int):
        v_str = ""
        for insn in self.instructions.values():
            v_str += insn.to_verilog(xlen) + '\n\n'
        return v_str + super().to_verilog()
