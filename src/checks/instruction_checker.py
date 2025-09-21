from dataclasses import dataclass, field
from textwrap import dedent, indent
from typing import Callable, ClassVar, Optional

from . import GenericGroupChecker
from ..insns import Instruction
from ..rvfi import (
    Observer,
    SpeculativeObserver,
    ZeroedObserver,
    SpeculativeEvaluation,
)
from ..named_set import NamedSet


@dataclass(kw_only=True)
class InstructionCheckerBase(GenericGroupChecker):
    instructions: NamedSet[Instruction] = field(default_factory=NamedSet)
    observers: NamedSet[Observer] = field(default_factory=NamedSet)

    registered_speculators: ClassVar[dict[str, tuple[SpeculativeObserver, Callable[[Instruction], Optional[str]]]]] = {}

    def configure_io(self):
        for insn in self.instructions:
            insn.select_inputs(self.observers)
            insn.select_outputs([o for o in self.observers if isinstance(o, SpeculativeObserver)])

    @classmethod
    def register_speculator(cls,
        spec_obs: SpeculativeObserver,
        speculator: Callable[[Instruction], Optional[str]],
    ):
        cls.registered_speculators[spec_obs.name] = (spec_obs, speculator)

    def _v_instantiation(self) -> str:
        v_str = ""

        # instantiate insns
        insn_inst_map: list[str] = []
        spec_map: dict[str, tuple[Instruction, list[str]]] = {}
        for insn in self.instructions:
            insn_prefix = "insn_" + insn.name

            spec_list: list[str] = []
            spec_map[insn_prefix] = (insn, spec_list)

            # map observers to signals
            inst_sig_map: dict[str, str] = {}
            inst_sig_decls: list[str] = []
            for obs in insn.get_inputs():
                if isinstance(obs, ZeroedObserver):
                    #TODO: substitute insn specific signals in zero_condition
                    inst_sig = f"{insn_prefix}_{obs.name}_or_zero"
                    inst_sig_map[f"rvfi_{obs.name}"] = inst_sig
                    inst_sig_decls.append(f"(* keep *) wire {obs.bitrange()} {inst_sig} = {obs.zero_condition} ? 0 : rvfi.{obs.name};")
                else:
                    inst_sig_map[f"rvfi_{obs.name}"] = f"rvfi.{obs.name}"
            for obs in insn.get_outputs():
                if isinstance(obs, SpeculativeObserver):
                    if obs.name != "valid": spec_list.append(obs.name)
                    inst_sig = f"{insn_prefix}_spec_{obs.name}"
                    inst_sig_map[f"spec_{obs.name}"] = inst_sig
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
        spec_obs: NamedSet[SpeculativeObserver] = NamedSet()
        for obs in self.observers:
            if isinstance(obs, SpeculativeObserver):
                spec_obs.add(obs)
        for obs, _ in self.registered_speculators.values():
            spec_obs.add(obs)

        for obs in spec_obs:
            v_str += f"(* keep *) reg {obs.bitrange()} spec_{obs.name};\n"
        v_str += "always @* begin\n"
        for obs in spec_obs:
            v_str += f"    spec_{obs.name} <= {obs.spec_value};\n"

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

        return v_str

    def _v_spec_check(self) -> str:
        raise NotImplementedError()

    def _v_body(self) -> str:
        v_str = self._v_format_block(self._v_rvfi_channel())
        v_str += self._v_format_block(self._v_instantiation())
        v_str += self._v_format_block(self._v_spec_check())
        return v_str

    def _subchecks(self) -> NamedSet[Instruction]:
        return self.instructions


@dataclass(kw_only=True)
class InstructionChecker(InstructionCheckerBase):
    defined_checks: list[SpeculativeEvaluation] = field(default_factory=list)

    registered_checks: ClassVar[list[SpeculativeEvaluation]] = []
    registered_verilog: ClassVar[list[str]] = []
    registered_hw_traps: ClassVar[dict[str, Callable[[NamedSet[Observer]], str]]] = {}

    @classmethod
    def register_check(cls, check: SpeculativeEvaluation):
        cls.registered_checks.append(check)

    @classmethod
    def register_verilog(cls, verilog: str):
        cls.registered_verilog.append(verilog)

    @classmethod
    def register_hw_trap(cls, condition: str, handler: Callable[[NamedSet[Observer]], str]):
        cls.registered_hw_traps[condition] = handler

    def _v_instantiation(self) -> str:
        v_str = super()._v_instantiation()

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
        for obs in self.observers:
            if isinstance(obs, SpeculativeObserver) and obs.name not in handled_observers:
                spec_untrapped.append(f"assert(spec_{obs.name} == rvfi.{obs.name});")

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


@dataclass(kw_only=True)
class CompleteISAChecker(InstructionCheckerBase):
    valid_opcodes: list[str] = field(default_factory=list)
    extra_valid_checks: list[str] = field(default_factory=list)

    def _v_spec_check(self) -> str:
        v_str = ""

        v_str += "wire opcode_valid = "
        if self.valid_opcodes:
            op_checks: list[str] = []
            for op in self.valid_opcodes:
                if len(op) == 7:
                    try:
                        int(op, 2)
                    except ValueError:
                        # not valid binary
                        pass
                    else:
                        op = f"7'b {op}"
                op_checks.append(f"(rvfi.insn[6:0] == {op})")
            v_str += "\n    || ".join(op_checks)
        else:
            v_str += "0"
        v_str += ";\n\n"

        v_str += "wire extra_valid = "
        v_str += "\n    || ".join(f"({check})" for check in self.extra_valid_checks) or "0"
        v_str += ";\n\n"

        v_str +=dedent("""\
            always @* begin
                if (!reset && rvfi.valid && !rvfi.trap && !opcode_valid && !extra_valid) begin
                    assert(spec_valid && !spec_trap);
                end
            end""")

        return v_str
