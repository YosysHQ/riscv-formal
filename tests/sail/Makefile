SAIL_RISCV_DIR ?= sail-riscv
PYTHON ?= python3

sail-riscv:
	git clone --sparse --depth=1 --filter=tree:0 \
		--branch=sv https://github.com/Alasdair/sail-riscv.git $@
	cd $@ && git sparse-checkout set model/

$(SAIL_RISCV_DIR)/Makefile: sail-riscv

ARCH=32
include $(SAIL_RISCV_DIR)/Makefile

RV_SRCS := riscv_dummy.sail

# riscv_insts_rtype.sail is a cut down version of riscv_insts_base.sail
# with just the base RTYPE instructions
INST := riscv_insts_rtype.sail
RV_TYPES := riscv_types_common.sail riscv_types_ext.sail riscv_types.sail
RV_REGS := riscv_reg_type.sail riscv_regs.sail
RV_PRE := $(PRELUDE) $(RV_TYPES) $(RV_REGS) riscv_insts_begin.sail
RV_POST := riscv_insts_end.sail
RV_SRCS += $(addprefix $(SAIL_RISCV_DIR)/model/,$(RV_PRE) $(INST) $(RV_POST))

SV_FLAGS := --sv --sv-no-assertions --sv-no-strings --sv-no-packed --sv-no-write-flush

generated_rtype.sv: Makefile
	$(SAIL) $(SAIL_FLAGS) -O --Oconstant-fold $(SV_FLAGS) --sv-toplevel execute $(RV_SRCS) -o $(basename $@)
	$(PYTHON) sv_rewriter.py -f $@
