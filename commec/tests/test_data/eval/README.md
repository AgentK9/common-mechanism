# Evaluation (detection) test cases

This directory holds **end-to-end detection test cases** for `commec screen`, driven by
`commec/tests/test_evaluation.py`. Unlike the mocked logic tests, these run the real
pipeline against real reference databases and check that known sequences produce the
expected screening outcome.

## How it works

Each **subfolder** of this directory is one test case. A subfolder is collected as a case
when it contains a `metadata.yaml` (or `metadata.yml`) file. The harness:

1. discovers every case subfolder (folders starting with `_` or `.` are ignored — use
   them for templates/notes, like `_template/`);
2. runs `commec screen` on the case's FASTA against the database directory you provide;
3. compares the resulting per-query statuses (and optional hit/rationale checks) against
   the `expected` block in `metadata.yaml`.

Because the reference databases are large and not in the repo, these tests are **skipped**
unless you point them at a database directory:

```bash
pytest commec/tests/test_evaluation.py --commec-db-dir /path/to/commec-dbs
# or:
COMMEC_DB_DIR=/path/to/commec-dbs pytest commec/tests/test_evaluation.py
```

## Layout of a case

```
eval/
  my_case_name/
    metadata.yaml          # required — describes the case and expected outcomes
    sequence.fasta         # the input to screen
```

By default a case has exactly one FASTA file and that file holds a single record. A FASTA
may hold multiple records (e.g. to test "distribution attacks" that split a sequence of
concern across records); just add an `expected` entry per record id.

## `metadata.yaml` schema

```yaml
# Human-readable description (optional, recommended).
name: dataset_name
description: >
  Dataset Description

# Which FASTA to screen (optional). If omitted, the single *.fasta in the folder is used.
fasta: sequence.fasta

# Extra CLI args passed verbatim to `commec screen` (optional). e.g. ["--skip-nt"].
screen_args: []

# Expected outcomes (required).
#
# Two forms are accepted:
#
# (A) Single-query shorthand — write the status fields directly. Only valid when the
#     FASTA produces exactly one query:
expected:
  screen_status: Flag          # overall outcome (required)
  biorisk: Flag                # per-step expectations (all optional)
  protein_taxonomy: Flag
  nucleotide_taxonomy: Pass
  low_concern: Pass
  hits: []                     # optional: hit names that MUST be present for the query
  rationale_contains: []       # optional: substrings that MUST appear in the rationale

# (B) Per-query form — key by FASTA record id (the header up to the first space).
#     Use this for multi-record FASTAs:
#
# expected:
#   record_id_1:
#     screen_status: Flag
#     biorisk: Flag
#   record_id_2:
#     screen_status: Pass
```

### Status values

Status fields accept either the human-readable enum value or the enum name (case
sensitive for the value, case-insensitive for the name):

| Name           | Value               |
|----------------|---------------------|
| `NULL`         | `-`                 |
| `SKIP`         | `Skip`              |
| `SKIP_SHORT`   | `Skip (too short)`  |
| `SKIP_LONG`    | `Skip (too long)`   |
| `PASS`         | `Pass`              |
| `CLEARED_WARN` | `Warning (Cleared)` |
| `CLEARED_FLAG` | `Flag (Cleared)`    |
| `WARN`         | `Warning`           |
| `FLAG`         | `Flag`              |
| `STOP`         | `Incomplete`        |
| `ERROR`        | `Error`             |

So `screen_status: Flag` and `screen_status: FLAG` are equivalent.

Only the fields you specify are checked — omit a step's field to leave it unasserted.
