from dataclasses import dataclass, field
from textwrap import dedent, indent
from typing import Callable, ClassVar, Optional

from . import GenericChecker
from ..insns import Instruction
from ..rvfi import (
    Observer,
    SpeculativeObserver,
    ZeroedObserver,
    SpeculativeEvaluation,
)

@dataclass(kw_only=True)
class InstructionChecker(GenericChecker):
    instructions: dict[str, Instruction] = field(default_factory=dict)
    observers: dict[str, Observer] = field(default_factory=dict)

    defined_checks: list[SpeculativeEvaluation] = field(default_factory=list)

    registered_checks: ClassVar[list[SpeculativeEvaluation]] = []
    registered_verilog: ClassVar[list[str]] = []
    registered_speculators: ClassVar[dict[str, tuple[SpeculativeObserver, Callable[[Instruction], Optional[str]]]]] = {}
    registered_hw_traps: ClassVar[dict[str, Callable[[dict[str, Observer]], str]]] = {}

    def configure_io(self):
        for insn in self.instructions.values():
            insn.select_inputs(self.observers.values())
            insn.select_outputs([o for o in self.observers.values() if isinstance(o, SpeculativeObserver)])

    @classmethod
    def register_check(cls, check: SpeculativeEvaluation):
        cls.registered_checks.append(check)

    @classmethod
    def register_verilog(cls, verilog: str):
        cls.registered_verilog.append(verilog)

    @classmethod
    def register_speculator(cls,
        spec_obs: SpeculativeObserver,
        speculator: Callable[[Instruction], Optional[str]],
    ):
        cls.registered_speculators[spec_obs.name] = (spec_obs, speculator)

    @classmethod
    def register_hw_trap(cls, condition: str, handler: Callable[[dict[str, Observer]], str]):
        cls.registered_hw_traps[condition] = handler

    def _v_io(self) -> str:
        # macro defined RVFI inputs
        return dedent("""\
            input clock, reset, check,
            `RVFI_INPUTS""")

    def _v_instantiation(self) -> str:
        v_str = ""

        # instantiate insns
        insn_inst_map: list[str] = []
        spec_map: dict[str, tuple[Instruction, list[str]]] = {}
        for mnemonic, insn in self.instructions.items():
            insn_prefix = "insn_" + mnemonic

            spec_list: list[str] = []
            spec_map[insn_prefix] = (insn, spec_list)

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

        # generate speculative signals
        # name: (bitrange, default_value)
        spec_obs: dict[str, SpeculativeObserver] = {}
        for name, obs in self.observers.items():
            if isinstance(obs, SpeculativeObserver):
                spec_obs[name] = obs
        for name, (obs, _) in self.registered_speculators.items():
            spec_obs[name] = obs

        for name, obs in spec_obs.items():
            v_str += f"(* keep *) reg {obs.bitrange()} spec_{name};\n"
        v_str += "always @* begin\n"
        for name, obs in spec_obs.items():
            v_str += f"    spec_{name} <= {obs.spec_value};\n"

        # assign speculative values for valid insn
        is_first = True
        for insn_prefix, (insn, spec_list) in spec_map.items():
            conditional = "    if" if is_first else " else if"
            is_first = False
            v_str += f"{conditional} ({insn_prefix}_spec_valid) begin\n        spec_valid <= 1;\n"
            for name in spec_list:
                v_str += f"        spec_{name} <= {insn_prefix}_spec_{name};\n"
            for name, (_, speculator) in self.registered_speculators.items():
                value = speculator(insn)
                if value is not None:
                    v_str += f"        spec_{name} <= {value};\n"
            v_str += "    end"
        v_str += "\nend\n"

        if self.registered_verilog:
            v_str += "\n"
            v_str += "\n\n".join(self.registered_verilog)
            v_str += "\n"

        return v_str

    def _v_spec_check(self) -> str:
        # initialize speculative check lists
        handled_observers: set[str] = set(["valid", "trap"])
        spec_pre_hw_trap: list[str] = [
            "assume (spec_valid);",
        ]
        spec_pre_trap: list[str] = [
            "assert (spec_trap == rvfi.trap);",
        ]
        spec_untrapped: list[str] = []

        # load defined checks
        for spec in self.registered_checks + self.defined_checks:
            handled_observers.update(spec.speculates_about)
            if spec.ignore_trap:
                spec_pre_trap.append(spec.evaluation)
            else:
                spec_untrapped.append(spec.evaluation)

        # use default checks for unhandled observers
        for name, obs in self.observers.items():
            if isinstance(obs, SpeculativeObserver) and name not in handled_observers:
                spec_untrapped.append(f"assert(spec_{name} == rvfi.{name});")

        # hw traps
        trapdent = "    "*5
        hw_trap_str = trapdent
        for condition, callback in self.registered_hw_traps.items():
            hw_trap_str += f"if ({condition}) begin\n"
            hw_trap_str += indent(callback(self.observers), trapdent + "    ")
            hw_trap_str += f"\n{trapdent}end else "

        # bring it together
        pre_hw_trap_str = indent("\n".join(spec_pre_hw_trap), "    "*5)
        pre_trap_str = indent("\n".join(spec_pre_trap), "    "*6)
        untrapped_str = indent("\n".join(spec_untrapped), "    "*7)
        v_str = dedent(f"""\
            integer i;
            always @* begin
                if (!reset && check) begin\n{pre_hw_trap_str}\n{hw_trap_str}begin\n{pre_trap_str}
                        if (!spec_trap) begin\n{untrapped_str}
                        end
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
