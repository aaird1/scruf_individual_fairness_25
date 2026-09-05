# Post-processing

Computes metrics (nDCG, RBO, coverage, proportional fairness, ...) over
SCRUF-D rerank history files. Everything here is driven by two things you
can configure without touching code: a **dataset** (where the data files
live, what protected features exist) and a **list of metrics** (which of the
registered metrics to actually compute).

## Quick start

Process every history file for a dataset and get one summary CSV:

```bash
python run_experiment.py -d movies --history-dir data/movies --output movie_results.csv
python run_experiment.py -d music --history-dir data/music --output music_results.csv
```

This writes a `.json` of metrics next to each history file (same as before)
*and* rolls all of them up into `movie_results.csv` / `music_results.csv`,
with one column per metric -- no separate "create_csv" step needed, and no
hardcoded column list to keep in sync when a metric is added or removed.

Only want to (re-)build the summary CSV from JSON files that already exist?

```bash
python run_experiment.py -d movies --json-dir data/movies --output movie_results.csv
```

Process a single history file:

```bash
python post_processor.py data/movies/some_history.parquet -d movies -c
```

## Choosing metrics

Every dataset config lists its default metrics:

```toml
metrics = ["ndcg", "rbo", "nlip", "coverage", "proportional_fairness"]
```

Override the defaults from the command line with `-m`/`--metrics` on either
script, e.g. to compute only nDCG and coverage:

```bash
python run_experiment.py -d movies --history-dir data/movies -m ndcg,coverage --output movie_results.csv
```

Run `python post_processor.py --help` to see every metric currently
registered (`ndcg`, `rbo`, `nlip`, `coverage`, `proportional_fairness`,
`gini`).

### Adding a new metric

Add a function to `metrics/definitions.py` that takes a `RunContext` (has
`.dataset`, `.users` -- per-user recs/ratings/original-ranking -- and
`.all_recommender_ids` for corpus-level metrics) and returns a dict of
output fields, then decorate it:

```python
@metric("my_metric")
def my_metric(ctx: RunContext) -> dict:
    ...
    return {"my_metric": value}
```

It's immediately usable via `-m my_metric` or by adding it to a dataset's
`metrics` list -- no other code needs to change.

## Adding a new dataset

Add a TOML file to `datasets/`, e.g. `datasets/my_dataset.toml`:

```toml
[dataset]
name = "my_dataset"
data_dir = "data/my_dataset"       # relative to post_processing/
recs_filename = "recs.csv"
ratings_filename = "ratings.csv"
items_filename = "items.csv"
num_items = 10000
coverage_target = 0.8
metrics = ["ndcg", "rbo", "nlip", "coverage", "proportional_fairness"]

[[dataset.features]]
name = "some_protected_feature"
proportion_target = 0.2
```

Then run `python run_experiment.py -d my_dataset ...` -- no Python changes
required. `python -c "from dataset_config import available_datasets; print(available_datasets())"`
lists every dataset currently defined.

### recs/ratings/items that vary per history file (fold, model, ...)

`recs_filename`, `ratings_filename`, and `items_filename` are format
strings, not just literal filenames -- they're resolved separately for
*each* history file, using fields parsed out of that history file's own
name. `history_filename_fields` says how to split the history filename's
`_`-separated stem into named fields, in order.

For history files named `<data>_<fold>_<model>_...` (see
`datasets/kiva.toml`):

```toml
history_filename_fields = ["data", "fold", "model"]
recs_filename = "{data}_{fold}_{model}_test_recommendations.csv"
ratings_filename = "{data}_{fold}_test.csv"
```

`kiva_fold1_BPR_static.parquet` then reads recs from
`kiva_fold1_BPR_test_recommendations.csv` and ratings from
`kiva_fold1_test.csv`; `kiva_fold2_ItemKNN_static.parquet` reads its own
fold2/ItemKNN files -- each history file automatically gets the right
recs/ratings for its fold and model. A template with no `{placeholders}`
(like movies'/music's `recs_filename`) is just used as-is, so this is opt-in
per dataset. Any filename part beyond `history_filename_fields` (e.g.
`static` above) is kept as an `extra` column in the summary CSV instead of
being dropped.

If a dataset's recs/ratings/items CSVs have a header row (unlike the
legacy headerless movies/music files), set `recs_has_header` /
`ratings_has_header` / `items_has_header = true` -- the header's column
*names* are ignored, only column order matters (user id, item id, then
score/rating/feature value).

## Layout

- `dataset_config.py` -- loads a dataset's TOML config into a `DatasetConfig`.
- `datasets/*.toml` -- one file per dataset (paths, protected features, default metrics).
- `metrics/context.py` -- loads a history file + a dataset's data files into a `RunContext` shared by every metric.
- `metrics/definitions.py` -- the metric implementations (`ndcg`, `rbo`, `nlip`, `coverage`, `proportional_fairness`, `gini`).
- `metrics/registry.py` -- the `@metric("name")` registry that makes metrics selectable by name.
- `post_processor.py` -- CLI to run all (or selected) metrics on one history file.
- `run_experiment.py` -- CLI to run post-processing over a directory of history files and aggregate the results into one CSV.
- `metrics_wrapper.py` / `metrics.c` / `metrics.so` -- C-accelerated nDCG/Gini implementations, unchanged.
