#  NERV -- Naive Educational RISC-V Processor
#
#  Copyright (C) 2020  N. Engelhardt <nak@yosyshq.com>
#  Copyright (C) 2020  Claire Xenia Wolf <claire@yosyshq.com>
#  Copyright (C) 2023  Jannis Harder <jix@yosyshq.com> <me@jix.one>
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

TESTBENCH_DEFINES?=-D NERV_DBGREGS -D NERV_CSR
TESTBENCH_ARGS?=+vcd
CHECKS?=

CLONE?=0

RISCV_ARCH?=rv32i$(shell $(TOOLCHAIN_PREFIX)as -march=rv32i_zicsr --dump-config 2>/dev/null && echo _zicsr)

CACHE_SOURCES:=nerv_axi_cache.sv nerv_axi_cache_icache.sv nerv_axi_cache_dcache.sv

.PHONY: test_internal test_axi verify_axi verify_axi_cover checks_internal checks_axi all

test_internal: firmware.hex testbench_internal
	vvp -N testbench_internal $(TESTBENCH_ARGS)

test_axi: firmware.hex testbench_axi
	vvp -N testbench_axi $(TESTBENCH_ARGS)

verify_axi: SVA-AXI4-FVIP verify_axi.sby verify_axi.sv
	sby -f verify_axi.sby prove

verify_axi_cover: SVA-AXI4-FVIP verify_axi.sby verify_axi.sv
	sby -f verify_axi.sby cover

firmware.elf: ../firmware.s ../vectors.s firmware.c
	$(TOOLCHAIN_PREFIX)gcc -march=$(RISCV_ARCH) -mabi=ilp32 -Os -Wall -Wextra -Wl,-Bstatic,-T,../sections.lds,--strip-debug -ffreestanding -nostdlib -o $@ $^

firmware.hex: firmware.elf
	$(TOOLCHAIN_PREFIX)objcopy -O verilog $< $@

testbench_internal: testbench_internal.sv ../nerv.sv $(CACHE_SOURCES)
	iverilog -stestbench -g2012 -o $@ $(TESTBENCH_DEFINES) $^

testbench_axi: testbench_axi.sv ../nerv.sv $(CACHE_SOURCES) axi_ram.v
	iverilog -stestbench -g2012 -o $@ $(TESTBENCH_DEFINES) $^

ifeq ($(CLONE),1)
SVA-AXI4-FVIP:
	git clone https://github.com/YosysHQ-GmbH/SVA-AXI4-FVIP
else
SVA-AXI4-FVIP:
	@echo "SVA-AXI4-FVIP repository not found, use 'make SVA-AXI4-FVIP CLONE=1' to clone from GitHub"
	@echo "alternatively manually clone or symlink a clone of https://github.com/YosysHQ-GmbH/SVA-AXI4-FVIP"
	@exit 1
endif

checks_internal:
	cd .. && python3 ../../checks/genchecks.py axi_cache/checks_internal
	$(MAKE) -C checks_internal $(CHECKS)

checks_axi:
	cd .. && python3 ../../checks/genchecks.py axi_cache/checks_axi
	$(MAKE) -C checks_axi $(CHECKS)

all: test_internal test_axi verify_axi verify_axi_cover checks_internal checks_axi

clean:
	rm -rf firmware.elf firmware.hex
	rm -rf testbench_internal testbench_internal.vcd
	rm -rf testbench_axi testbench_axi.vcd
	rm -rf verify_axi_prove verify_axi_cover
	rm -rf checks_internal checks_axi
