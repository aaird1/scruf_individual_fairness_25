"""Compute post-processing metrics for a single rerank-history file.

This replaces the old post_processor_movie.py / post_processor_music.py
scripts. Both were the same logic with dataset-specific constants
hardcoded at the top -- adding a dataset meant copy-pasting the whole file.
Now the dataset and the metrics to compute are both just arguments:

    python post_processor.py history.parquet -d movies -c
    python post_processor.py history.parquet -d music -c -m ndcg,coverage

Add a dataset by adding a TOML file to post_processing/datasets/ (see
dataset_config.py). Add a metric by registering a function in
post_processing/metrics/definitions.py -- it becomes selectable via -m
immediately.
"""

from __future__ import annotations

import argparse
import json
import os

from dataset_config import load_dataset_config
from metrics import available_metrics, build_context, get_metric


def get_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("history_csv", type=str, help="Path to the history CSV/Parquet file.")
    parser.add_argument(
        "-d", "--dataset", required=True,
        help="Dataset name (matches post_processing/datasets/<name>.toml) or a path to a dataset TOML file.",
    )
    parser.add_argument("-c", "--compressed", action="store_true", help="Read history_csv as Parquet.")
    parser.add_argument(
        "-m", "--metrics", type=str, default=None,
        help=f"Comma-separated metrics to compute (default: the dataset's configured metrics). "
             f"Available: {', '.join(available_metrics())}",
    )
    parser.add_argument("-o", "--output", type=str, default=None, help="Where to write the results JSON (default: alongside history_csv).")
    parser.add_argument("-q", "--quiet", action="store_true", help="Don't print results to stdout.")
    return parser.parse_args()


def run_post_processing(history_csv: str, dataset: str, compressed: bool = False, metric_names: list[str] | None = None) -> dict:
    """Load `history_csv` for `dataset` and compute the requested metrics.
    Returns a flat dict ready to serialize to JSON."""
    dataset_config = load_dataset_config(dataset)
    ctx = build_context(dataset_config, history_csv, compressed)

    names = metric_names or dataset_config.metrics
    results: dict = {}
    for name in names:
        results.update(get_metric(name)(ctx))
    return results


def main():
    args = get_args()
    metric_names = [m.strip() for m in args.metrics.split(",")] if args.metrics else None

    results = run_post_processing(args.history_csv, args.dataset, args.compressed, metric_names)

    output_path = args.output or (os.path.splitext(args.history_csv)[0] + ".json")
    with open(output_path, "w") as json_file:
        json.dump(results, json_file, indent=4)

    if not args.quiet:
        for key, value in results.items():
            if not key.endswith("_scores"):  # raw per-user lists are noisy; means/summaries only
                print(f"{key}: {value}")
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
