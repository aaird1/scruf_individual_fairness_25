# TODO: Add type forcing by converting to unique integer IDs

"""nDCG and Gini computation.

Normally these run through the C extension (metrics.c -> metrics.so) for
speed. Building that extension needs a C compiler (clang/gcc/cc), which
some environments -- e.g. a VM without admin rights -- don't have. Rather
than hard-requiring the compiled library, this module tries to load it and
falls back to equivalent pure-Python/NumPy implementations when it can't
(missing .so, or no compiler was ever able to build one). Everything above
this module (metrics/definitions.py) calls gini_wrapper()/ndcg_wrapper()
the same way either way.
"""

import ctypes
import os
from collections import Counter

import numpy as np
import numpy.ctypeslib as ctl

REC_LIST_SIZE = 10  # matches metrics.c's REC_LIST_SIZE
EPSILON = 0.0001    # matches metrics.c's epsilon for float comparisons

_libdir = os.path.dirname(os.path.abspath(__file__))
_lib = None
try:
    _lib = ctl.load_library("metrics.so", _libdir)
    _lib.giniWrapper.restype = ctypes.c_float
    _lib.ndcgWrapper.restype = ctypes.c_float
except (OSError, ImportError):
    # OSError: file missing, or present but unloadable on this platform --
    # e.g. metrics.so built as a macOS Mach-O binary won't dlopen on Linux
    # ("invalid ELF header"), and vice versa. Some numpy versions re-raise
    # that as ImportError instead of letting the OSError propagate, so both
    # are caught here.
    _lib = None


def _gini_wrapper_c(out_lists):
    out_lists = sorted(out_lists)
    targets = np.array(list(set(out_lists)), dtype=np.uint64)
    target_size = len(targets)
    out_size = len(out_lists)
    c_targets = (ctypes.c_uint * target_size)(*targets)
    c_out_lists = (ctypes.c_uint * out_size)(*out_lists)
    return _lib.giniWrapper(c_targets, c_out_lists, target_size, out_size)


def _ndcg_wrapper_c(items, scores, rec, sorted):
    code = {}
    i = 0
    for item in items:
        code[item] = i
        i += 1
    for item in rec:
        if item not in code.keys():
            code[item] = i
            i += 1
    new_rec = [code[item] for item in rec]

    score_size = len(scores)
    rec_size = len(rec)
    base_logs = np.log2(np.arange(rec_size) + 2)

    c_scores = (ctypes.c_float * score_size)(*scores)
    c_rec = (ctypes.c_uint * rec_size)(*new_rec)
    c_base_logs = (ctypes.c_float * rec_size)(*base_logs)

    sorted_flag = 1 if sorted else -1

    return _lib.ndcgWrapper(c_scores, c_rec, score_size, c_base_logs, sorted_flag)


def _gini_wrapper_python(out_lists):
    """Equivalent to metrics.c's gini()/giniWrapper(): the Gini index over
    how many times each unique item appears in out_lists (0 = perfectly
    even, 1 = maximally concentrated)."""
    counts = Counter(out_lists)
    propensities = sorted(counts.values())
    size = len(propensities)
    if size == 0:
        return float("nan")

    # weight of the i-th smallest count is (size - i), matching the C loop's
    # `size + 1 - (i + 1)`.
    num = sum(count * (size - i) for i, count in enumerate(propensities))
    denom = sum(propensities)
    if denom == 0:
        return float("nan")

    return (1.0 / size) * (size + 1.0 - 2.0 * (num / denom))


def _ndcg_wrapper_python(items, scores, rec, sorted):
    """Equivalent to metrics.c's ndcg()/ndcgWrapper(): DCG/IDCG over the
    first REC_LIST_SIZE recommended items, using `scores` (aligned with
    `items`) as relevance."""
    code = {}
    i = 0
    for item in items:
        code[item] = i
        i += 1
    for item in rec:
        if item not in code.keys():
            code[item] = i
            i += 1
    new_rec = [code[item] for item in rec]

    score_size = len(scores)
    base_logs = np.log2(np.arange(REC_LIST_SIZE) + 2)

    rel = np.zeros(REC_LIST_SIZE)
    for i in range(min(REC_LIST_SIZE, len(new_rec))):
        idx = new_rec[i]
        if idx < score_size and scores[idx] > EPSILON:
            rel[i] = 1
    dcg = float(np.sum(rel / base_logs))

    ideal_scores = list(scores) if sorted else sorted(scores, reverse=True)
    ideal_rel = np.zeros(REC_LIST_SIZE)
    for i in range(min(REC_LIST_SIZE, len(ideal_scores))):
        if ideal_scores[i] > EPSILON:
            ideal_rel[i] = 1
    idcg = float(np.sum(ideal_rel / base_logs))

    if idcg == 0:
        return 0.0
    return dcg / idcg


if _lib is not None:
    gini_wrapper = _gini_wrapper_c
    ndcg_wrapper = _ndcg_wrapper_c
else:
    print(
        "metrics_wrapper: metrics.so not found/loadable (no C extension built) "
        "-- using pure-Python fallbacks for gini/ndcg. Slower, but no compiler needed."
    )
    gini_wrapper = _gini_wrapper_python
    ndcg_wrapper = _ndcg_wrapper_python

