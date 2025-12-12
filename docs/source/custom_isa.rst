.. default-role:: py:obj

.. py:currentmodule:: riscv_formal

Defining custom ISA extensions
==============================

- Call ``riscv_formal`` with ``--load <extension>``
- ``<extension>`` must be a path to a valid Python module, may be source
  code (``.py``) or precompiled file (e.g. ``.so`` or ``.pyc``)
- module can register extension compositions (e.g. "B" is composed of
  "Zba", "Zbb", and "Zbs" with `Isa.register_composition()`) and
  dependencies (e.g. "Zicntr" depends on "Zicsr" with
  `Isa.register_dependency()`)
- custom instructions and csr generators (factories may be a more
  pythonic name?) can also be registered for callback

  - callback functions must be of the form ``(isa_mods: Iterable[str])
    -> NamedSet[Csr] | NamedSet[Instruction]`` (maybe change to just be
    ``Iterable`` on the return type?)
  - one or more extensions which use that generator

- When loading the configuration file, ``riscv_formal`` will iterate
  over all extensions in the ``isa`` option
- compositions are expanded, dependencies are checked, and generators
  are called

  + generators are called with the set of extensions in the current
    configuration (``isa_mods``)
  + each generator is only called once; 

The `GenericChecker` class
--------------------------

- `Csr` and `Instruction` are both subclasses of this
- methods starting with ``_v_`` are used during
  `GenericChecker.to_verilog()` for generating verilog code
- by default, `GenericChecker.xlen` is the only class variable required
  to be set before calling `GenericChecker.to_verilog()`

  + this is done to allow optimizations to be performed based on the
    maximum supported xlen (the value assigned to ``RISCV_FORMAL_XLEN``)
    and is distinct from the current xlen, ``rvfi_ixl``
  + most built in tests are not setup to handle ``rvfi_ixl !=
    RISCV_FORMAL_XLEN``, though that may change in the future

- subclasses can specify other class variables required for verilog
  conversion with e.g. ``class MyInstruction(Instruction,
  required_v_args=["my_arg"])``

  + an error will be raised if any such variables are not assigned
    before calling ``to_verilog()`` on an instance of the corresponding
    class
  + this can be used to perform additional configuration of the verilog
    output based on the ``isa_mods`` argument during generator callback,
    while still providing useful error messages without manually
    checking that a value is set

Custom instructions
-------------------

- `Isa.register_generator()` to register callback function

  + return the set of all available instruction checks, `Instruction`
  + may return instructions for all supported extensions, or only for
    the current configuration (``isa_mods``)
  + `Instruction.extension` field should be set to the extension or
    extensions which provide that instruction

- use `Isa.register_non_insn_ext()` for extensions with no instruction checks
- if any extension in the current configuration does not have a
  generator callback, an error will be raised

.. TODO sail derived custom instructions

Defining instructions
~~~~~~~~~~~~~~~~~~~~~

- built in instruction generators available in ``riscv_formal/insns/``
  directory
- `insns.builtins` provides helper functions for quickly defining new
  instructions
- ``addi`` example uses `insns.builtins.insn_imm` with the mnemonic, the
  value of ``funct3``, and the (SystemVerilog) expression for the result

.. code-block:: python

   insn_imm("addi", "000", "rvfi_rs1_rdata + insn_imm")

.. code-block:: python

   def insn_imm(insn, funct3, expr, wmode=False, extension = "I"):
      return Instruction(
         name = insn,
         insn_format = FORMAT_I,
         opcode = "0011011" if wmode else "0010011",
         result = expr,
         extension = extension,
         sign_extend_from = 32 if wmode else None,
         xlen_min = 64 if wmode else 32,
         op_values = {
               "funct3": funct3,
         },
         imm = True,
      )

.. code-block:: python

   FORMAT_I = Instruction_format(
      "I-type", [
         ("imm12", 12),
         ("rs1", 5),
         ("funct3", 3),
         ("rd", 5),
         ("opcode", 7),
      ],
      imm = "$signed(insn_imm12)",
   )

Refer to `.Instruction` for more information about available arguments

Subclassing `Instruction`
~~~~~~~~~~~~~~~~~~~~~~~~~~

- built in subclasses in ``riscv_formal/insns/model.py``:

  + `MemoryInstruction` for reading/writing memory,
  + `AltopsInstruction` for use with ``RISCV_FORMAL_ALTOPS``, and 
  + `CsrInstruction` for instructions which access csrs.

- also `cext.C_Instruction` for compressed instructions in
  ``riscv_formal/insns/cext.py``

- `Instruction.included_in()` and `Instruction.valid_xlen()` are called
  to check if the instruction is available in the current configuration,
  by default checks are only generated if

  + any of the (space separated) extensions in `Instruction.extension`
    are enabled in the current configuration (``isa_mods``)
  + ``xlen_min<=RISCV_FORMAL_XLEN<=xlen_max`` (unless overridden by
    ``valid_xlen()``)


Custom csrs
-----------

- `CsrSpec.register_generator()`

  + return the set of all available csrs, `Csr`
  + must only include csrs for the current configuration (``isa_mods``)

- only required for extensions which include csrs

Defining csrs
~~~~~~~~~~~~~

- built in csr generators in ``riscv_formal/csrs/csr_spec.py``
- in general require a name, a width, and an index
- width should either be ``"xlen"`` (single index) or ``"64"`` (index
  and indexh) (feels like this could be automatic instead)
- privilege (e.g. "MRW") can be provided, or automatically determined by
  the index
- `Csr.has_macro_define` should only be set if the corresponding verilog
  macro definitions exist, should generally only be set for builtin csrs
- All other fields are assigned by `CsrSpec` based on test configuration

Subclassing csrs
~~~~~~~~~~~~~~~~

- built in subclasses in ``riscv_formal/csrs/csr.py``:

  + `ShadowCsr` for shadowing higher privilege csrs,
  + `MachineCsr` for csrs which can have shadows, and
  + `HpmeventCsr` for ``hpmevent`` csrs controlling a corresponding
    ``hpmcounter``.


Currently unsupported
---------------------

- optional csrs
- providing custom csrc behaviors to config file
- assigning default behavior checks (csrc)
- custom csrs which are always 64 bit in rvfi (like ``mcycle``)
- checking instructions which modify csr values (except for those
  provided by "Zicsr")
- specifying/checking supported values of ``rvfi_ixl`` at generation
  time
