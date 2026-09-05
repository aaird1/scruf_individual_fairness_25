"""Run post-processing over every history file for a dataset and collect the
resulting metrics into a single summary CSV.

This replaces run_movie_experiment.py, run_music_experiment.py,
create_csv_movie.py and create_csv_music.py, which were four near-identical
copies of "glob a directory, shell out to a post-processor script, then
hand-parse the resulting JSONs into a CSV with a hardcoded set of columns".

Typical use -- process every *.parquet history file for a dataset and get
one CSV with all the metrics:

    python run_experiment.py -d movies --history-dir data/movies --output movie_results.csv

Just re-summarize JSON results that were already computed (e.g. by
post_processor.py directly):

    python run_experiment.py -d movies --json-dir data/movies --output movie_results.csv

The metric columns in the output CSV are derived automatically from
whatever metrics were actually computed -- add a metric and it just shows
up as a new column, no aggregation script to update.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from dataset_config import load_dataset_config
from post_processor import run_post_processing


def get_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--dataset", required=True, help="Dataset name, matching post_processing/datasets/<name>.toml.")
    parser.add_argument("--history-dir", type=str, default=None, help="Directory of raw history files to post-process first.")
    parser.add_argument("--pattern", type=str, default="*.parquet", help="Glob pattern for history files within --history-dir (default: *.parquet).")
    parser.add_argument("--compressed", action="store_true", default=None, help="Force reading history files as Parquet (default: inferred from --pattern).")
    parser.add_argument("-m", "--metrics", type=str, default=None, help="Comma-separated metrics to compute (default: the dataset's configured metrics).")
    parser.add_argument("--json-dir", type=str, default=None, help="Directory of *.json results to summarize (default: --history-dir).")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output summary CSV path.")
    return parser.parse_args()


def flatten_metrics(data: dict) -> dict:
    """Flatten metric results into CSV-friendly columns. Nested dicts (e.g.
    proportional_fairness per feature) become one column per key; raw
    per-user score lists are dropped from the summary (they live in the
    per-file JSON) since a CSV cell isn't a great place for a list."""
    flat = {}
    for key, value in data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flat[f"{key}_{sub_key}"] = sub_value
        elif isinstance(value, list):
            continue
        else:
            flat[key] = value
    return flat


def run_history_files(dataset: str, history_dir: str, pattern: str, compressed: bool | None, metric_names: list[str] | None) -> None:
    if compressed is None:
        compressed = pattern.endswith(".parquet")

    files = sorted(Path(history_dir).glob(pattern))
    print(f"Found {len(files)} history file(s) in {history_dir} matching '{pattern}'")
    for file_path in files:
        print(f"Processing {file_path.name}...")
        results = run_post_processing(str(file_path), dataset, compressed=compressed, metric_names=metric_names)
        output_path = file_path.with_suffix(".json")
        with open(output_path, "w") as json_file:
            json.dump(results, json_file, indent=4)


def summarize(dataset: str, json_dir: str, output_csv: str) -> None:
    dataset_config = load_dataset_config(dataset)
    rows = []
    fieldnames = list(dataset_config.history_filename_fields)

    for json_path in sorted(Path(json_dir).glob("*.json")):
        with open(json_path) as json_file:
            data = json.load(json_file)

        row = dataset_config.parse_history_fields(json_path)
        row.update(flatten_metrics(data))
        rows.append(row)

        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    if not rows:
        print(f"No JSON result files found in {json_dir}; nothing to summarize.")
        return

    with open(output_csv, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} row(s) to {output_csv}")


def main():
    args = get_args()
    metric_names = [m.strip() for m in args.metrics.split(",")] if args.metrics else None

    if args.history_dir:
        run_history_files(args.dataset, args.history_dir, args.pattern, args.compressed, metric_names)

    json_dir = args.json_dir or args.history_dir
    if not json_dir:
        raise SystemExit("Provide --history-dir and/or --json-dir so there's something to summarize.")

    summarize(args.dataset, json_dir, args.output)


if __name__ == "__main__":
    main()
