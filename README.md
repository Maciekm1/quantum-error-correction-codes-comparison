<div align="center">

# A Comparative Study on Error Correction Algorithms for LEO-Based CubeSats

**LDPC vs. Cascade information reconciliation for continuous-variable QKD under CubeSat-style constraints**

[![University of York](https://img.shields.io/badge/University%20of%20York-Dissertation%202026-00599C?labelColor=555555)](https://www.york.ac.uk/)
[![C11](https://img.shields.io/badge/C-11-00599C?labelColor=555555&logo=c&logoColor=white)](https://en.wikipedia.org/wiki/C11_(C_standard_revision))
[![C++17](https://img.shields.io/badge/C%2B%2B-17-00599C?labelColor=555555&logo=c%2B%2B&logoColor=white)](https://isocpp.org/)
[![Python 3](https://img.shields.io/badge/python-3.10+-00599C?labelColor=555555&logo=python&logoColor=white)](https://www.python.org/)
[![CMake](https://img.shields.io/badge/CMake-3.10+-00599C?labelColor=555555&logo=cmake&logoColor=white)](https://cmake.org/)

*Author: **Maciek Zaweracz** · Supervisor: Dr Adrian Bors · BSc Computer Science*

</div>

---

## Abstract

This repository supports a simulation and systems study comparing **one-way quasi-cyclic LDPC** reconciliation (via the SPOQC-oriented [`cvqkd-reconciliation`](cvqkd-reconciliation/) library) with the **interactive Cascade** protocol (via [`cascade-cpp`](cascade-cpp/), after Bruno Rijsman’s reference implementation). Work is framed around **LEO CubeSat** limits on compute, memory, classical bandwidth, and pass time, in the context of **continuous-variable quantum key distribution (CV-QKD)** and the **Satellite Platform for Optical Quantum Communications (SPOQC)**.

**Part I** sweeps channel difficulty and records reconciliation efficiency, residual errors, classical overhead, timings, and interaction counts under **matched pre-correction bit error rate** between pipelines. **Part II** maps those measurements onto a first-order mission model (quantum window, RF vs. optical classical links, compute pace scenarios). Full methodology, results, and ethics statement are in the LaTeX dissertation (`Overleaf-Dissertation-Files/`).

---

## Table of contents

- [Repository layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Running LDPC experiments](#running-ldpc-experiments)
- [Running Cascade experiments](#running-cascade-experiments)
- [Analysis and figures](#analysis-and-figures)
- [Implementation contribution: LDPC statistics tracking](#implementation-contribution-ldpc-statistics-tracking)
- [Upstream and mission context](#upstream-and-mission-context)
- [Citation](#citation)

---

## Repository layout

| Path | Role |
|------|------|
| [`cvqkd-reconciliation/`](cvqkd-reconciliation/) | C library: CV-QKD-style channel, 8D reconciliation, Min–Sum LDPC; **`ldpc_experiment`** benchmark binary |
| [`cascade-cpp/`](cascade-cpp/) | C++17 Cascade reference; **`bin/run_experiments`** drives JSON-defined sweeps |
| [`experiments/scripts/run_sweep.py`](experiments/scripts/run_sweep.py) | YAML-driven orchestration for LDPC SNR × matrix sweeps |
| [`experiments/config/`](experiments/config/) | Example sweep configuration |
| [`experiments/scripts/part_1_results.ipynb`](experiments/scripts/part_1_results.ipynb) | Part I plots and tables |
| [`Overleaf-Dissertation-Files/`](Overleaf-Dissertation-Files/) | UoYCS LaTeX project and bibliography |

---

## Prerequisites

**LDPC (`cvqkd-reconciliation`)**

- CMake ≥ 3.10, a C11 toolchain (`clang` or `gcc`), and `make` or Ninja.

**Cascade (`cascade-cpp`)**

- `clang++` with **C++17**, **pthread**, **GoogleTest** (for `make test`), and **Boost** (`program_options`, `filesystem`).
- On Apple Silicon, the bundled `Makefile` expects Homebrew headers/libs under `/opt/homebrew` (see comments in [`cascade-cpp/Makefile`](cascade-cpp/Makefile)).

**Python (experiments + notebooks)**

- **[uv](https://docs.astral.sh/uv/)** package manager; dependencies are declared in [`pyproject.toml`](pyproject.toml) and locked in [`uv.lock`](uv.lock) (Python **≥ 3.12**, including PyYAML and notebook stack).

---

## Running LDPC experiments

### 1. Build `ldpc_experiment`

From the **repository root**:

```bash
cd cvqkd-reconciliation
cmake -S . -B build
cmake --build build
```

The executable is **`build/ldpc_experiment`**. It implements the unified CV-QKD-style path (Gaussian samples → AWGN at chosen SNR → 8D reconciliation → syndrome → Min–Sum decode) and appends **one NDJSON summary line** per invocation to `results.ndjson` in the **current working directory** (used by the sweep runner).

**Manual invocation** (arguments: SNR, seed, frames, path to `.coo` B-matrix, QKD dimension):

```bash
cd cvqkd-reconciliation/build
./ldpc_experiment 0.07 123 10000 ../data/B_matrices/1024x1023_z1.coo 8
```

### 2. Run a full SNR sweep with `run_sweep.py`

The runner reads a YAML file, loops over SNR values and B-matrices, runs the binary with `cwd` set to the output directory, then renames the merged file.

```bash
# From repository root - install locked deps into .venv
uv sync

uv run python experiments/scripts/run_sweep.py experiments/config/sweep_snr_ldpc.yaml
```

Edit [`experiments/config/sweep_snr_ldpc.yaml`](experiments/config/sweep_snr_ldpc.yaml) to set:

- `ldpc.binary` — path to `ldpc_experiment` (default: `cvqkd-reconciliation/build/ldpc_experiment`)
- `ldpc.b_matrices` — e.g. `256x255_z1.coo`, `512x511_z4.coo`, `1024x1023_z1.coo`
- `snr` geometric range or `snr_points` list
- `frames_per_point`, `seed`, `output.raw_dir`, `experiment_name`

Raw NDJSON lands under `experiments/data/raw/` (or your configured `raw_dir`).

---

## Running Cascade experiments

Cascade sweeps are defined by a **JSON experiment specification** consumed by **`bin/run_experiments`** (multi-threaded driver). See [`cascade-cpp/README.md`](cascade-cpp/README.md) for the full schema.

### 1. Build the driver

```bash
cd cascade-cpp
make bin/run_experiments
```

### 2. Run the sweep

This repository includes a narrowed spec (original 4-pass algorithm, 10 000-bit keys, wide BSC error-rate grid, 10 000 runs per point) in:

**`cascade-cpp/study/experiments_papers_ec_compare.json`**

```bash
cd cascade-cpp
mkdir -p study/data/dissertation

./bin/run_experiments study/experiments_papers_ec_compare.json --output-dir study/data/dissertation
```

Optional flags (see `run_experiments --help`): `--seed N`, `--max-runs K`, `--disable-multi-processing`.

Outputs are **JSON data files** (one per algorithm / key-size / sweep type), suitable for plotting or for alignment with LDPC NDJSON via shared metrics (efficiency, BER, parity traffic, timings).

Equivalent upstream target (full *papers* suite, different JSON path):

```bash
make data-papers   # uses study/experiments_papers.json → study/data/papers
```

---

## Analysis and figures

- **Part I:** [`experiments/scripts/part_1_results.ipynb`](experiments/scripts/part_1_results.ipynb) — efficiency, residual BER/FER, overhead, timings, Cascade message counts.

Run `uv sync` once, then select the project **`.venv`** as the notebook kernel (or prefix commands with **`uv run`**). Regenerate graphs after updating raw data paths inside the notebooks.

---

## Implementation contribution: LDPC statistics tracking

A main **software contribution** of this work is a **statistics-tracking layer** in the internal SPOQC **`cvqkd-reconciliation`** codebase (C), integrated with the **`ldpc_experiment`** entry point in [`cvqkd-reconciliation/src/examples/ldpc_experiment.c`](cvqkd-reconciliation/src/examples/ldpc_experiment.c):

1. **Structured output** — Each completed (matrix, SNR) aggregate is serialized as **newline-delimited JSON (NDJSON)** so downstream tools can stream-parse results like Cascade’s experiment outputs.
2. **Schema alignment** — Field names and semantics (efficiency, reconciliation bits, per-key-bit overhead, timings, iteration counts, pre/post BER, FER, etc.) were chosen to **mirror `cascade-cpp`’s experiment records** so **one Python analysis pipeline** can treat both algorithms uniformly.
3. **Online aggregation** — Per-frame metrics feed **Welford’s algorithm** in [`cvqkd-reconciliation/src/qkd_stats.c`](cvqkd-reconciliation/src/qkd_stats.c) (via `QKDAggregateStats` / `qkd_stats_add_frame`) for **numerically stable running means and sample standard deviations** over thousands of frames **without storing every trial**.

Efficiency is computed compatibly with the Shannon reference for a BSC using the measured pre-correction BER per aggregate, matching the dissertation’s Part I definitions.

---

## Upstream and mission context

| Component | Origin / notes |
|-----------|----------------|
| **Cascade-cpp** | [brunorijsman/cascade-cpp](https://github.com/brunorijsman/cascade-cpp) (vendored/forked here with local `Makefile` tweaks). |
| **cvqkd-reconciliation** | Quantum Communications Hub / SPOQC-oriented CV-QKD reconciliation library; Hub-supervised use. Statistics NDJSON extension is intended to ship with the mission codebase. |
| **SPOQC / HOGS** | 12U CubeSat and ground segment context for CV-QKD from space (see dissertation references). |

---

## Acknowledgements

Supervision: **Dr Adrian Bors** (University of York). Quantum communications context: **Dr Rupesh Kumar**. Systems and implementation guidance: **Killian Murphy**. SPOQC / LDPC matrix design: SPOQC team (acknowledged in the dissertation). Cascade-cpp: **Bruno Rijsman** and contributors.

---

<div align="center">

<sub>Repository layout and commands reflect the state of this workspace; adjust paths if you relocate build directories.</sub>

</div>
