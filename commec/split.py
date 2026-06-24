#!/usr/bin/env python3
# Copyright (c) 2021-2024 International Biosecurity and Biosafety Initiative for Science
"""
Split a multi-record FASTA file into individual files, one for each record.

Command-line usage:
    split.py input.fasta
"""

import os
from pathlib import Path
import string

from needletail import parse_fastx_file
import typer

VALID_FILENAME_CHARS = f"-._{string.ascii_letters}{string.digits}"


def _clean_description(description):
    """
    Cleans the description from a sequence record for use as part of a filename.
    """
    cleaned = description.strip()
    cleaned = "".join(x for x in cleaned if x in VALID_FILENAME_CHARS)
    if len(cleaned) > 150:
        cleaned = cleaned[:150]
    return cleaned


def _write_split_fasta(fasta_file):
    """
    Parse all sequence records in an input FASTA file, and write a new file for each record.
    """
    output_dir = os.path.dirname(fasta_file)
    fasta_name = os.path.splitext(os.path.basename(fasta_file))[0]

    for i, record in enumerate(parse_fastx_file(fasta_file)):
        desc = _clean_description(record.description)

        # Handle empty descriptions and avoid overwriting input files
        if not desc or desc == fasta_name:
            output_basename = f"{fasta_name}-split-{i}.fasta"
        else:
            output_basename = f"{desc}.fasta"

        output_path = os.path.join(output_dir, output_basename)
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(f">{desc}{os.linesep}")
            output_file.write(str(record.seq))


def main(fasta_file: Path):
    """Split a multi-record FASTA file into individual files, one for each record."""
    _write_split_fasta(fasta_file)


if __name__ == "__main__":
    typer.run(main)
