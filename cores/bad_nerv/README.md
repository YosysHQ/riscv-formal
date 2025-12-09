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

- 201: ADD always returns 0 if rs1=x0
- 202: ADD ignores MSb of rs1
- 203: ADD skips write back if result is 0
- 204: ADD output doesn't change if the instruction hasn't changed

testbug3xx
----------

csr errors

- 301: Writes to MIE change rs1_value when rs1=x0

testbug 4xx
-----------

memory errors

- 401: Reads from address 0 always return 0
- 402: As above, but rvfi sees the true value
