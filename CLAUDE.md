# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`technology-data` compiles energy-system technology assumptions (costs, efficiencies, lifetimes, fuel/material/electricity inputs, emissions) from many heterogeneous sources into a single standardized set of CSV files, one per year in `config.yaml:years` (2020–2050). The outputs are consumed downstream by [PyPSA-Eur](https://github.com/PyPSA/pypsa-eur) and [PyPSA-Earth](https://github.com/pypsa-meets-earth/pypsa-earth). This is a **data-compilation pipeline, not a library** — there is no installable package; the deliverable is the committed `outputs/*.csv`.

## Commands

The environment is a conda/mamba env defined in `environment.yaml` (referenced as `technology-data`). Run everything inside it.

```bash
# Regenerate the European cost CSVs (outputs/costs_<year>.csv)
snakemake --cores all -f compile_cost_assumptions --configfile config.yaml

# Regenerate the US cost CSVs (outputs/US/costs_<year>.csv) — depends on the EU outputs above
snakemake --cores all -f compile_cost_assumptions_usa --configfile config.yaml

# Both of the above, the way CI runs them:
make test

# Unit tests
make unit-test                                   # == pytest test
pytest test/test_compile_cost_assumptions.py     # one file
pytest test/test_compile_cost_assumptions.py::test_add_carbon_capture   # one test

# Lint/format (also enforced by pre-commit.ci on every PR)
ruff check . && ruff format .
```

`make purge` deletes all generated outputs (interactive confirm); `snakemake all` regenerates everything.

## Critical workflow rule: outputs are committed and CI diff-checks them

The generated `outputs/*.csv` are **checked into git**. CI (`.github/workflows/ci.yaml`) regenerates them and **fails if the committed files differ from a fresh run**. Therefore, after any change to input data or compile logic you must rerun both snakemake rules and commit the updated CSVs. Never hand-edit `outputs/*.csv` — including when resolving merge conflicts in them; instead resolve the inputs/code, regenerate, and stage the result.

Because `compile_cost_assumptions_usa` takes the EU `outputs/costs_{year}.csv` as **input**, always regenerate the EU rule before the US rule.

## Pipeline architecture

Two snakemake rules in `Snakefile` drive everything:

- **`compile_cost_assumptions`** (`scripts/compile_cost_assumptions.py`) — the core. Reads ~15 source files listed as `input:` in the Snakefile (Danish Energy Agency `.xlsx` catalogues, Fraunhofer ISE, EWG, PyPSA legacy costs, PNNL storage, a Eurostat inflation spreadsheet, and `inputs/manual_input.csv`). It harmonizes technology names, units, and currency years; applies inflation adjustment to a common `eur_year` (`config.yaml`); and writes `outputs/costs_{year}.csv`.
- **`compile_cost_assumptions_usa`** (`scripts/compile_cost_assumptions_usa.py`) — overlays US-specific data from NREL/ATB parquet files plus `inputs/US/*.csv`, producing `outputs/US/costs_{year}.csv`.

`config.yaml` holds the knobs: output `years`, target `eur_year`, NREL/ATB filters, optimist/pessimist uncertainty (`expectation`), and per-source toggles (e.g. `offwind_no_gridcosts`, `pnnl_energy_storage`). Per-source loading/cleaning is implemented as functions in `compile_cost_assumptions.py` (e.g. `add_carbon_capture`, `get_data_from_dea`, `get_sheet_location`), which the unit tests target directly.

The `convert_pdf_*` scripts and the `convert_EWG` / `retrieve_data_from_dea` rules are one-off source-ingestion helpers (some commented out); they are not part of the normal output-regeneration loop.

## Adding or editing a technology

Most non-DEA additions go through **`inputs/manual_input.csv`**, schema:
`technology,parameter,year,value,unit,currency_year,source,further_description`
(US-only rows live in `inputs/US/manual_input_usa.csv`, which adds `financial_case,scenario`).
DEA-sourced technologies are instead pulled from the `.xlsx` catalogues by name/sheet inside the compile functions. The final `outputs/*.csv` schema is the narrower `technology,parameter,value,unit,source,further description,currency_year`. Conventions to follow: parameter names are lower-case hyphenated (`electricity-input`, `co2-input`, `heat-output`); always fill `source` and `further_description` (reviewers require traceable derivations — page/table references and the arithmetic behind any computed value).

Add a bullet for user-facing changes under "Upcoming Release" in `docs/release_notes.rst`.

## Tests

`test/` uses pytest (`conftest.py`, fixtures in `test/test_data`). Note: a few tests in `test_compile_cost_assumptions.py` (e.g. `test_get_sheet_location`, `test_get_data_from_dea`, `test_add_carbon_capture`) depend on DEA source spreadsheets and **fail locally if that data isn't present**, while passing in CI where it is fetched. Verify whether a failure reproduces on a clean `master` before assuming your change caused it.

## Repo / PR workflow

`origin` is a personal fork; `upstream` is `PyPSA/technology-data` and is where PRs target (`base: master`). pre-commit.ci auto-formats PRs and pushes fixup commits, so `git pull` your PR branch after pushing. Keep PRs single-topic.
