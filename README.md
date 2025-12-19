
RISC-V Formal Verification Framework
====================================

**This is work in progress. The interfaces described here are likely to change as the project matures.**

About
-----

`riscv-formal` is a framework for formal verification of RISC-V processors.

It consists of the following components:
- A processor-independent formal description of the RISC-V ISA
- A set of formal testbenches for each processor supported by the framework
- The specification for the [RISC-V Formal Interface (RVFI)](docs/source/rvfi.rst) that must be
  implemented by a processor core to interface with `riscv-formal`.
- Some auxiliary proofs and scripts, for example to prove correctness of the ISA spec against
  riscv-isa-sim.

See [cores/picorv32/](cores/picorv32/) for example bindings for the PicoRV32 processor core.

A processor core usually will implement RVFI as an optional feature that is only enabled for verification. Sequential equivalence check can be used to prove equivalence of the processor versions with and without RVFI.

The current focus is on implementing formal models of all instructions from the RISC-V RV32I and RV64I ISAs, and formally verifying those models against the models used in the RISC-V "Spike" ISA simulator.

`riscv-formal` uses the FOSS formal verification tool, [SBY](https://github.com/yosyshq/sby). All properties are expressed using immediate assertions/assumptions for maximal compatibility with other tools.

Documentation is available at https://riscv-formal.readthedocs.io/.

Running `riscv_formal`
----------------------

We recommend using [uv](https://docs.astral.sh/uv/) for managing the `riscv_formal` package.

1. Follow uv installation instructions, https://docs.astral.sh/uv/getting-started/installation/
2. From the root directory, run `uv sync --directory cli`
3. Activate the generated virtual environment with `source cli/.venv/bin/activate`
4. You should now be able to call (e.g.) `riscv_formal --help`

Configuring a new RISC-V processor
----------------------------------

1. Write a wrapper module that instantiates the core under test and abstracts models of necessary
   peripherals (usually just memory)
   - Use the [RVFI helper macros](docs/source/config.rst#rvfi_wires-rvfi_outputs-rvfi_inputs-rvfi_conn)
     `RVFI_OUTPUTS` and `RVFI_CONN` for quickly defining wrapper connections
   - See [picorv32/wrapper.sv](cores/picorv32/wrapper.sv) for a simple example wrapper
2. Write a `<checks>.cfg` config file for the new core
   - See [nerv/checks.cfg](cores/nerv/checks.cfg) for an example utilising most of the checks
   - Refer to [The riscv-formal Verification Procedure](docs/source/procedure.rst) for a complete
     guide on available checks, and a more detailed view of using `riscv_formal`
3. Generate checks with `riscv_formal <checks>.cfg genchecks`
   - A `<checks>` folder is created in the current working directory
4. Run checks with `make -C <checks> j$(nproc)`

### Notes

- The [quickstart guide](docs/source/quickstart.rst) goes through the process of running `riscv-formal` with
  some of the included cores.  It is recommended to follow this guide before adding a new core.
- See [picorv32/Makefile](cores/picorv32/Makefile) for an example makefile to manage generation and
  execution of checks.
- Refer to [docs/source/config.rst](docs/source/config.rst) and [docs/source/procedure.rst](docs/source/procedure.rst) for a
  breakdown of how to use checks generated from `riscv_formal` with custom scripts/testbenches.
- The [cover check](docs/source/procedure.rst#cover) can be used to help determine the depth needed for the
  core to reach certain states as needed for other checks.

Funding
-------

`riscv-formal` checks for memory buses, CSRs, and the B extension were made
possible with funding from Sandia National Laboratories.

Sandia National Laboratories is a multimission laboratory operated by National
Technology and Engineering Solutions of Sandia LLC, a wholly owned subsidiary of
Honeywell International Inc., for the U.S. Department of Energy's National
Nuclear Security Administration. Sandia Labs has major research and development
responsibilities in nuclear deterrence, global security, defense, energy
technologies and economic competitiveness, with main facilities in Albuquerque,
New Mexico, and Livermore, California.
