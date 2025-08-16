PYTHON ?= python3
SBY ?= sby
INPUT ?= rtype.json
INSN ?= add

INSN_SV := $(INSN)_wrapper.sv

insn_%.json: insn_config_generator.py $(INPUT)
	$(PYTHON) $< $(INPUT) -f

WRAPPER := ../sail/insn_wrapper.py
%_wrapper.sv: insn_%.json $(WRAPPER)
	$(PYTHON) $(WRAPPER) $< -f

.PHONY: insn_wrapper.sv
insn_wrapper.sv: $(INSN_SV) Makefile
	@echo "module rvfi_insn_wrapper (" > $@
	sed -e '1d' $< >> $@

rvf_notsail_%: rvf_notsail.sby insn_wrapper.sv
	$(SBY) -f $< $*

.PHONY: clean
clean:
	rm -f insn_*.json
