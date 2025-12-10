RVF_CLI ?=
RVF_OPTS ?=

# make patch with git diff --output=bad_nerv.patch bad_nerv.sv
.PHONY: patch unpatch
patch:
	git apply bad_nerv.patch
unpatch:
	git apply -R bad_nerv.patch

# ./gen_test.py all will (re-)generate all test configs
testbug%.cfg: gen_test.py
	./$< $*

testbug%: testbug%.cfg
ifeq ($(RVF_CLI),)
	python3 ../../checks/genchecks.py $@
else
	riscv_formal $< genchecks $(RVF_OPTS)
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
