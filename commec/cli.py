#!/usr/bin/env python3
# Copyright (c) 2021-2024 International Biosecurity and Biosafety Initiative for Science
"""
Command-line entrypoint for the package. Calls `screen.py`, `flag.py` and `split.py` as subcommands.

The subcommands:
    screen  Run Common Mechanism screening on an input FASTA.
    flag    Parse all .screen files in a directory and create two CSVs file of flags raised
    split   Split a multi-record FASTA file into individual files, one for each record

Command-line usage:
    - commec screen -d /path/to/databases input.fasta
    - commec flag /path/to/directory/with/output.screen
    - commec split input.fasta
    - commec -h, --help
    - commec -v, --version
"""

import typer
from commec.flag import main as flag
from commec.screen import main as screen
from commec.setup import main as setup
from commec.split import main as split


commec = typer.Typer(no_args_is_help=True)

commec.command("screen")(screen)
commec.command("flag")(flag)
commec.command("split")(split)
commec.command("setup")(setup)


def main():
    commec()


if __name__ == "__main__":
    commec()
