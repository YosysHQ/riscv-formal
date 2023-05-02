
picorv32.v:
	wget -O picorv32.v https://raw.githubusercontent.com/YosysHQ/picorv32/master/picorv32.v

checks: picorv32.v
	python3 ../../checks/genchecks.py
	$(MAKE) -C checks

check: checks
	bash cexdata.sh
	cat cexdata-*/status.txt

clean:
	rm -f picorv32.v cexdata-*.zip
	rm -rf disasm.o disasm.s checks/ cexdata-*/
	rm -f testbug*.cfg
	rm -rf testbug*/
