BAD-NERV - Naive Educational RISC-V Processor
=============================================

it's NERV but broken in specific ways to test riscv-formal

tesbug0xx
---------

These are configuration errors, many of which call ``exit`` in Yosys, which is
not recognized as a valid command in scripts, producing an SBY ``ERROR`` state.
