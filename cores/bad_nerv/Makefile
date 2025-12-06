RVF_CLI ?=

%: %.cfg
ifeq ($(RVF_CLI),)
	python3 ../../checks/genchecks.py $*
else
	riscv_formal $< genchecks
	sed -i "s%$(HOME)/riscv-formal/cli/.venv/lib/python3.11/cores/%$(HOME)/riscv-formal/cores/%g" $*/reg_ch0.sby
	sed -i "s%$(HOME)/riscv-formal/cli/.venv/lib/python3.11/checks/%$(HOME)/riscv-formal/checks/%g" $*/reg_ch0.sby
endif
	echo "/*" >> $*/.gitignore

%/run: %
	$(MAKE) -C $*
	touch $@

check:
	bash cexdata.sh
