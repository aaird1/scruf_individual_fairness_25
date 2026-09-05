"""Builds the shared `RunContext` that every metric function reads from.

Loading the history/recs/ratings/items files and slicing them per-user used
to be copy-pasted (with dataset-specific constants baked in) at the top of
every post_processor_*.py script. It now happens once, here, driven by a
`DatasetConfig`, so metric functions stay small and dataset-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from dataset_config import DatasetConfig

HISTORY_COLUMNS = ["time", "user", "agent_item", "id", "score", "rank", "type"]
OUTPUT_TYPE = " output"


@dataclass
class UserResult:
    user: str
    recommender_ids: list[int]
    obs_ids: list[int]
    obs_scores: list[float]
    original_ids: list[int]  # this user's full original (pre-rerank) recommendation list


@dataclass
class RunContext:
    dataset: DatasetConfig
    history: pd.DataFrame
    recs_file: pd.DataFrame
    ratings_file: pd.DataFrame
    items_file: pd.DataFrame
    users: list[UserResult] = field(default_factory=list)

    @property
    def all_recommender_ids(self) -> list[int]:
        """Every recommended item id, across all users, flattened. Used by
        corpus-level metrics like coverage and proportional fairness."""
        ids: list[int] = []
        for u in self.users:
            ids.extend(u.recommender_ids)
        return ids


def _load_history(history_path: str, compressed: bool) -> pd.DataFrame:
    if compressed:
        history = pd.read_parquet(history_path)
    else:
        history = pd.read_csv(history_path, header=None)
    history.columns = HISTORY_COLUMNS
    return history


def _read_positional_csv(path, columns: list[str], dtypes: dict, has_header: bool) -> pd.DataFrame:
    """Read a CSV keyed by column *position*, not name -- source files come
    from different pipelines and don't agree on header names (or whether
    they have a header at all), but they agree on column order."""
    if has_header:
        df = pd.read_csv(path, header=0)
        df = df.iloc[:, : len(columns)]
        df.columns = columns
    else:
        df = pd.read_csv(path, names=columns, header=None)
    return df.astype(dtypes)


def build_context(dataset: DatasetConfig, history_path: str, compressed: bool) -> RunContext:
    history = _load_history(history_path, compressed)

    # Which recs/ratings/items file to read can depend on the history file
    # itself (e.g. a fold and model parsed out of its name), so this is
    # resolved per call rather than once when the dataset config is loaded.
    fields = dataset.parse_history_fields(history_path)

    recs_file = _read_positional_csv(
        dataset.recs_path(fields),
        ["user_id", "item_id", "score"],
        {"user_id": int, "item_id": int, "score": float},
        dataset.recs_has_header,
    )
    ratings_file = _read_positional_csv(
        dataset.ratings_path(fields),
        ["user_id", "item_id", "rating"],
        {"user_id": int, "item_id": int, "rating": float},
        dataset.ratings_has_header,
    )
    items_file = _read_positional_csv(
        dataset.items_path(fields),
        ["Item", "Feature", "BV"],
        {"Item": int, "Feature": str, "BV": float},
        dataset.items_has_header,
    )
    feature_names = [f.name for f in dataset.features]
    items_file = items_file[items_file["Feature"].isin(feature_names)]

    users: list[UserResult] = []
    for user in history["user"].unique():
        history_view = history[history["user"] == user]
        out_view = history_view[history_view["type"] == OUTPUT_TYPE]

        recommender_ids = [int(i) for i in out_view["id"].tolist()]

        user_ratings = ratings_file[ratings_file["user_id"] == int(user)]
        obs_ids = user_ratings["item_id"].tolist()
        obs_scores = user_ratings["rating"].tolist()

        user_original = recs_file[recs_file["user_id"] == int(user)]
        original_ids = user_original.iloc[:, 1].to_list()

        users.append(
            UserResult(
                user=user,
                recommender_ids=recommender_ids,
                obs_ids=obs_ids,
                obs_scores=obs_scores,
                original_ids=original_ids,
            )
        )

    return RunContext(
        dataset=dataset,
        history=history,
        recs_file=recs_file,
        ratings_file=ratings_file,
        items_file=items_file,
        users=users,
    )
