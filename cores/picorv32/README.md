
riscv-formal proofs for picorv32
================================

Quickstart guide:

First install Yosys, SBY, and the solvers. See the 
[SBY Installation Guide](https://yosyshq.readthedocs.io/projects/sby/en/latest/install.html)
for instructions.  Then download the core, generate the formal checks and run them:

```
make check -j$(nproc)
```

