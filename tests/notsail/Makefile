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

.PHONY: clean
clean:
	rm -f insn_*.json
