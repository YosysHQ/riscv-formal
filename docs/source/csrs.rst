CSR semantics
=============

For the most part the CSR values output via RVFI match exactly the CSR
values observable via the ISA. But there are a few minor differences
that are outlined here.

Most importantly, for RV64 processors in RV32 mode, the values output
via RVFI are still following RV64 CSR encondings, including some of the
information that is not available through the RV32 ISA, such as SXL and
UXL in ``mstatus``.

Counters are always output as singe 64-bit wide CSRs even on RV32
targets.

M-mode CSRs
-----------

Machine Information Registers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

mvendorid, marchid, mimpid, mhartid, mconfigptr
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These CSRs are mandatory and expected to be constant, but may be all 0.

Machine Trap Setup
~~~~~~~~~~~~~~~~~~

mstatus
^^^^^^^

Mandatory. (Reminder: RV64 processors in RV32 mode are expected to
output the RV64 format.) May be all 0, reserved bits must be 0
regardless of writes.

misa
^^^^

Can be read-only 0, but existence is mandatory. Reserved bits must be 0
regardless of writes.

medeleg, mideleg
^^^^^^^^^^^^^^^^

Only exist if S mode is supported.

mie, mtvec
^^^^^^^^^^

Mandatory.

mcounteren
^^^^^^^^^^

Currently only the ``IR`` and ``CY`` bits of ``mcounteren`` are
supported by riscv-formal. The other bits are ignored. mcounteren must
only exist if U mode is supported.

Machine Trap Handling
~~~~~~~~~~~~~~~~~~~~~

mscratch
^^^^^^^^

Nothing special for this CSR.

mepc
^^^^

The version of ``mepc`` observable through the ISA masks ``mepc[1]`` on
CSR reads when the processor is in a mode that does not supprt 16-bit
instruction alignment. However, writes to that bit shall still modify
the underlying architectural state.

In riscv-formal semantics the ``mepc`` value output via RVFI must be the
actual architectural state with ``mepc[1]`` not masked.

mcause, mtval, mip
^^^^^^^^^^^^^^^^^^

Nothing special for these CSRs.

Machine Protection and Translation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TBD

Machine Counter/Timers
~~~~~~~~~~~~~~~~~~~~~~

mcycle, minstret
^^^^^^^^^^^^^^^^

Always 64-bit wide, even on pure RV32 processors (no mcycleh/minstreth).

Incrementing those counters should happen “between instructions”, this
means for example that an instruction that isn't a CSR write to
``mcycle`` should always have
``rvfi_csr_mcycle_rdata == rvfi_csr_mcycle_wdata``.

mhpmcounter, mhpmevent
^^^^^^^^^^^^^^^^^^^^^^

Machine performance-monitoring counters are currently not supported by
riscv-formal.

CSR 0xFFF
~~~~~~~~~

This address is used as a catch-all to mean no address and thus is not
able to be tested normally.

Debug-Mode CSRs
---------------

TBD

U-Mode CSRs
-----------

TBD

S-Mode CSRs
-----------

TBD
