%: %.cfg
	python3 ../../checks/genchecks.py $*
	echo "/*" >> $*/.gitignore

%/run: %
	$(MAKE) -C $*
	touch $@

check:
	bash cexdata.sh
