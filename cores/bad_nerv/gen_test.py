#!/bin/python3
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import click

# read-only class describing a given test configuration
@dataclass(frozen=True)
class BugCfg:
    # between 100 and 999 inclusive
    id: int
    # leave empty to include all checks
    filter_checks: list[str] = field(default_factory=list)

    @property
    def id_str(self) -> str:
        return f"{self.id:03d}"

    @property
    def name(self) -> str:
        return f"testbug{self.id_str}"


# list of all available test configurations
BUGS = [
    BugCfg(101, ["reg"]),
]

def get_bugs(testbug: str) -> Iterable[BugCfg]:
    for bug in BUGS:
        if testbug in [bug.id_str, bug.name, "all"]:
            yield bug

@click.command
@click.argument("testbug", default="all")
def run(testbug: str):
    """
    Generate the riscv-formal <TESTBUG>.cfg (e.g. "testbug101" or "101").
    Use "all" to generate all available.
    """
    with open("checks.cfg", "r") as checks_cfg:
        base_cfg = checks_cfg.readlines()

    valid_bug = False
    for bug in get_bugs(testbug):
        with open(f"{bug.name}.cfg", "w") as bug_cfg:
            click.echo(f"Writing to {bug_cfg.name}")
            for line in base_cfg:
                click.echo(line, bug_cfg, nl=False)
                if line.startswith("[defines]"):
                    # enable testbug
                    click.echo(f"`define NERV_TESTBUG_{bug.id_str}", bug_cfg)

            if bug.filter_checks:
                click.echo("", bug_cfg)
                click.echo("[filter-checks]", bug_cfg)
                for check in bug.filter_checks:
                    click.echo(f"+ {check}", bug_cfg)
                click.echo("- .*", bug_cfg)

        valid_bug = True

    if not valid_bug:
        click.echo(f"{testbug!r} did not match any known config!", err=True)
        exit(1)

if __name__ == "__main__":
    run()
