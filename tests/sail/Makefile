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
model/riscv_insts_base_%.sail: $(SAIL_RISCV_DIR)
	sed -n -e '1,8p' -e 'H; /^\/\*/!d ; x ; /$*\b/Ip' $^/model/riscv_insts_base.sail > $@

sail-riscv/model/riscv_min.sail_project: sail-riscv riscv_min.sail_project
	cp riscv_min.sail_project $@

SAIL_FLAGS := --require-version 0.19.1
SAIL_FLAGS += --config sail-riscv/config/rv32d.json
SAIL_FLAGS += --strict-var
SAIL_FLAGS += -dno_cast

SV_FLAGS := --Oconstant-fold --sv --sv-no-assertions --sv-no-strings --sv-no-packed --sv-no-write-flush
SV_FLAGS += --sv-toplevel execute

RV_PROJECT := $(SAIL_RISCV_DIR)/model/riscv_min.sail_project

generated_%.sv: Makefile $(RV_PROJECT) model/riscv_insts_base_%.sail
	$(SAIL) $(SAIL_FLAGS) $(SV_FLAGS) $(RV_PROJECT) model/$*.sail_project -o $(basename $@) riscv_$*
	$(PYTHON) sv_rewriter.py -f $@

.PHONY: clean-sby
clean-sby:
	rm -rf rtype rtype_* add add_*
