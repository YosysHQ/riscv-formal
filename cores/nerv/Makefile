#  NERV -- Naive Educational RISC-V Processor
#
#  Copyright (C) 2020  N. Engelhardt <nak@yosyshq.com>
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

TOOLCHAIN_PREFIX?=riscv64-unknown-elf-

RISCV_ARCH?=rv32i$(shell $(TOOLCHAIN_PREFIX)as -march=rv32i_zicsr --dump-config 2>/dev/null && echo _zicsr)

test: firmware.hex testbench
	vvp -N testbench +vcd

firmware.elf: firmware.s vectors.s firmware.c
	$(TOOLCHAIN_PREFIX)gcc -march=$(RISCV_ARCH) -mabi=ilp32 -Os -Wall -Wextra -Wl,-Bstatic,-T,sections.lds,--strip-debug -ffreestanding -nostdlib -o $@ $^

firmware.hex: firmware.elf
	$(TOOLCHAIN_PREFIX)objcopy -O verilog $< $@

testbench: testbench.sv nerv.sv
	iverilog -g2012 -o testbench -D STALL -D NERV_DBGREGS testbench.sv nerv.sv

checks:
	python3 ../../checks/genchecks.py
	$(MAKE) -C checks

check: checks
	bash cexdata.sh
	cat cexdata/warnings.txt
	cat cexdata/status.txt

show:
	gtkwave testbench.vcd testbench.gtkw >> gtkwave.log 2>&1 &

trace:
	gtkwave cexdata/checks_$(TRACE_CHECK)_ch0.vcd trace.gtkw >> gtkwave.log 2>&1 &

clean:
	rm -rf firmware.elf firmware.hex testbench testbench.vcd gtkwave.log
	rm -rf disasm.o disasm.s checks/ cexdata/
