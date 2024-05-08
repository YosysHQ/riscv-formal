Quick start guide
=================

So you want to get your hands dirty with riscv-formal? Install the tools
and pick one of the exercises below.

.. Do these slides still exist somewhere?

.. See also `this presentation
.. slides <http://bygone.clairexen.net/papers/2017/riscv-formal/>`__ for an
.. introduction to riscv-formal.

Prerequisites
-------------

You'll need Yosys, SBY, and Boolector for the formal proofs. See the `SBY
install instructions
<https://yosyshq.readthedocs.io/projects/sby/en/latest/install.html>`__.

For additional python requirements:

::

   python3 -m pip install Verilog_VCD

Some of those tools are packaged for some of the major Linux
distribution, but those packages are sometimes a few years old and do
not work with riscv-formal. Follow the descriptions linked above and
install from the latest sources instead.

If you want to inspect counter example traces you will need
`gtkwave <http://gtkwave.sourceforge.net/>`__. Whatever version of
gtkwave is pre-packaged in your distribution is probably fine.

If you want to disassemble the code executed in the counter example
traces you will need an installation of 32 bit
`riscv-tools <https://github.com/riscv/riscv-tools>`__, specifically
you'll need ``riscv32-unknown-elf-gcc`` and
``riscv32-unknown-elf-objdump`` in your ``$PATH``.

For the 2nd exercise the PicoRV32 Makefile expects a toolchain with
certain properties in ``/opt/riscv32i``. The easiest way to build this
is to check out the `PicoRV32 github repo
<https://github.com/YosysHQ/picorv32>`__ and run ``make -j$(nproc)
build-riscv32i-tools`` ( `prerequisites and more documentation on the
process
<https://github.com/YosysHQ/picorv32#building-a-pure-rv32i-toolchain>`__
also available).

For the 2nd exercise you will also need `Icarus
Verilog <http://iverilog.icarus.com/>`__. If your distribution packages
v10 or better then this is fine, otherwise you'll need to build it from
source.

Exercise 1: Formally verify a core
----------------------------------

Formally verify that the NERV processor complies with the RISC-V ISA:

::

   cd riscv-formal
   cd cores/nerv/
   make -j$(nproc) check

Now make a random change to ``nerv.sv`` and re-run the tests:

::

   make clean
   make -j$(nproc) check

The check will likely fail now. (It will if the change did break ISA
compliance of the core.)

If you have a 32 bit version of riscv-tools installed
(``riscv32-unknown-elf-gcc`` and ``riscv32-unknown-elf-objdump`` are in
``$PATH``) then you can use ``disasm.py`` to display the sequence of
instructions that caused the error.

Let's say ``liveness_ch0`` is the check that failed:

::

   python3 disasm.py checks/liveness_ch0/engine_0/trace.vcd

Or you can simply use gtkwave to display the counter example trace:

::

   gtkwave checks/liveness_ch0/engine_0/trace.vcd trace.gtkw

Exercise 2: Build an RVFI Monitor and run it
--------------------------------------------

An RVFI Monitor can be run side-by-side with your core and will detect
when the core violates the ISA spec. RVFI monitors are synthesizable, so
in addition to simulation they can also be used in FPGA emulation
testing.

Let's build an RVFI Monitor to be used with PicoRV32. PicoRV32 supports
the rv32ic ISA (``-i rv32ic``), its RVFI port is one channel wide
(``-c 1``), and it performs memory operations with word alignment
(``-a``):

::

   cd monitor
   python3 generate.py -i rv32ic -c 1 -a -p picorv32_rvfimon > picorv32_rvfimon.v

Next we need to clone the PicoRV32 git repository and copy the monitor
core:

::

   git clone https://github.com/YosysHQ/picorv32.git
   cp picorv32_rvfimon.v picorv32/rvfimon.v
   cd picorv32

And then run the test bench with RVFI monitor support:

::

   make test_rvf

(You will need to make minor changes to the Makefile if you don't have
an rv32i toolchain installed in ``/opt/riscv32i``.)

You can now try making changes to ``picorv32.v`` and see if the RVFI
monitor catches errors in the test bench when you re-run
``make test_rvf``.

You can also try running ``generate.py`` with ``-V``. This will generate
a monitor that prints some information about each packet it sees on the
RVFI port.
