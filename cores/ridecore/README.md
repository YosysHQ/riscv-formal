# RISCV-Formal for RIDECORE

First install Yosys, SymbiYosys, and the solvers. See
[here](http://symbiyosys.readthedocs.io/en/latest/quickstart.html#installing)
for instructions. Then build the version of Ridecore with RVFI support and
generate the formal checks:

```
git submodule update --init
python3 ../../checks/genchecks.py
```

Then run the formal checks:

```
make -C checks
```
