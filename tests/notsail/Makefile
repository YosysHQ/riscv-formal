PYTHON ?= python3
SBY ?= sby
INSN ?= add
XLEN ?= 32

INSN_SV := $(INSN)_wrapper.sv

RISCV_ROOT ?= ../..
# WRAPPER := insns.wrapper
# %_wrapper.sv: insn_%.json $(RISCV_ROOT)/insns/wrapper.py
# 	cd $(RISCV_ROOT) && $(PYTHON) -m $(WRAPPER) $(abspath $< $@) -f

GENERATOR := src.insns.generate
%_wrapper.sv: $(addprefix $(RISCV_ROOT)/src/insns/,generate.py model.py)
	cd $(RISCV_ROOT) && $(PYTHON) -m $(GENERATOR) -x $(XLEN) $(abspath $@) $*

c_%_wrapper.sv: $(addprefix $(RISCV_ROOT)/src/insns/,generate.py model.py cext.py)
	cd $(RISCV_ROOT) && $(PYTHON) -m $(GENERATOR) -x $(XLEN) -c $(abspath $@) c_$*

.PHONY: insn_wrapper.sv
insn_wrapper.sv: $(INSN_SV) Makefile
	@echo "module rvfi_insn_wrapper (" > $@
	sed -e '1d' $< >> $@

rvf_notsail_%: rvf_notsail.sby insn_wrapper.sv
	$(SBY) -f $< $*

ISA_MODEL = rtype
ifneq ($(ISA_MODEL), $(shell cat isa_model))
.PHONY: isa_model
endif
isa_model: $(addprefix $(RISCV_ROOT)/src/checks/,$(ISA_MODEL).py)
	@echo $(ISA_MODEL) > isa_model

rvfi_insn_check.sv: isa_model
	cd $(RISCV_ROOT) && $(PYTHON) -m src.checks.$(ISA_MODEL) --format verilog > $(abspath $@)

rvf_complete_%: rvf_complete.sby rvfi_insn_check.sv
	$(SBY) -f $< $*

.PHONY: clean
clean:
	rm -f insn_*.json
	rm -f *_wrapper.sv rvfi_insn_check.sv
	rm -rf rvf_complete rvf_complete_* rvf_notsail rvf_notsail_*
