RISC-V Formal Interface (RVFI)
==============================

RVFI specification
------------------

In the following specification the term ``XLEN`` refers to the width of
an ``x`` register in bits, as described in the RISC-V ISA specification.
The term ``NRET`` refers to the maximum number of instructions that the
core under test can retire in one cycle. If more than one of the retired
instruction writes the same register, the channel with the highest index
contains the instruction that wins the conflict. The term ``ILEN``
refers to the maximum instruction width for the processor under test.

The Interface consists only of output signals. Each signal is a
concatenation of ``NRET`` values of constant width, effectively creating
``NRET`` channels. For simplicity, the following descriptions refer to
one such channel. For example, we refer to ``rvfi_valid`` as a 1-bit
signal, not a ``NRET``-bits signal.

Instruction metadata
~~~~~~~~~~~~~~~~~~~~

.. code-block:: systemverilog

   output [NRET        - 1 : 0] rvfi_valid
   output [NRET *   64 - 1 : 0] rvfi_order
   output [NRET * ILEN - 1 : 0] rvfi_insn
   output [NRET        - 1 : 0] rvfi_trap
   output [NRET        - 1 : 0] rvfi_halt
   output [NRET        - 1 : 0] rvfi_intr
   output [NRET * 2    - 1 : 0] rvfi_mode
   output [NRET * 2    - 1 : 0] rvfi_ixl

When the core retires an instruction, it asserts the ``rvfi_valid``
signal and uses the signals described below to output the details of the
retired instruction. The signals below are only valid during such a
cycle and can be driven to arbitrary values in a cycle in which
``rvfi_valid`` is not asserted.

The ``rvfi_order`` field must be set to the instruction index. No
indices must be used twice and there must be no gaps. Instructions may
be retired in a reordered fashion, as long as causality is preserved
(register and memory write operations must be retired before the read
operations that depend on them).

``rvfi_insn`` is the instruction word for the retired instruction. In
case of an instruction with fewer than ``ILEN`` bits, the upper bits of
this output must be all zero. For compressed instructions the compressed
instruction word must be output on this port. For fused instructions the
complete fused instruction sequence must be output.

``rvfi_trap`` must be set for an instruction that cannot be decoded as a
legal instruction, such as 0x00000000.

In addition, ``rvfi_trap`` must be set for a misaligned memory read or
write in PMAs that don't allow misaligned access, or other memory access
violations. ``rvfi_trap`` must also be set for a jump instruction that
jumps to a misaligned instruction.

The signal ``rvfi_halt`` must be set when the instruction is the last
instruction that the core retires before halting execution. It should
not be set for an instruction that triggers a trap condition if the CPU
reacts to the trap by executing a trap handler. This signal enables
verification of liveness properties.

``rvfi_intr`` must be set for the first instruction that is part of a
trap handler, i.e. an instruction that has a ``rvfi_pc_rdata`` that does
not match the ``rvfi_pc_wdata`` of the previous instruction.

``rvfi_mode`` must be set to the current privilege level, using the
following encoding: 0=U-Mode, 1=S-Mode, 2=Reserved, 3=M-Mode

Finally ``rvfi_ixl`` must be set to the value of MXL/SXL/UXL in the
current privilege level, using the following encoding: 1=32, 2=64

Integer register read/write
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: systemverilog

   output [NRET *    5 - 1 : 0] rvfi_rs1_addr
   output [NRET *    5 - 1 : 0] rvfi_rs2_addr
   output [NRET * XLEN - 1 : 0] rvfi_rs1_rdata
   output [NRET * XLEN - 1 : 0] rvfi_rs2_rdata

``rvfi_rs1_addr`` and ``rvfi_rs2_addr`` are the decoded ``rs1`` and
``rs1`` register addresses for the retired instruction. For an
instruction that reads no ``rs1``/``rs2`` register, this output can have
an arbitrary value. However, if this output is nonzero then
``rvfi_rs1_rdata`` must carry the value stored in that register in the
pre-state.

``rvfi_rs1_rdata``/``rvfi_rs2_rdata`` is the value of the ``x`` register
addressed by ``rs1``/``rs2`` before execution of this instruction. This
output must be zero when ``rs1``/``rs2`` is zero.

.. code-block:: systemverilog

   output [NRET *    5 - 1 : 0] rvfi_rd_addr
   output [NRET * XLEN - 1 : 0] rvfi_rd_wdata

``rvfi_rd_addr`` is the decoded ``rd`` register address for the retired
instruction. For an instruction that writes no ``rd`` register, this
output must always be zero.

``rvfi_rd_wdata`` is the value of the ``x`` register addressed by ``rd``
after execution of this instruction. This output must be zero when
``rd`` is zero.

Program counter
~~~~~~~~~~~~~~~

.. code-block:: systemverilog

   output [NRET * XLEN - 1 : 0] rvfi_pc_rdata
   output [NRET * XLEN - 1 : 0] rvfi_pc_wdata

This is the program counter (``pc``) before (``rvfi_pc_rdata``) and
after (``rvfi_pc_wdata``) execution of this instruction. I.e. this is
the address of the retired instruction and the address of the next
instruction.

Memory access
~~~~~~~~~~~~~

.. code-block:: systemverilog

   output [NRET * XLEN   - 1 : 0] rvfi_mem_addr
   output [NRET * XLEN/8 - 1 : 0] rvfi_mem_rmask
   output [NRET * XLEN/8 - 1 : 0] rvfi_mem_wmask
   output [NRET * XLEN   - 1 : 0] rvfi_mem_rdata
   output [NRET * XLEN   - 1 : 0] rvfi_mem_wdata

For memory operations (``rvfi_mem_rmask`` and/or ``rvfi_mem_wmask`` are
non-zero), ``rvfi_mem_addr`` holds the accessed memory location.

When the define ``RISCV_FORMAL_ALIGNED_MEM`` is set, the address must
have a 4-byte alignment for ``XLEN=32`` and an 8-byte alignment for
``XLEN=64``. When the define is not set, then the address must point
directly to the LSB or the word / half word / byte that is accessed.

``rvfi_mem_rmask`` is a bitmask that specifies which bytes in
``rvfi_mem_rdata`` contain valid read data from ``rvfi_mem_addr``.

``rvfi_mem_wmask`` is a bitmask that specifies which bytes in
``rvfi_mem_wdata`` contain valid data that is written to
``rvfi_mem_addr``.

``rvfi_mem_rdata`` is the pre-state data read from ``rvfi_mem_addr``.
``rvfi_mem_rmask`` specifies which bytes are valid.

``rvfi_mem_wdata`` is the post-state data written to ``rvfi_mem_addr``.
``rvfi_mem_wmask`` specifies which bytes are valid.

When ``RISCV_FORMAL_ALIGNED_MEM`` is set then ``riscv-formal`` assumes
that unaligned memory access causes a trap.

.. _rvfi-alt-arith:

Alternative arithmetic operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some arithmetic operations (such as multiplication and division) are
beyond to practical capabilities of even modern hardware model checkers.
In order to still be able to verify things like bypassing for the
arithmetic units performing those operations we define a set of
alternative arithmetic operations. When the define
``RISCV_FORMAL_ALTOPS`` is set riscv-formal will expect the processor
under test to implement those alternative operations instead.

Commutative operations (like multiplication) are replaced with addition
followed by applying XOR with a bitmask that indicates the type of the
operation. Noncommutative operations (like division) are replaced with
subtraction followed by applying XOR with a bitmask that indicates the
type of the operation.

The bitmasks are 64 bits wide. RV32 implementations only use the lower
32 bits of the bitmasks. The ``*W`` instructions in RV64 (such as
``MULW``) are implemented by adding or subtracting the lower 32 bits of
the operands, then XORing with the lower 32 bits of the bitmask, then
sign extending the result to 64 bits.

Integer multiply/divide instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..  for n in MUL{,H,HSU,HU} DIV{,U} REM{,U}; do echo "$( echo -n $n | md5sum ) $n"; done | cut -c1-16,36-

========= ======= ==================
Operation Add/Sub Bitmask
========= ======= ==================
MUL       Add     0x2cdf52a55876063e
MULH      Add     0x15d01651f6583fb7
MULHSU    Sub     0xea3969edecfbe137
MULHU     Add     0xd13db50d949ce5e8
DIV       Sub     0x29bbf66f7f8529ec
DIVU      Sub     0x8c629acb10e8fd70
REM       Sub     0xf5b7d8538da68fa5
REMU      Sub     0xbc4402413138d0e1
========= ======= ==================

.. _rvfi-csrs:

Control and Status Registers (CSRs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each supported CSR there are four additional output ports:

.. code-block:: systemverilog

   output [NRET * XLEN - 1 : 0] rvfi_csr_<csrname>_rmask
   output [NRET * XLEN - 1 : 0] rvfi_csr_<csrname>_wmask
   output [NRET * XLEN - 1 : 0] rvfi_csr_<csrname>_rdata
   output [NRET * XLEN - 1 : 0] rvfi_csr_<csrname>_wdata

The ``rmask`` and ``wmask`` ports specify which bits of ``rdata`` and
``wdata`` are valid.

It is always valid for an instruction to activate more
``rmask``/``rdata`` bits than required by the instruction, as long as
the reported bits correctly reflect the machine state.

If reading a CSR has side effects, those side effects are not triggered
by raised ``rmask`` bits but by the type of the instruction.

The Verilog define ``RISCV_FORMAL_CSR_<CSRNAME>`` must be set for each
CSR traced via RVFI by the core under test.

See :doc:`csrs` for the exact semantics of CSR values output via RVFI.

Handling of speculative execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Out-of-order cores that execute speculatively can commit speculative
instructions on RVFI.

Rollbacks must be output via the rollback interface, that is enabled
when ``RISCV_FORMAL_ROLLBACK`` is defined:

.. code-block:: systemverilog

   output [ 0 : 0] rvfi_rollback_valid
   output [63 : 0] rvfi_rollback_order

All RVFI packets output *prior* to the cycle with asserted
``rvfi_rollback_valid`` with a ``rvfi_order`` field of *greater or
equal* to ``rvfi_rollback_order`` are invalidated by a rollback event.

RVFI packets output in the same cycle as ``rvfi_rollback_valid`` are
already part of the new instruction stream re-starting at the
instruction number indicated in ``rvfi_rollback_order``.

Handling of dynamic faults
~~~~~~~~~~~~~~~~~~~~~~~~~~

Cores where the fault check for an instruction fetch or a data access is
determined by an external bus response can signal such faults via RVFI.

When ``RISCV_FORMAL_MEM_FAULT`` is defined, the RVFI interface is
extended by the following signal:

.. code-block:: systemverilog

   output [NRET          - 1 : 0] rvfi_mem_fault
   output [NRET * XLEN/8 - 1 : 0] rvfi_mem_fault_rmask
   output [NRET * XLEN/8 - 1 : 0] rvfi_mem_fault_wmask

An instruction fetch that faults sets ``rvfi_insn`` to all zero and set
``rvfi_mem_fault``. A memory access that faults sets ``rvfi_mem_fault``
and does not signal any register or memory writes. Instead the bytes
that would have been accessed (if the access hadn't faulted) are output
to ``rvfi_mem_fault_rmask`` and ``rvfi_mem_fault_wmask`` instead. The
address is still output via ``rvfi_mem_addr``.

Handling of external memory busses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

RISC-V Formal includes several checks that verify consistency properties
between memory accesses observed via the RVFI and memory accesses
observed on external instruction and/or data busses. To not tie those
checks to a specific bus, those checks extend the RVFI with the RVFI_BUS
interface. RVFI_BUS consists of further outputs that observe memory
accesses on a bus while abstracting over the exact signalling used for
the bus.

To run these checks, the relevant busses of the core should be connected
to an abstraction that implements the required bus signalling but
provides unconstrai (This may be relaxed with an extensions )ned
responses to the core. The accesses on the bus are then observed and
constrained by these checks via the RVFI_BUS outputs.

Note: When implementing such an abstraction it should output the access
using RVFI_BUS as soon as the access first appears on the bus, even when
the reply to the core happens in a later cycle. (Whether this is
necessary and how much delay is acceptable depends on the checks
performed and on the design of the core and the core's RVFI
implementation. Too much delay can cause false positives by preventing
the check from properly constraining the RVFI_BUS transfers.)

For standard busses the same unconstrained abstractions and RVFI_BUS
observers can be re-used for multiple cores.

The RVFI_BUS extension can observe multiple busses using multiple
RVFI_BUS channels. This is used to model separate data and instruction
busses as well as busses that can transfer accesses to several unrelated
addresses in the same cycle. The total number of channels is specified
using ``NBUS`` which works like ``NRET`` for the main RVFI signals. The
width of the observed bus is independent of ``XLEN`` and is specified
using ``BUSLEN``. If different channels observe busses of a different
width, ``BUSLEN`` should be set to the maximum width in use.

RVFI_BUS adds the following ouptuts:

.. code-block:: systemverilog

   output [NBUS *      1   - 1 : 0] rvfi_bus_valid
   output [NBUS *      1   - 1 : 0] rvfi_bus_insn
   output [NBUS *      1   - 1 : 0] rvfi_bus_data
   output [NBUS *      1   - 1 : 0] rvfi_bus_fault
   output [NBUS *   XLEN   - 1 : 0] rvfi_bus_addr
   output [NBUS * BUSLEN/8 - 1 : 0] rvfi_bus_rmask
   output [NBUS * BUSLEN/8 - 1 : 0] rvfi_bus_wmask
   output [NBUS * BUSLEN   - 1 : 0] rvfi_bus_rdata
   output [NBUS * BUSLEN   - 1 : 0] rvfi_bus_wdata

When ``rvfi_bus_valid`` is set, there is an observed memory access
present on the RVFI_BUS channel, otherwise, all other RVFI_BUS outputs
are ignored.

The outputs ``rvfi_bus_insn`` and ``rvfi_bus_data`` are used to indicate
whether the access is an instruction fetch or a data access. For cores
or busses that do not distinguish between those, both have to be set.

The ``rvfi_bus_addr`` output is the address of the access.

The outputs ``rvfi_bus_rmask`` and ``rvfi_bus_wmask`` indicate which
bytes starting with ``rvfi_bus_addr`` are accessed. This is used for
both, masked writes as well as for outputting busses smaller than
``BUSLEN``. Note that when the LSBs of ``rvfi_bus_rmask`` and
``rvfi_bus_wmask`` are cleared, ``rvfi_bus_addr`` may be lower than the
first actually accessed byte.

The outputs ``rvfi_bus_rdata`` and ``rvfi_bus_wdata`` contain the read
and written data and are only valid for the bytes corresponding to the
respective bits in ``rvfi_bus_rmask`` and ``rvfi_bus_wmask``.

All accesses observed using RVFI_BUS are assumed to be in order,
including acceses in the same cycle which are ordered by increasing
RVFI_BUS channel index. This may be relaxed by future extensions.

RVFI_BUS observers for standard interfaces
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``bus`` directory contains implementations RVFI_BUS observers and
abstractions for standard interfaces.

Note that the observers are passive and do not constrain any signals on
their own. That means to test a core in isolation, the core's interface
may have to be connected to an abstraction that provides the handshaking
that the core expects to properly function without constraining the data
or timing beyond that.

AXI4 observers and abstractions are provided in
``bus/rvfi_bus_axi4.sv``, which also contains some notes about the
timing when translating AXI4 into RVFI_BUS signals.

RVFI TODOs and requests for comments
------------------------------------

The following section contains notes on future extensions to RVFI. They
will come part of the spec as soon as there is at least one core that
implements the feature, and a matching formal check that utilises the
feature. In many cases the additional ports will only be used (and
expected from the core) when additional to-be-defined ``RISCV_FORMAL_*``
Verilog defines are set.

Support for fused instructions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fused instructions are simply handled as larger instructions in RVFI.
Additional ``rvfi_rs*`` ports (or even ``rvfi_rd*`` ports) may be added
to accommodate the fused instructions.

No instruction models for fused instructions have been created yet.

Alternatively fused instructions may be output as individual
instructions in separate RVFI channels.

Modelling of Floating-Point State
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following is the proposed RVFI extension for floating point ISAs:

.. code-block:: systemverilog

   output [NRET *    5 - 1 : 0] rvfi_frs1_addr
   output [NRET *    5 - 1 : 0] rvfi_frs2_addr
   output [NRET *    5 - 1 : 0] rvfi_frs3_addr
   output [NRET *    5 - 1 : 0] rvfi_frd_addr
   output [NRET        - 1 : 0] rvfi_frs1_rvalid
   output [NRET        - 1 : 0] rvfi_frs2_rvalid
   output [NRET        - 1 : 0] rvfi_frs3_rvalid
   output [NRET        - 1 : 0] rvfi_frd_wvalid
   output [NRET * FLEN - 1 : 0] rvfi_frs1_rdata
   output [NRET * FLEN - 1 : 0] rvfi_frs2_rdata
   output [NRET * FLEN - 1 : 0] rvfi_frs3_rdata
   output [NRET * FLEN - 1 : 0] rvfi_frd_wdata
   output [NRET * XLEN - 1 : 0] rvfi_csr_fcsr_rmask
   output [NRET * XLEN - 1 : 0] rvfi_csr_fcsr_wmask
   output [NRET * XLEN - 1 : 0] rvfi_csr_fcsr_rdata
   output [NRET * XLEN - 1 : 0] rvfi_csr_fcsr_wdata

Since ``f0`` is not a zero register, additional ``*_[rw]valid`` signals
are required to indicate if ``frs1``, ``frs2``, ``frs3``, and ``frd``
and their corresponding pre- or post-values are valid.

Alternative arithmetic operations (``RISCV_FORMAL_ALTOPS``) will be
defined for all non-trivial floating point operations.

Modelling of Virtual Memory
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For processors with support for S-mode and virtual memory we define the
following additional RVFI signals for data load/stores:

.. code-block:: systemverilog

   output [NRET *   64 - 1 : 0] rvfi_mem_paddr
   output [NRET * XLEN - 1 : 0] rvfi_mem_pte0
   output [NRET * XLEN - 1 : 0] rvfi_mem_pte1
   output [NRET * XLEN - 1 : 0] rvfi_mem_pte2
   output [NRET * XLEN - 1 : 0] rvfi_mem_pte3

And the following additional RVFI signals for instruction fetches:

.. code-block:: systemverilog

   output [NRET *   64 - 1 : 0] rvfi_pc_paddr
   output [NRET * XLEN - 1 : 0] rvfi_pc_pte0
   output [NRET * XLEN - 1 : 0] rvfi_pc_pte1
   output [NRET * XLEN - 1 : 0] rvfi_pc_pte2
   output [NRET * XLEN - 1 : 0] rvfi_pc_pte3

And we require that the ``satp`` CSR is observable through RVFI:

.. code-block:: systemverilog

   output [NRET * XLEN - 1 : 0] rvfi_csr_satp_rmask
   output [NRET * XLEN - 1 : 0] rvfi_csr_satp_wmask
   output [NRET * XLEN - 1 : 0] rvfi_csr_satp_rdata
   output [NRET * XLEN - 1 : 0] rvfi_csr_satp_wdata

The ``rvfi_mem_paddr`` field carries the physical address of the memory
access. The ``rvfi_mem_pte[0123]`` fields carry the values of the page
table entries used to convert ``rvfi_mem_addr`` to ``rvfi_mem_paddr``.
Unused ``rvfi_mem_pte[0123]`` fields must always be set to zero.

For memory accesses in M-mode, or with ``satp.MODE=0``,
``rvfi_mem_paddr`` must have the same value as ``rvfi_mem_addr`` and all
four ``rvfi_mem_pte[0123]`` fields must be set to zero.

For example in Sv32 mode, modulo missing fences, ``rvfi_mem_pte1`` must
carry the value of the 32-bit word at the following memory location:

::

   pt1 = rvfi_csr_satp_rdata & 0x003fffff
   vpn1 = (rvfi_mem_addr >> 22) & 0x3ff
   pte1_addr = (pt1 << 12) | (vpn1 << 2)

And ``rvfi_mem_pte0`` must carry the value of the 32-bit word at the
following memory location (or zero if ``pte1.X`` or ``pte1.R`` or
``!pte1.V``):

::

   pt0 = rvfi_mem_pte1 >> 10
   vpn0 = (rvfi_mem_addr >> 12) & 0x3ff
   pte0_addr = (pt0 << 12) | (vpn0 << 2)

Finally, ``rvfi_mem_paddr`` must be set to the following address:

::

   ppn = rvfi_mem_pte0 >> 10
   offset = rvfi_mem_addr & 0xfff
   rvfi_mem_paddr = (ppn << 12) | offset

Modelling of Atomic Memory Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AMO instructions (``AMOSWAP.W``, etc.) can be modelled using the
existing ``rvfi_mem_*`` interface by asserting bits in both
``rvfi_mem_rmask`` and ``rvfi_mem_wmask``.

There is also no extension to the RVFI port necessary to accommodate the
``LR``, ``SC``, ``FENCE`` and ``FENCE.I`` instructions.

Verification of this instructions for a single-core systems can be done
using the RVFI port only. A strategy must be defined to verify their
correct behavior in multicore systems.

For atomic instructions with ``rd = x0`` a core might have no way of
knowing the old or new value of the memory location. For those
situations we add an additional RVFI output port:

.. code-block:: systemverilog

   output [NRET          - 1 : 0] rvfi_mem_extamo

When ``rvfi_mem_extamo`` is set, ``rvfi_mem_wdata`` carries the ``rs2``
value used with the atomic instruction instead of the new value in the
memory location. ``rvfi_mem_rmask`` is all-zeros in this case.

Skipping instructions
~~~~~~~~~~~~~~~~~~~~~

Consider the following sequence of instructions:

::

       ....
       add t0,t1,t2
       beqz t3,label
       sub t0,t1,t3
   label:
       ....

When t3 has a non-zero value the processor could decide not to schedule
the add instruction because its value is never going to be used. In this
case the processor would be unable to produce a valid RVFI trace for the
instruction sequence.

An additional signal can be added to RVFI that can be used to mark such
instructions:

.. code-block:: systemverilog

   output [NRET        - 1 : 0] rvfi_skip

When ``rvfi_skip`` is high the core may output arbitrary data on the
``*_rdata`` and ``*_wdata`` ports (excluding ``rvfi_pc_rdata`` and
``rvfi_pc_wdata``). The register values written by such intrustions may
only be observed by other skipped instructions. An additional formal
proof must be added to check this property.

Memory operations (``rvfi_mem_rmask`` and/or ``rvfi_mem_wmask`` are
non-zero) can not be skipped.
