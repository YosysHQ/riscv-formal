Welcome to the RISC-V Formal Verification Framework documentation!
==================================================================

``riscv-formal`` is a framework for formal verification of RISC-V
processors.  This framework is built around the :doc:`rvfi`, providing a
set of formal testbenches utilizing SystemVerilog Assertions (SVA).
These can be used to verify behaviour on this interface, and by
extension prove functional correctness of a RISC-V processor. Tests can
be generated for `SBY`_ automatically with the included Python scripts
or used as-is.

.. _SBY: https://github.com/YosysHQ/sby

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   rvfi
   csrs
   config
   procedure
   examplebugs
   references
