PYTHON ?= python3
SBY ?= sby
INSN ?= add
XLEN ?= 32

INSN_SV := $(INSN)_wrapper.sv

RISCV_ROOT ?= ../..
CLI_ROOT ?= $(RISCV_ROOT)/cli
# WRAPPER := insns.wrapper
# %_wrapper.sv: insn_%.json $(RISCV_ROOT)/insns/wrapper.py
# 	cd $(RISCV_ROOT) && $(PYTHON) -m $(WRAPPER) $(abspath $< $@) -f

GENERATOR := riscv_formal.insns.generate
%_wrapper.sv: $(addprefix $(RISCV_ROOT)/riscv_formal/insns/,generate.py model.py)
	cd $(RISCV_ROOT) && $(PYTHON) -m $(GENERATOR) -x $(XLEN) $(abspath $@) $*

c_%_wrapper.sv: $(addprefix $(RISCV_ROOT)/riscv_formal/insns/,generate.py model.py cext.py)
	cd $(RISCV_ROOT) && $(PYTHON) -m $(GENERATOR) -x $(XLEN) -c $(abspath $@) c_$*

.PHONY: insn_wrapper.sv
insn_wrapper.sv: $(INSN_SV) Makefile
	@echo "module rvfi_insn_wrapper (" > $@
	sed -e '1d' $< >> $@

rvf_notsail_%: rvf_notsail.sby insn_wrapper.sv
	$(SBY) -f $< $*

ISA_MODEL ?= rtype
MODEL_FLAGS ?=
INSN_CHECK = $(ISA_MODEL) $(MODEL_FLAGS)
ifneq ("$(INSN_CHECK)", $(shell cat insn_check))
.PHONY: insn_check
endif
insn_check: $(addprefix $(CLI_ROOT)/riscv_formal/checks/,$(ISA_MODEL).py instruction_checker.py generic_checker.py)
	@echo \"$(INSN_CHECK)\" > insn_check

rvfi_insn_check.sv: insn_check
	cd $(CLI_ROOT) && $(PYTHON) -m riscv_formal.checks.$(ISA_MODEL) $(MODEL_FLAGS) --format verilog > $(abspath $@)

rvf_complete_%: rvf_complete.sby rvfi_insn_check.sv $(RISCV_ROOT)/cores/nerv/nerv.sv
	$(SBY) -f $< $*

rvfi_csr_check.sv: $(addprefix $(CLI_ROOT)/riscv_formal/csrs/,nerv_test.py csr.py behavior.py)
	cd $(CLI_ROOT) && $(PYTHON) -m riscv_formal.csrs.nerv_test -r > $(abspath $@)

rvf_csr_check: rvf_csr_check.sby rvfi_csr_check.sv $(RISCV_ROOT)/cores/nerv/nerv.sv
	$(SBY) -f $<

rvfi_csr_ill_check.sv: $(addprefix $(CLI_ROOT)/riscv_formal/checks/,base_csr.py csr_checker.py)
	cd $(CLI_ROOT) && $(PYTHON) -m riscv_formal.checks.base_csr --format verilog > $(abspath $@)

rvf_csr_ill_check: rvf_csr_ill_check.sby rvfi_csr_ill_check.sv $(RISCV_ROOT)/cores/nerv/nerv.sv
	$(SBY) -f $<

.PHONY: clean
clean:
	rm -f insn_*.json
	rm -f *_wrapper.sv rvfi_insn_check.sv
	rm -rf rvf_complete rvf_complete_* rvf_notsail rvf_notsail_*
	rm -f insn_check
