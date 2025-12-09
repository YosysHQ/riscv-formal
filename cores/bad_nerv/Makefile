RVF_CLI ?=
RVF_OPTS ?=

# ./gen_test.py all will (re-)generate all test configs
testbug%.cfg: gen_test.py
	./$< $*

testbug%: testbug%.cfg
ifeq ($(RVF_CLI),)
	python3 ../../checks/genchecks.py $@
else
	riscv_formal $< genchecks $(RVF_OPTS)
	sed -i "s%$(HOME)/riscv-formal/cli/.venv/lib/python3.11/cores/%$(HOME)/riscv-formal/cores/%g" $@/*.sby
	sed -i "s%$(HOME)/riscv-formal/cli/.venv/lib/python3.11/checks/%$(HOME)/riscv-formal/checks/%g" $@/*.sby
endif

%/run: %
	-$(MAKE) -C $*
	touch $@

check:
	bash cexdata.sh

TARGET ?=
ifneq ($(TARGET),)
.PHONY: clean-target run
clean-target:
	rm -rf $(TARGET)
run: $(TARGET) $(TARGET)/run
endif

TESTBUGS := $(wildcard testbug*.cfg)
TESTBUG_DIRS := $(basename $(TESTBUGS))
TESTBUG_OUT ?= out.log
.PHONY: testbugs
testbugs: $(TESTBUG_DIRS) $(addsuffix /run,$(TESTBUG_DIRS))
	bash cexdata.sh | sed 's%cores/bad_nerv/../../%%g' | tee $(TESTBUG_OUT)

.PHONY: clean
clean:
	rm -rf $(TESTBUG_DIRS) checks/
