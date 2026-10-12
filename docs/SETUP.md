# Running SCRUF-D Experiments

Setup and usage guide for running these experiments.

## Requirements

Python 3.10 or newer. Earlier versions will not work.

| Platform | Command |
|---|---|
| macOS (Homebrew) | `brew install python@3.11` |
| Ubuntu / Debian | `sudo apt install python3.11 python3.11-venv` |
| Any platform | Installer from https://www.python.org/downloads/ |
| conda | `conda create -n scruf python=3.11` |

## 1. Create a virtual environment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate          # macOS, Linux
.venv\Scripts\activate             # Windows
python -m pip install --upgrade pip setuptools wheel
```

With conda, activate your conda environment instead. The remaining steps are the same.

## 2. Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

`requirements.txt` pins exact versions, so you get the same packages the results were
produced with. `pip install -e .` makes `import scruf` work from any directory.

## 3. Run an experiment

Each experiment lives in a folder under `configurations/`. Run from inside that folder,
because the script reads `params.yaml` from the current directory.

```bash
cd configurations/movie_experiments/group
python ../../../scruf_d/__main__MODIFY.py
```

`params.yaml` controls what runs:

- `choice`: `weighted_scoring`, `RuleBorda`, `RuleCopeland`
- `allocation`: `least_fair`, `product_lottery`, `weighted_product_allocation`
- `rec_weight`: one or more recommender weights
- `fold`: which data fold

Every combination runs, so three choices and three allocations means nine runs.

For a quick test, set `iterations = 200` in the experiment's `.toml`. The default `-1`
runs every user and takes much longer.

## 4. Compute metrics

Each run writes to a timestamped folder under `results/`. Point post-processing at it:

```bash
cd post_processing
python run_experiment.py -d movies --history-dir ../results/RUN_FOLDER -o ../results/RUN_FOLDER/summary.csv
```

Replace `RUN_FOLDER` with the folder name, such as `2026-10-10_161238`. Use `-d movies`,
`-d music`, or `-d kiva` to match your dataset.

## 5. What a run folder contains

```
results/2026-10-10_161238/
  run_info.yaml     code version, package versions, start/finish time, status
  *.toml            the exact configuration used
  path_list.csv     which config produced which output file
  *.parquet         raw run output
  *.json            computed metrics
  summary.csv       metrics as a table
```

Nothing is ever overwritten. Each run gets a new folder.

`run_info.yaml` has a `status` field: `running` while in progress, `completed` when
finished. A folder still saying `running` after the process exited means it crashed.

```bash
grep -l 'status: running' results/*/run_info.yaml
```

## 6. Keeping a run

`results/` is not tracked by git, so experimental runs stay on your machine. To keep one
that belongs in the written record:

```bash
git add -f results/2026-10-10_161238
git commit -m "Results for movie group experiment"
```

The `-f` is needed because `results/` is in `.gitignore`.

## Notes

The repository contains a C implementation of nDCG and Gini
(`post_processing/metrics.c`) but it is not used and should not be built. It reads past
the end of an array for users whose recommendation list is shorter than 10 items, which
changes nDCG for a large fraction of users. All results come from the pure-Python
implementation in `metrics_wrapper.py`. The committed `metrics.so` is an x86_64 binary
and does not load on Apple Silicon, which is why the Python path is used by default.

`post_processing/data/` holds input files and also older result files from earlier work.
It is not a clean inputs-only directory.

The `*_recommendations.csv` input files are outputs of recommender models (BPR, DMF,
MultiVAE), not raw datasets. No model-training code is included in this repository, so
these files cannot be regenerated here — they can only be used as committed. This means
anyone reproducing this work uses the same recommendation lists that produced the
original results, but cannot verify how those lists were generated or produce new ones
for a different dataset or model.
