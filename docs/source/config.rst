Defining macros
~~~~~~~~~~~~~~~

Configuration macros
====================

The riscv-formal insn models and checkers are configured using a few
Verilog pre-processor macros. They must be defined bofore reading any
riscv-formal verilog files. The first riscv-formal verilog file read
after defining the macros must be
`rvfi_macros.vh <../checks/rvfi_macros.vh>`__.

Example configuration:

.. code-block:: systemverilog

   `define RISCV_FORMAL
   `define RISCV_FORMAL_NRET 1
   `define RISCV_FORMAL_XLEN 32
   `define RISCV_FORMAL_ILEN 32
   `define RISCV_FORMAL_COMPRESSED
   `define RISCV_FORMAL_ALIGNED_MEM

The macros in this section must be defined by the user where relevant,
while the next section includes additional macros which may be
automatically generated depending on configuration. Defining
``RISCV_FORMAL``, ``RISCV_FORMAL_NRET``, ``RISCV_FORMAL_XLEN``, and
``RISCV_FORMAL_ILEN`` is mandatory if ``genchecks.py`` is not being
used.

RISCV_FORMAL_UMODE
------------------

This macro must be defined when the core under tests supports U-mode.

RISCV_FORMAL_SMODE
------------------

This macro must be defined when the core under tests supports S-mode.

RISCV_FORMAL_ALTOPS
-------------------

This macro must be defined if the core under tests implements :ref:`alternative
arithmetic semantics <rvfi-alt-arith>`.

RISCV_FORMAL_ALIGNED_MEM
------------------------

Cores that only have hardware support for word-aligned memory access may
choose to retire memory load/store operations for smaller units
(half-words, bytes) word aligned with the appropiate ``rmask/wmask``
values to select the correct bytes. In this case the
``RISCV_FORMAL_ALIGNED_MEM`` macro must be defined.

RISCV_FORMAL_VALIDADDR(addr)
----------------------------

Set this to an expression of ``addr`` that evaluates to 1 when the given
address is a valid physical address for the processor under test. If not
defined this expression will always evaluate to true.

RISCV_FORMAL_VALIDHPMEVENT(event)
---------------------------------

Set this to an expression of ``event`` that evaluates to 1 when the
given event is a valid assignment for a hpmevent CSR. If not defined
this expression will always evaluate to true.

RISCV_FORMAL_IOADDR(addr)
-------------------------

Set this to an expression of ``addr`` that evaluates to 1 when the given
address belongs to an i/o memory region.  If not defined this expression
will always evaluate to true.

RISCV_FORMAL_WAITINSN(insn)
---------------------------

Set this to an expression of ``insn`` that evaluates to 1 when the given
instruction is a wait instruction similar to WFI. (WFI does not need to
be recognized by the expression. This is for non-standard instructions
in addition to WFI.)

RISCV_FORMAL_PMA_MAP
--------------------

Set this to the name of a module that takes an address as input and
outputs the PMA info for that address. The exact interface of such a
module is not entirely defined yet.

Testbench macros
================

The following macros are all defined automatically when using
``genchecks.py``. If tests are being performed manually without the
generated framework, some of these macros may be required to be defined
by the user prior to loading the testbench. Additional information may
be found in :ref:`procedure-config`.

RISCV_FORMAL
------------

This macro is set whenever riscv-formal is used. It is actually never
used by any of the riscv-formal Verilog files, but can be used by cores
under test to enable or disable generation of the RVFI ports.

RISCV_FORMAL_NRET
-----------------

The number of channels for the RVFI port (and thus the theoretical
maximum number of instructions the core can retire via RVFI in one
cycle). The value of this macro can be set by providing the ``nret``
option in the check config.

RISCV_FORMAL_XLEN
-----------------

The width of integer registers in the ISA implemented by the core under
test. Valid values are 32, 64, and 128. Only 32 is fully supported at
the moment. ``genchecks.py`` will define this as 32, unless the ``isa``
string in the options contains rv64.

RISCV_FORMAL_ILEN
-----------------

The maximum width of an instruction retired by the core. For cores
supporting fused instructions this is the maximum length of a complete
fused instruction. There is currently no way to automatically generate
tests with a value other than 32.

RISCV_FORMAL_COMPRESSED
-----------------------

For cores supporting the RISC-V Compressed ISA this define must be set.
This will be automatically defined if the ``c`` extension appears in the
``isa`` string.

RISCV_FORMAL_BLACKBOX_REGS
--------------------------

When checking for correct implementation of the RISC-V instructions
(“insncheck”) it is possible to black-box the processor register file.
This macro may be used in the core under test to black-box the register
file. Controlled by the presence or absence of the ``blackbox`` option.

RISCV_FORMAL_BLACKBOX_ALU
-------------------------

When checking for consistency of the stream of retired instructions
(such as “regcheck”) it is possible to black-box the actual ALU
operations. This macro may be used in the core under test to black-box
the ALU. Controlled by the presence or absence of the ``blackbox``
option.

RISCV_FORMAL_FAIRNESS
---------------------

When checking for liveness of the core, then the peripherals and
abstractions used in the check must guarantee fairness. This macro
should be tested by the peripherals and abstractions to decide if
fairness guarantees should be enabled. Automatically defined for
``liveness`` and ``hang`` checks.

RISCV_FORMAL_RESET_CYCLES
-------------------------

The number of cycles to hold reset high for at the start of the model
checking.

RISCV_FORMAL_CHECK_CYCLE
------------------------

The cycle number in which checks will be performed. For bounded model
checking, this should be the solver depth.

RISCV_FORMAL_TRIG_CYCLE
-----------------------

The cycle number in which to trigger some check specific action.

RISCV_FORMAL_CHANNEL_IDX
------------------------

For checks which only operate on a single channel, this macro defines
which channel is being checked.

RISCV_FORMAL_CHECKER
--------------------

The name of the module to be instantiated by the testbench for formal
verification. e.g. ``rvfi_csrw_check``.

RISCV_FORMAL_ASSUME
-------------------

Indicates that the ``assume_stmts.vh`` file should be included in the
testbench. This file is expected to contain a series of SV assumptions
that the solver should make.

RISCV_FORMAL_UNBOUNDED
----------------------

This macro is used to indicate that unbounded model checking is being
used.

RISCV_FORMAL_CSR\_<name>
------------------------

Each CSR being connected over the RVFI interface should be defined with
one of these macros. Refer to :ref:`rvfi-csrs` for more details
on how this name is used.

RISCV_FORMAL_CSRW_NAME
----------------------

This macro defines the name of the CSR under test during ``csrw``
checks.

RISCV_FORMAL_CSRWH
------------------

This macro is used in the ``csrw`` checks to indicate that the current
CSR consists of two registers, with the second being of the same name
but appended with 'h'.

RISCV_FORMAL_INSN_MODEL
-----------------------

When performing ``insn`` checks, this is the name of the module for the
current instruction. e.g. ``rvfi_insn_add``.

Macros defined by rvfi_macros.vh
================================

The Verilog file ``rvfi_macros.vh`` defines a few useful helper macros.

RVFI_WIRES, RVFI_OUTPUTS, RVFI_INPUTS, RVFI_CONN
------------------------------------------------

Macros to declare wires, output ports, or input ports for all ``rvfi_*``
signals. The last macro is for creating the proper connections on module
instances. This macros can be useful for routing the ``rvfi_*`` signals
through the design hierarchy.

rvformal_rand_reg and rvformal_rand_const_reg
---------------------------------------------

Macros for defining unconstrained signals (``rvformal_rand_reg``) or
constant signals with an unconstrained initial value
(``rvformal_rand_const_reg``).

Usage example:

.. code-block:: systemverilog

   `rvformal_rand_reg [7:0] anyseq;
   `rvformal_rand_const_reg [7:0] anyconst;

For formal verification with Yosys (i.e. when ``YOSYS`` is defined),
this will be converted to the following code:

.. code-block:: systemverilog

   rand reg [7:0] anyseq;
   rand const reg [7:0] anyconst;

For simulation (i.e. when ``SIMULATION`` is defined), this will be
converted to:

.. code-block:: systemverilog

   reg [7:0] anyseq;
   reg [7:0] anyconst;

And otherwise (for use with any formal verification tool):

.. code-block:: systemverilog

   wire [7:0] anyseq;
   reg [7:0] anyconst;
