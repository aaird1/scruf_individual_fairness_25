from .context import RunContext, UserResult, build_context
from .registry import available_metrics, get_metric, metric

# Importing definitions registers every built-in metric (ndcg, rbo, nlip,
# coverage, proportional_fairness, gini) with the registry above.
from . import definitions  # noqa: F401

__all__ = [
    "RunContext",
    "UserResult",
    "build_context",
    "available_metrics",
    "get_metric",
    "metric",
]
