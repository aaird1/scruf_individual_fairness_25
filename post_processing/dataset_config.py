"""Dataset configuration for post-processing.

Each dataset (movies, music, ...) is described by a small TOML file in
`post_processing/datasets/`. Adding a new dataset means adding a new TOML
file here -- no code changes required.

Example (`datasets/movies.toml`):

    [dataset]
    name = "movies"
    data_dir = "data/movies"
    recs_filename = "recs_1m.csv"
    ratings_filename = "ratings_1m.csv"
    items_filename = "movie_features_1m.csv"
    num_items = 2753
    coverage_target = 0.85
    metrics = ["ndcg", "rbo", "nlip", "coverage", "proportional_fairness"]

    [[dataset.features]]
    name = "non-en"
    proportion_target = 0.07

`recs_filename` / `ratings_filename` / `items_filename` are Python format
strings, not just literal filenames. They're resolved per history file
using fields parsed out of that history file's name, so the recs/ratings
file used can vary by fold, model, etc. `history_filename_fields` says how
to split the history filename's `_`-separated stem into named fields, in
order. For history files named "<data>_<fold>_<model>_...":

    history_filename_fields = ["data", "fold", "model"]
    recs_filename = "{data}_{fold}_{model}_test_recommendations.csv"
    ratings_filename = "{data}_{fold}_test.csv"

A history file "kiva_fold1_BPR_static.parquet" then reads recs from
"kiva_fold1_BPR_test_recommendations.csv" and ratings from
"kiva_fold1_test.csv" in `data_dir`. A template with no placeholders (like
movies' `recs_filename` above) is just used as-is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import toml

THIS_DIR = Path(__file__).resolve().parent
DATASETS_DIR = THIS_DIR / "datasets"


@dataclass(frozen=True)
class FeatureTarget:
    """A protected item feature and the proportion of recommendations it should get."""

    name: str
    proportion_target: float


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    data_dir: Path
    recs_filename: str
    ratings_filename: str
    items_filename: str
    num_items: int
    coverage_target: float
    features: list[FeatureTarget] = field(default_factory=list)
    metrics: list[str] = field(default_factory=lambda: ["ndcg", "rbo", "nlip", "coverage", "proportional_fairness"])
    list_low: int = 10
    list_high: int = 50
    score_sort: bool = True
    # Order of "_"-separated fields in a history filename's stem, used both
    # to fill in {placeholders} in recs_filename/ratings_filename/items_filename
    # and to tag each row of the run_experiment.py summary CSV.
    history_filename_fields: list[str] = field(
        default_factory=lambda: ["data", "agents", "choice", "allocation", "weight"]
    )
    # Set True if recs_filename/ratings_filename/items_filename have a header
    # row. The header's own column names are ignored -- only the first 2-3
    # columns' positions matter (user id, item id, [score/rating]).
    recs_has_header: bool = False
    ratings_has_header: bool = False
    items_has_header: bool = False

    def parse_history_fields(self, history_path) -> dict:
        """Split a history file's name into named fields per
        `history_filename_fields`. Extra trailing "_"-parts (beyond the
        named fields) are joined back together under "extra"."""
        stem = Path(history_path).stem
        parts = stem.split("_")
        fields = dict(zip(self.history_filename_fields, parts))
        if len(parts) > len(self.history_filename_fields):
            fields["extra"] = "_".join(parts[len(self.history_filename_fields):])
        return fields

    def _resolve(self, template: str, fields: dict, template_name: str) -> Path:
        try:
            filename = template.format(**fields)
        except KeyError as missing:
            raise ValueError(
                f"Dataset '{self.name}': {template_name} template '{template}' needs a field "
                f"{missing} that wasn't found in the history filename. Parsed fields: {fields}. "
                f"Check the dataset's `history_filename_fields` setting."
            ) from None
        return self.data_dir / filename

    def recs_path(self, fields: dict) -> Path:
        return self._resolve(self.recs_filename, fields, "recs_filename")

    def ratings_path(self, fields: dict) -> Path:
        return self._resolve(self.ratings_filename, fields, "ratings_filename")

    def items_path(self, fields: dict) -> Path:
        return self._resolve(self.items_filename, fields, "items_filename")


def _dataset_toml_path(name_or_path: str) -> Path:
    candidate = Path(name_or_path)
    if candidate.suffix == ".toml" and candidate.exists():
        return candidate
    named = DATASETS_DIR / f"{name_or_path}.toml"
    if named.exists():
        return named
    available = sorted(p.stem for p in DATASETS_DIR.glob("*.toml"))
    raise FileNotFoundError(
        f"No dataset config found for '{name_or_path}'. "
        f"Available datasets: {', '.join(available) or '(none defined yet)'}"
    )


def load_dataset_config(name_or_path: str) -> DatasetConfig:
    """Load a dataset config by name (looked up in post_processing/datasets/)
    or by an explicit path to a TOML file."""
    toml_path = _dataset_toml_path(name_or_path)
    raw = toml.load(toml_path)["dataset"]

    # Paths in the TOML are relative to the dataset config's own directory
    # (normally post_processing/), so relative data_dir entries keep working
    # no matter where the caller's cwd is.
    base_dir = toml_path.resolve().parent.parent if toml_path.parent == DATASETS_DIR else toml_path.resolve().parent
    data_dir = Path(raw["data_dir"])
    if not data_dir.is_absolute():
        data_dir = base_dir / data_dir

    features = [
        FeatureTarget(name=f["name"], proportion_target=f["proportion_target"])
        for f in raw.get("features", [])
    ]

    kwargs = dict(
        name=raw.get("name", toml_path.stem),
        data_dir=data_dir,
        recs_filename=raw["recs_filename"],
        ratings_filename=raw["ratings_filename"],
        items_filename=raw["items_filename"],
        num_items=raw["num_items"],
        coverage_target=raw["coverage_target"],
        features=features,
    )
    if "metrics" in raw:
        kwargs["metrics"] = list(raw["metrics"])
    if "list_low" in raw:
        kwargs["list_low"] = raw["list_low"]
    if "list_high" in raw:
        kwargs["list_high"] = raw["list_high"]
    if "score_sort" in raw:
        kwargs["score_sort"] = raw["score_sort"]
    if "history_filename_fields" in raw:
        kwargs["history_filename_fields"] = list(raw["history_filename_fields"])
    if "recs_has_header" in raw:
        kwargs["recs_has_header"] = raw["recs_has_header"]
    if "ratings_has_header" in raw:
        kwargs["ratings_has_header"] = raw["ratings_has_header"]
    if "items_has_header" in raw:
        kwargs["items_has_header"] = raw["items_has_header"]

    return DatasetConfig(**kwargs)


def available_datasets() -> list[str]:
    return sorted(p.stem for p in DATASETS_DIR.glob("*.toml"))
