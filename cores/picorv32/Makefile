
picorv32.v:
	wget -O picorv32.v https://raw.githubusercontent.com/YosysHQ/picorv32/master/picorv32.v

RISCV_FORMAL ?= python3 -m riscv_formal
RVF_OPTS ?=
checks: picorv32.v
	$(RISCV_FORMAL) checks.cfg genchecks $(RVF_OPTS)

run_checks: checks
	$(MAKE) -C checks
	@touch $@

.PHONY: check
check: run_checks
	bash cexdata.sh
	cat cexdata-*/status.txt

clean:
	rm -f picorv32.v cexdata-*.zip
	rm -rf disasm.o disasm.s checks/ cexdata-*/
	rm -f testbug*.cfg
	rm -rf testbug*/
