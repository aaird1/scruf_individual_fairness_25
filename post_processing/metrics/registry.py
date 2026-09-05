"""A tiny name -> function registry so metrics can be picked by name from a
dataset TOML file or a `--metrics` CLI flag, instead of being wired in by
hand in each post-processing script."""

from __future__ import annotations

from typing import Callable

_REGISTRY: dict[str, Callable] = {}


def metric(name: str):
    """Decorator: register a metric function under `name`.

    A metric function takes a single `RunContext` and returns a dict of
    output fields to merge into the results JSON (e.g. {"coverage": 0.9}).
    """

    def decorator(fn: Callable) -> Callable:
        if name in _REGISTRY:
            raise ValueError(f"Metric '{name}' is already registered.")
        _REGISTRY[name] = fn
        return fn

    return decorator


def get_metric(name: str) -> Callable:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"Unknown metric '{name}'. Available metrics: {', '.join(available_metrics())}"
        ) from None


def available_metrics() -> list[str]:
    return sorted(_REGISTRY)
