"""The actual metric implementations, each registered under the name used in
a dataset TOML's `metrics = [...]` list or a `--metrics` CLI flag.

To add a new metric: write a function taking a `RunContext` and returning a
dict of fields to add to the results JSON, then decorate it with
`@metric("your_name")`. It is immediately usable from any dataset config.
"""

from __future__ import annotations

import numpy as np
import rbo as rbo_lib

import metrics_wrapper as mw

from .context import RunContext
from .registry import metric


@metric("ndcg")
def ndcg(ctx: RunContext) -> dict:
    scores = [
        mw.ndcg_wrapper(u.obs_ids, u.obs_scores, u.recommender_ids, sorted=ctx.dataset.score_sort)
        for u in ctx.users
    ]
    return {
        "ndcg_scores": scores,
        "mean_ndcg": float(np.mean(scores)) if scores else None,
    }


@metric("rbo")
def rbo(ctx: RunContext) -> dict:
    scores = []
    for u in ctx.users:
        original_top = u.original_ids[:10]
        scores.append(rbo_lib.RankingSimilarity(original_top, u.recommender_ids).rbo())
    return {
        "rbo_scores": scores,
        "mean_rbo": float(np.mean(scores)) if scores else None,
    }


@metric("nlip")
def nlip(ctx: RunContext) -> dict:
    """Normalized lowest-item-position: how far down the original ranking the
    lowest-surviving reranked item came from, normalized to [list_low, list_high]."""
    low, high = ctx.dataset.list_low, ctx.dataset.list_high
    scores = []
    for u in ctx.users:
        reranked = set(u.recommender_ids)
        lowest_position = -1
        for position, item in enumerate(u.original_ids, start=1):
            if item in reranked:
                lowest_position = position
        scores.append((lowest_position - low) / (high - low))
    return {
        "nlip_scores": scores,
        "nlip": float(np.mean(scores)) if scores else None,
    }


@metric("coverage")
def coverage(ctx: RunContext) -> dict:
    unique_recommended = len(set(ctx.all_recommender_ids))
    return {"coverage": (unique_recommended / ctx.dataset.num_items) / ctx.dataset.coverage_target}


@metric("proportional_fairness")
def proportional_fairness(ctx: RunContext) -> dict:
    """For each protected feature, the share of all recommendations carrying
    that feature, divided by its target proportion (1.0 == exactly on target)."""
    all_ids = ctx.all_recommender_ids
    total = len(all_ids)
    result = {}
    for feature in ctx.dataset.features:
        if total == 0:
            result[feature.name] = None
            continue
        feature_ids = set(ctx.items_file[ctx.items_file["Feature"] == feature.name]["Item"])
        count = sum(1 for item_id in all_ids if item_id in feature_ids)
        result[feature.name] = (count / total) / feature.proportion_target
    return {"proportional_fairness": result}


@metric("gini")
def gini(ctx: RunContext) -> dict:
    ids = sorted(ctx.all_recommender_ids)
    if not ids:
        return {"gini": None}
    return {"gini": mw.gini_wrapper(ids)}
