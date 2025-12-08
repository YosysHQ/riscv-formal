BAD-NERV - Naive Educational RISC-V Processor
=============================================

it's NERV but broken in specific ways to test riscv-formal

tesbug0xx
---------

These check config parsing.  Not all of these are bugs/errors and may instead
call ``exit`` in Yosys, which is not recognized as a valid command in scripts,
producing an SBY ``ERROR`` state.

- 000-002: script-* sections are inserted relative to ``read`` and ``prep``
- 003-005: defines and script-defines sections can be specified per-check

testbug1xx
----------

rvfi errors

testbug2xx
----------

instruction errors

testbug3xx
----------

csr errors

testbug 4xx
-----------

memory errors
