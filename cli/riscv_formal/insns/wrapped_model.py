from dataclasses import dataclass, field
from typing import Optional
from textwrap import dedent

from .model import Instruction

@dataclass(kw_only=True)
class WrappedInstruction(Instruction):
    checker_module: str

    inst_args: list[str] = field(default_factory=list)

    wrap_x_in: bool = False
    wrap_x_out: bool = False
    wrap_pc: bool = False
    wrap_next_pc: bool = False
    x_upper: int = 31
    x_lower: int = 1
    r_bits: int = 5

    extra_sig1: list[tuple[str, str, Optional[str]]] = field(default_factory=list)
    extra_sig2: list[tuple[str, str, Optional[str]]] = field(default_factory=list)
    op_name: str | list[str] | None = "op"
    # [mnemonic, enum_value, op_value]
    op_values_list: list[tuple[str, str | list[str], str | list[str]]] = field(default_factory=list)

    op_type_enum: str | list[str] | None = None
    op_value_switch: Optional[str] = None

    def _inputs_used(self):
        inputs = super()._inputs_used()
        if self.wrap_pc:
            inputs.add("pc_rdata")
        return inputs

    def _outputs_used(self):
        outputs = super()._outputs_used()
        if self.wrap_next_pc:
            outputs.add("pc_wdata")
        return outputs

    def _v_inst_check(self) -> None:
        # check instance map
        inst_args_avail = list(self._insn_part_dict.keys()) + [self.op_name]
        for inst_arg in self.inst_args:
            for arg_part in inst_arg.split():
                if arg_part not in inst_args_avail and not arg_part[0].isdigit():
                    raise NotImplementedError(arg_part)

    def _v_reg_wrap(self) -> str:
        # wrap registers
        x_type = f"logic [{self.xlen-1}:0]"
        x_range = f"[{self.x_upper}:{self.x_lower}]"
        reg_wrap = ""
        for x_inout, do_wrap in [("x_in", self.wrap_x_in), ("x_out", self.wrap_x_out)]:
            if do_wrap:
                reg_wrap += f"{x_type} {x_inout}{x_range};\n"

        # address fixing
        localparams = []
        x_assigns = []
        #todo: multiple destination regs
        result_decl = ""
        for idx, used_reg in enumerate(self._used_regs, start=1):
            raddr = f"{used_reg}_0"
            localparams.append(f"{raddr} = {self.r_bits}'d{idx}")
            if used_reg in self._maybe_sources and self.wrap_x_in:
                x_assigns.append(f"assign x_in[{raddr}] = rvfi_{used_reg}_rdata;")
            if used_reg in self._maybe_dests and self.wrap_x_out:
                result_decl = f"wire [{self.xlen-1}:0] result = x_out[{raddr}];\n"
        if localparams:
            localparams = ", ".join(localparams)
            reg_wrap += f"localparam {localparams};\n"
        if x_assigns:
            reg_wrap += "\n".join(x_assigns) + "\n"
        reg_wrap += result_decl

        if self.wrap_next_pc:
            reg_wrap += f"wire [{self.xlen-1}:0] next_pc = rvfi_pc_rdata + 4;\n"
        if reg_wrap:
            return "// register wrapping\n" + reg_wrap
        else:
            return "// no register wrapping"

    def _v_extra_sigs(self) -> str:
        extra_signals = "// extra signals\n"
        extra_signal_decls = self.extra_sig1 + self.extra_sig2
        if isinstance(self.op_name, str):
            if len(self.op_values_list) == 1:
                op_default = self.op_values_list[0][1]
                if isinstance(op_default, list):
                    raise NotImplementedError(op_default)
            else:
                op_default = None
            if not isinstance(self.op_type_enum, str):
                raise NotImplementedError(self.op_type_enum)
            extra_signal_decls.append((self.op_type_enum, f"{self.op_name}_0", op_default))
        for t, n, v in extra_signal_decls:
            extra_signals += f"{t} {n};\n" if v == None else f"{t} {n} = {v};\n"
        return extra_signals

    def _v_insn_map(self) -> str:
        v_str = self._v_reg_wrap() + '\n'
        v_str += self._v_extra_sigs() + '\n'
        if self.op_name is None:
            return v_str + super()._v_insn_map()
        else:
            # combined instruction mapping
            insn_map = "// insn check\n"

        if isinstance(self.op_name, list):
            if not isinstance(self.op_type_enum, list):
                raise NotImplementedError(self.op_type_enum)
            for name, type_enum in zip(self.op_name, self.op_type_enum):
                insn_map += f"{type_enum} {name}_0;\n"
            
            op_value_keys = self.op_name
        else:
            if self.op_value_switch is None:
                raise NotImplementedError(self.op_value_switch)
            op_value_keys = self.op_value_switch.split()

        if len(op_value_keys) == 1:
            case_switch = f"insn_{self.op_value_switch}"
        else:
            case_switch = '{' + ', '.join([f"insn_{k}" for k in op_value_keys]) + '}'
        op_value_bits = sum([self._insn_part_dict[k] for k in op_value_keys])
        if len(self.op_values_list) == 1:
            insn_map += f"wire illinsn = {case_switch} != {op_value_bits}'b {self.op_values_list[0][0]};\n"
        else:
            insn_map += dedent(f"""\
                reg illinsn;
                always @* begin
                    illinsn <= 0;
                    case ({case_switch})
            """)
            if isinstance(self.op_name, list):
                for _, part_type_values, part_values in self.op_values_list:
                    var_name = '{' + ', '.join(f"{name}_0" for name in self.op_name) + '}'
                    value = ''.join(part_values)
                    enum = '{' + ', '.join(part_type_values) + '}'
                    insn_map += f"        {op_value_bits}'b {value}: {var_name} <= {enum};\n"
            else:
                for _, enum, value in self.op_values_list:
                    insn_map += f"        {op_value_bits}'b {value}: {self.op_name}_0 <= {enum};\n"
            insn_map += dedent(f"""\
                        default: illinsn <= 1;
                    endcase
                end
            """)

        return v_str + insn_map

    def _v_instantiation(self) -> str:
        instantiation = f"// {self.name} instance\n"
        checker_args: list[str] = []
        for inst_arg in self.inst_args:
            if (inst_arg in self._used_regs
                or isinstance(self.op_name, str) and inst_arg == self.op_name
                or isinstance(self.op_name, list) and inst_arg in self.op_name
                ):
                checker_arg = f"{inst_arg}_0"
            elif " " in inst_arg:
                arg_parts = [k if k[0].isdigit() else f"insn_{k}" for k in inst_arg.split()]
                checker_arg = '{' + ', '.join(arg_parts) + '}'
            else:
                checker_arg = f"insn_{inst_arg}"
            if checker_arg: checker_args.append(checker_arg)
        if self.wrap_pc:
            checker_args.append(f"rvfi_pc_rdata")
        if self.wrap_next_pc:
            checker_args.append(f"next_pc")
        if self.wrap_x_in:
            for idx in range(self.x_lower, self.x_upper + 1):
                checker_args.append(f"x_in[{idx}]")
        for _, extra_sig, _ in self.extra_sig1:
            checker_args.append(extra_sig)
        if self.wrap_x_out:
            for idx in range(self.x_lower, self.x_upper + 1):
                checker_args.append(f"x_out[{idx}]")
        if self.wrap_next_pc:
            checker_args.append("spec_pc_wdata")
        for _, extra_sig, _ in self.extra_sig2:
            checker_args.append(extra_sig)

        instantiation += f"{self.checker_module} wrapped_checker("
        instantiation += ", ".join(checker_args)
        instantiation += ");\n"

        return instantiation

    def _v_spec_value(self, spec_sig: str) -> Optional[str]:
        if spec_sig == "pc_wdata" and self.wrap_next_pc:
            return None
        else:
            return super()._v_spec_value(spec_sig)

    def _v_checks(self):
        super()._v_checks()
        self._v_inst_check()
