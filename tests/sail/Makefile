SAIL_RISCV_DIR ?= sail-riscv
PYTHON ?= python3
SAIL ?= sail

sail-riscv:
	git clone --sparse --depth=1 --filter=tree:0 \
		--branch=0.8 https://github.com/riscv/sail-riscv.git $@
	cd $@ && \
		git sparse-checkout set model/ config/ && \
		patch -p1 < ../prelude.patch

# insts_rtype is just the RTYPE section from insts_base
model/riscv_insts_rtype.sail: $(SAIL_RISCV_DIR)
	sed -n -e '1,8p' -e 'H; /^\/\*/!d ; x ; /RTYPE\b/p' $^/model/riscv_insts_base.sail > $@

sail-riscv/model/riscv_min.sail_project: sail-riscv riscv_min.sail_project
	cp riscv_min.sail_project $@

SAIL_FLAGS := --require-version 0.19.1
SAIL_FLAGS += --config sail-riscv/config/rv32d.json
SAIL_FLAGS += --strict-var
SAIL_FLAGS += -dno_cast

SV_FLAGS := --Oconstant-fold --sv --sv-no-assertions --sv-no-strings --sv-no-packed --sv-no-write-flush
SV_FLAGS += --sv-toplevel execute

RV_PROJECTS := $(SAIL_RISCV_DIR)/model/riscv_min.sail_project ./model/rtype.sail_project
RV_TARGET := riscv_rtype

generated_rtype.sv: Makefile $(RV_PROJECTS)
	$(SAIL) $(SAIL_FLAGS) $(SV_FLAGS) $(RV_PROJECTS) -o $(basename $@) $(RV_TARGET)
	$(PYTHON) sv_rewriter.py -f $@

.PHONY: clean-sby
clean-sby:
	rm -rf rtype rtype_* add add_*
