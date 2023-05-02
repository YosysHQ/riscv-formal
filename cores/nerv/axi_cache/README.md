# Caches for NERV using an AXI interface


## Contents

### Cache Implementation

Split across [`nerv_axi_cache.sv`](./nerv_axi_cache.sv), [`nerv_axi_cache_icache.sv`](./nerv_axi_cache_icache.sv) and [`nerv_axi_cache_dcache.sv`](./nerv_axi_cache_dcache.sv).

The top-level module for the cache is `nerv_axi_cache` in [`nerv_axi_cache.sv`](./nerv_axi_cache.sv).
Module parameters are documented in the comment above that module.

### Testbenches

The testbenches were tested using `iverilog`, use `make test_axi` and `make test_internal` for running them.
There is [`testbench_internal.sv`](./testbench_internal.sv) which uses the cache-internal bus instead of the AXI interface and [`testbench_axi.sv`](./testbench_axi.sv) which uses the full AXI-interfacing cache together with a third-party open-source AXI4 memory implementation in [`axi_ram.v`](./axi_ram.v) (Taken from [Alex Forencich's "Verilog AXI Components"](https://github.com/alexforencich/verilog-axi)).

These testbenches also uses a different firmware than the top-level NERV testbench to actually exercise the cache a bit.

### Formal Verification Using SVA AXI Properties

The caches' AXI interface is formally verified using the [YosysHQ SVA AXI Properties](https://github.com/YosysHQ-GmbH/SVA-AXI4-FVIP).
Use `make verify_axi` to run this verification.

The verification is setup in [`verify_axi.sby`](./verify_axi.sby) and [`verify_axi.sv`](./verify_axi.sv).

Note that SVA-AXI4-FVIP requires SVA support and thus this part requires the Tabby CAD Suite and does not work with the OSS CAD Suite. This limitation does not apply to verifying NERV using riscv-formal.

### RISC-V Formal Bus Checks

The caches' correct operation when used together with the NERV core is formally verified using riscv-formal's bus memory checks.

This can be done for the complete caches using the AXI interface, using `make checks_axi`, as well as for the cache internal interface using `make checks_internal`.

The riscv-formal configurations are in [`checks_axi.cfg`](./checks_axi.cfg) and [`checks_internal.cfg`](./checks_internal.cfg). The RVFI wrappers are [`wrapper_axi.sv`](./wrapper_axi.sv) and [`wrapper_internal.sv`](./wrapper_internal.sv).

The RVFI wrapper for the AXI setup also uses a modified version of  [`axi_ram.v`](./axi_ram.v) in which the actual memory is removed and read data is unconstrained. This modified version is contained in [`axi_ram_abstraction.v`](./axi_ram_abstraction.v).
