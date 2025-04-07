#include <stdlib.h>
#include <stdio.h> // for debug

// Global variables
const int REC_LIST_SIZE = 10;

// Utility functions

// Returns the index of the first occurence of a target in an array.
int lowerBound(unsigned int arr[], unsigned int size, unsigned int target) {
    int low = 0, high = size - 1, result = -1;

    while (low <= high) {
        int mid = low + (high - low) / 2;
        if (arr[mid] == target) {
            result = mid;
            high = mid - 1;
        } else if (arr[mid] < target) {
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }

    return result;
}

// Returns the index of the last element that is <= target.
int upperBound(unsigned int arr[], unsigned int size, unsigned int target) {
    int low = 0, high = size - 1, result = -1;

    while (low <= high) {
        int mid = low + (high - low) / 2;
        if (arr[mid] == target) {
            result = mid;
            low = mid + 1;
        } else if (arr[mid] < target) {
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }

    return result;
}

// Returns the number of times a target appears in an array.
int countOccurrence(unsigned int arr[], unsigned int size, unsigned int target) {
    int lower = lowerBound(arr, size, target);
    int upper = upperBound(arr, size, target);
    if (lower == -1 || upper == -1) {
        return 0;
    }
    else {
        return upper - lower + 1;
    }
}

// Helper function for qsort -> ascending order.
int comp_asc(const void* a,const void* b) {
      return *(int*)a - *(int*)b;
}

// Helper function for qsort -> descending order.
int comp_desc(const void *a, const void *b) {
    return (*(int *)b - *(int *)a);
}

// Gini index

// Takes an arbitary array of item occurences in output lists.
float gini(unsigned int* propensities, unsigned int size) {

    qsort(propensities, size, sizeof(unsigned int), comp_asc);

    float num = 0;
    for (unsigned int i = 0; i < size; i++) {
        num += propensities[i] * (size + 1 - (i+1));
    }

    float denom = 0;
    for (unsigned int i = 0; i < size; i++) {
        denom += propensities[i];
    }

    float gini = (1.0 / size) * (size + 1.0 - 2.0 * (num/denom));

    return gini;
}

// Takes an array of unique items, and a SORTED array of the complete recommender outputs.
float giniWrapper(unsigned int* targets, unsigned int* out_lists, unsigned int target_size, unsigned int out_size) {
    unsigned int propensities[target_size];
    for (unsigned int i = 0; i < target_size; i++) {
        propensities[i] = countOccurrence(out_lists, out_size, targets[i]);
    }

    return gini(propensities, target_size);
    }

// NDCG

// Takes an array of scores, unique item -> score indicies, and pre-computed log values.
float ndcg(float* scores, unsigned int* rec, unsigned int score_size, float* base_logs, int sorted) {
    // DCG:
    unsigned int rel[REC_LIST_SIZE] = {0};
    for (unsigned int i = 0; i < REC_LIST_SIZE; i++) {
        // use epsilon=0.0001 to avoid evil floating point errors
        if (rec[i] < score_size && scores[rec[i]] > 0.0001) {
            rel[i] = 1;
        }
    }

    float result[10];
    for (unsigned int i = 0; i < REC_LIST_SIZE; i++) {
        result[i] = rel[i] / base_logs[i];
    }

    float dcg = 0;
    for (unsigned int i = 0; i < REC_LIST_SIZE; i++) {
            dcg += result[i];
        }

    // IdealDCG:
    if (sorted==-1) {
        qsort(scores, score_size, sizeof(unsigned int), comp_desc);
    }

    unsigned int ideal_rel[REC_LIST_SIZE] = {0};
    for (unsigned int i = 0; i < REC_LIST_SIZE; i++) {
        // use epsilon=0.0001 to avoid evil floating point errors
        if (scores[i] > 0.0001) {
            ideal_rel[i] = 1;
        }
    }

    float ideal_result[10];
    for (unsigned int i = 0; i < REC_LIST_SIZE; i++) {
        ideal_result[i] = ideal_rel[i] / base_logs[i];
    }

    float idcg = 0;
    for (unsigned int i = 0; i < REC_LIST_SIZE; i++) {
            idcg += ideal_result[i];
        }

    if (idcg == 0) {
        return 0;
    } else {
        return dcg/idcg;
    }

    float ndcg = dcg/idcg;

    return 0;
}

float ndcgWrapper(float* scores, unsigned int* rec, unsigned int score_size, float* base_logs, int sorted) {
    return ndcg(scores, rec, score_size, base_logs, sorted);
}

// Proportional Fairness

float propFair() {
    return 0;
}

float propFairWrapper() {
    return propFair();
}
