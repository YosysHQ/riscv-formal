#!/bin/bash
#
#  NERV -- Naive Educational RISC-V Processor
#
#  Copyright (C) 2020  Claire Xenia Wolf <claire@yosyshq.com>
#
#  Permission to use, copy, modify, and/or distribute this software for any
#  purpose with or without fee is hereby granted, provided that the above
#  copyright notice and this permission notice appear in all copies.
#
#  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#  ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#  WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#  ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#  OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

set -ex

rm -rf cexdata
mkdir cexdata

for x in {checks,testbug[0-9][0-9][0-9]}/*/FAIL; do
	test -f $x || continue
	x=${x%/FAIL}
	y=${x/\//_}
	cp $x/logfile.txt cexdata/$y.log
	if test -f $x/engine_*/trace.vcd; then
		cp $x/engine_*/trace.vcd cexdata/$y.vcd
		python3 disasm.py cexdata/$y.vcd > cexdata/$y.asm
	fi
done

sed -re '/WARNING|[Ww]arning/ ! d; /\[VERI-1927\] .*\/wrapper.sv:/ d; s/^([^:]|:[^ ])*: //;' checks/*/logfile.txt | sort -Vu > cexdata/warnings.txt

for x in {checks,testbug[0-9][0-9][0-9]}/*.sby; do
	test -f $x || continue
	x=${x%.sby}
	if [ -f $x/PASS ]; then
		printf "%-30s %s %10s\n" $x "  pass  " $(sed '/Elapsed process time/ { s/.*\]: //; s/ .*//; p; }; d;' $x/logfile.txt)
	elif [ -f $x/FAIL ]; then
		printf "%-30s %s %10s\n" $x "**FAIL**" $(sed '/Elapsed process time/ { s/.*\]: //; s/ .*//; p; }; d;' $x/logfile.txt)
	else
		printf "%-30s %s\n" $x unknown
	fi
done | awk '{ print gensub(":", "", "g", $3), $0; }' | sort -n | cut -f2- -d' ' > cexdata/status.txt

