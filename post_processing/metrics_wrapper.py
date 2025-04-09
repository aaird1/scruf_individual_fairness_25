# TODO: Add type forcing by converting to unique integer IDs

import numpy as np
import numpy.ctypeslib as ctl
import ctypes

libname = 'metrics.so'
libdir = './'
lib=ctl.load_library(libname, libdir)

# Gini Index
py_gini = lib.giniWrapper
lib.giniWrapper.restype = ctypes.c_float

# nDCG
py_ndcg = lib.ndcgWrapper
lib.ndcgWrapper.restype = ctypes.c_float

def gini_wrapper(out_lists):
    out_lists.sort()
    targets = np.array(list(set(out_lists)), dtype=np.uint64)
    target_size = len(targets)
    out_size = len(out_lists)
    c_targets = (ctypes.c_uint * target_size)(*targets)
    c_out_lists = (ctypes.c_uint * out_size)(*out_lists)

    return py_gini(c_targets, c_out_lists, target_size, out_size)

def ndcg_wrapper(items, scores, rec, sorted):
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
    base_logs = np.log2(np.arange(rec_size)+2)

    c_scores = (ctypes.c_float * score_size)(*scores)
    c_rec = (ctypes.c_uint * rec_size)(*new_rec)
    c_base_logs = (ctypes.c_float * rec_size)(*base_logs)

    if sorted:
        sorted = 1
    else:
        sorted = -1

    return py_ndcg(c_scores, c_rec, score_size, c_base_logs, sorted)
