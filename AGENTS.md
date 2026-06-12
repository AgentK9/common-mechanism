# AGENTS.md

Guidance for AI coding agents (and new human contributors) working in this repository.

## What this project is

`commec` is the command-line tool behind the [Common Mechanism for DNA Synthesis
screening](https://ibbis.bio/common-mechanism/), maintained by IBBIS. It takes an input
FASTA and screens each sequence for biosecurity concerns, producing a structured JSON
result, an HTML summary, and a human-readable `.screen` log.

The package installs a single entrypoint, `commec`, with four sub-commands (see
`commec/cli.py`):

| Sub-command | Module          | Purpose                                                            |
|-------------|-----------------|--------------------------------------------------------------------|
| `screen`    | `commec/screen.py` | Run screening on an input FASTA (the core pipeline).            |
| `flag`      | `commec/flag.py`   | Parse `.screen.json` files in a directory into a CSV of outcomes.|
| `setup`     | `commec/setup.py`  | Download the reference databases needed for screening.          |
| `split`     | `commec/split.py`  | Split a multi-record FASTA into one file per record.            |

## The screening pipeline

`commec screen` (see `Screen.run` in `commec/screen.py`) runs up to four steps, each of
which annotates a shared `ScreenResult` state object:

1. **Biorisk search** — HMM scan (`hmmscan`) against a curated biorisk profile DB.
2. **Protein taxonomy search** — BLASTX or DIAMOND against NCBI `nr`, to find best matches
   to regulated pathogens.
3. **Nucleotide taxonomy search** — BLASTN against `core_nt`, run only on non-coding
   regions (regions with no strong protein hit). Skippable with `--skip-nt`.
4. **Low-concern search** — three scans (conserved proteins via `hmmscan`, housekeeping
   RNAs via `cmscan`, synbio parts via `blastn`) that can *clear* protein/nucleotide hits
   (but never biorisk hits).

`--skip-tx` runs only the biorisk step.

## Code map

```
commec/
  cli.py               # Entrypoint dispatch for the four sub-commands
  screen.py            # Screen class: orchestrates the pipeline; argument parser lives here
  flag.py, split.py, setup.py
  config/
    result.py          # Output data model: ScreenResult > QueryResult > HitResult; the
                       #   ScreenStatus / ScreenStep enums; rationale-text generation
    json_io.py         # (De)serialize ScreenResult <-> JSON (dataclass <-> dict <-> file)
    query.py           # Query object: parsed FASTA record, translation, coordinates
    screen_io.py       # ScreenIO: argument/YAML config resolution, file path layout
    screen_tools.py    # ScreenTools: wires up + validates the search-tool wrappers
    constants.py       # MIN/MAX query length, e-value thresholds, thread limits
  screeners/
    check_biorisk.py, check_reg_path.py, check_low_concern.py   # Parse tool output -> hits
  tools/               # Thin wrappers around external binaries (hmmer, blastn, blastx,
                       #   diamond, cmscan) + search_handler.py base class
  utils/               # Logging, FASTA/file helpers, coordinate math, HTML rendering
  tests/               # Pytest suite (see Testing below)
```

## Key data model (read `commec/config/result.py` before touching outputs)

- `ScreenResult` is the root output object: `commec_info`, `query_info`, and
  `queries: dict[str, QueryResult]`.
- `QueryResult` holds a `QueryScreenStatus` (`status`) and `hits: dict[str, HitResult]`.
- `QueryScreenStatus` carries the overall `screen_status` plus per-step statuses:
  `biorisk`, `protein_taxonomy`, `nucleotide_taxonomy`, `low_concern`, and a `rationale`
  string.
- `ScreenStatus` is a `StrEnum` ordered by severity/importance (`NULL` < `SKIP` < `PASS`
  < `CLEARED_WARN` < `CLEARED_FLAG` < `WARN` < `FLAG` < `STOP` < `ERROR`). Its string
  *values* are human-facing (`"Flag"`, `"Flag (Cleared)"`, `"Pass"`, …) — keep this in
  mind when comparing against serialized JSON.
- The output JSON has its own format version (`JSON_COMMEC_FORMAT_VERSION` in
  `result.py`); always round-trip through `json_io` rather than hand-writing JSON.

## Dev environment

Dependencies (including the external bioinformatics binaries) are managed by conda, not
pip alone:

```bash
conda env create -f environment.yaml   # creates the `commec-dev` env
conda activate commec-dev               # installs the package editable via `pip -e .`
```

The non-Python tools (`blast`, `diamond`, `hmmer`, `infernal`) must be on `PATH` for a
real screen to run; they come from the conda env.

## Testing

Tests live in `commec/tests/` and run with `pytest` (CI: `.github/workflows/automate_tests.yml`
runs `pytest -vv`).

There are **two distinct testing styles** — know which one you want:

1. **Mocked logic tests** (the majority, e.g. `test_screen.py`). These use
   `commec/tests/screen_factory.py::ScreenTesterFactory`, which fabricates the
   *intermediate* search-tool output files and runs `commec screen --resume` against the
   tiny placeholder databases in `commec/tests/test_dbs/`. External taxonomy/biorisk
   lookups are monkeypatched out. This exercises the parsing + decision logic **without
   needing real databases or binaries**. Use this to test pipeline logic.
   - Build a scenario with `add_query()` / `add_hit(...)`, then `.run()` returns a
     `ScreenResult` you can assert on.
   - Exemplar-comparison tests (e.g. `test_functional_screen`) regenerate their expected
     JSON with `pytest --gen-examples` (see the `--gen-examples` option in `conftest.py`).

2. **End-to-end detection tests** (`commec/tests/test_evaluation.py`). These run the *real*
   pipeline on real FASTA inputs against real databases and assert on detection outcomes.
   Test cases are data-driven from `commec/tests/test_data/eval/` — see
   `commec/tests/test_data/eval/README.md` for the per-case `metadata.yaml` schema. Because
   the real databases are large and not in the repo, these tests **skip** unless a database
   directory is provided via `--commec-db-dir <path>` or the `COMMEC_DB_DIR` env var:

   ```bash
   pytest commec/tests/test_evaluation.py --commec-db-dir /path/to/commec-dbs
   ```

Run the fast (mocked) suite with a plain `pytest`; it does not require databases.

## Conventions

- Python ≥ 3.10. Match the existing style: module docstrings, type hints, `dataclass`-based
  state, `logging` (not `print`) in library code.
- Prefer interacting with the `ScreenResult` dataclasses and `json_io` helpers over raw
  dicts/JSON, so the output format version stays consistent.
- `commec/tests/.pylintrc` configures linting for the test package.
- Don't commit real reference databases or large FASTA inputs; keep test fixtures small.
