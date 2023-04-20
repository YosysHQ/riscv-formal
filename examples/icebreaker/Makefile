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

test: firmware.hex testbench
	vvp -N testbench +vcd

firmware.elf: firmware.s firmware.c
	$(TOOLCHAIN_PREFIX)gcc -march=rv32i -mabi=ilp32 -Os -Wall -Wextra -Wl,-Bstatic,-T,sections.lds,--strip-debug -ffreestanding -nostdlib -o $@ $^

firmware.hex: firmware.elf
	$(TOOLCHAIN_PREFIX)objcopy -O verilog $< /dev/stdout | sed -r 's,(..) (..) (..) (..),\4\3\2\1,g' > $@

testbench: testbench.sv ../../nerv.sv ../../nervsoc.sv top.v firmware.hex
	iverilog -o testbench -D STALL -D NERV_DBGREGS testbench.sv ../../nerv.sv ../../nervsoc.sv top.v

design.json: ../../nerv.sv ../../nervsoc.sv top.v firmware.hex
	yosys -l design_ys.log -p 'synth_ice40 -top top -json $@' ../../nerv.sv ../../nervsoc.sv top.v

design.asc: design.json icebreaker.pcf
	nextpnr-ice40 -l design_pnr.log --up5k --package sg48 --asc design.asc --pcf icebreaker.pcf --json design.json --placer heap

design.bin: design.asc
	icepack $< $@

prog: design.bin
	iceprog $<
	
show:
	gtkwave testbench.vcd testbench.gtkw >> gtkwave.log 2>&1 &

clean:
	rm -rf firmware.elf firmware.hex testbench testbench.vcd gtkwave.log
	rm -rf design.json design.asc design.bin design_ys.log design_pnr.log
