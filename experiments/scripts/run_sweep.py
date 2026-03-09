#!/usr/bin/env python3
"""Run LDPC SNR sweep experiments from a YAML config.

Usage:  python experiments/scripts/run_sweep.py experiments/config/sweep_snr_ldpc.yaml

All paths in the config are relative to the working directory (project root).

The binary appends one NDJSON line per (matrix, snr) combo to results.ndjson
in the output directory. 

Each line contains key_size and snr, so runs
with different B-matrices are distinguishable by key_size.
"""

import argparse
import subprocess
import sys
import yaml
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="LDPC SNR sweep runner")
    parser.add_argument("config", help="YAML config file")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())

    binary = Path(cfg["ldpc"]["binary"]).resolve()
    b_dir = Path(cfg["ldpc"]["b_matrices_dir"]).resolve()
    out_dir = Path(cfg["output"]["raw_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    seed = cfg.get("seed", 123)
    frames = cfg["frames_per_point"]
    dim = cfg["ldpc"].get("qkd_dimension", 8)

    # Resolve SNR values from list or geometric range (start, end, step_factor)
    if "snr_points" in cfg:
        snr_list = cfg["snr_points"]
    else:
        r = cfg["snr"]
        snr_list = []
        v = r["start"]
        while v <= r["end"]:
            snr_list.append(v)
            v *= r["step_factor"]

    # Binary writes to results.ndjson in cwd
    # rename to {experiment_name}.ndjson at end
    results = out_dir / f"{cfg['experiment_name']}.ndjson"
    interim = out_dir / "results.ndjson"
    interim.write_text("")

    combos = [
        (m, snr)
        for m in cfg["ldpc"]["b_matrices"]
        for snr in snr_list
    ]

    for i, (matrix, snr) in enumerate(combos, 1):
        matrix_path = b_dir / matrix
        if not matrix_path.exists():
            print(f"SKIP: {matrix_path} not found", file=sys.stderr)
            continue

        print(f"[{i}/{len(combos)}] {matrix}  SNR={snr}")

        proc = subprocess.run(
            [str(binary), str(snr), str(seed), str(frames),
             str(matrix_path), str(dim)],
            capture_output=True, text=True,
            cwd=str(out_dir),
        )

        if proc.returncode != 0:
            print(f"  FAILED (exit {proc.returncode}): {proc.stderr}",
                  file=sys.stderr)
            continue

        for line in proc.stderr.strip().splitlines():
            print(f"  {line}")

    interim.rename(results)
    print(f"\nDone. Results written to {results}")


if __name__ == "__main__":
    main()
