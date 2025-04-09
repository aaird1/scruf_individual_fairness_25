import pandas as pd
import numpy as np
import argparse
import metrics_wrapper as mw
import json
import os
import rbo 

# dataset-dependent params
RECS_FILENAME = "data/movies/recs_1m.csv"
RATINGS_FILENAME = "data/movies/ratings_1m.csv"
ITEMS_FILENAME = "data/movies/movie_features_1m.csv"
ITEM_FEATURES = ["women_writer_director", "non-en"]
FAIRNESS_TARGETS = [1.0]
SCORE_SORT_VALUE = True
num_items = 2753
coverage_target = 0.85


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('history_csv',
                        type=str,
                        help='Path to the history CSV file.')
    parser.add_argument('-c','--compressed',
                        action='store_true',
                        help='Whether to use Parquet decompression.')
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    history_csv = args.history_csv
    compressed = args.compressed

    if compressed:
        history = pd.read_parquet(history_csv)
        
    else:
        history = pd.read_csv(history_csv, header=None)
    history.columns = ['time', 'user', 'agent_item', 'id', 'score', 'rank', 'type']
    #history.to_csv('data/history_files/history.csv')
    #exp_values = history_csv.split('_')
    #dataset = exp_values[0]
    #agents = exp_values[1]
    #allocation = exp_values[2]
    #choice = exp_values[3]
  #  fold = exp_values[4].split('.')[0]

# TODO: Fix header situation later
    recs_file = pd.read_csv(RECS_FILENAME, names=['user_id', 'item_id', 'score'], dtype={"user_id":int, "item_id": int, "score": float}, header=None)
    ratings_file = pd.read_csv(RATINGS_FILENAME, names=['user_id', 'item_id', 'rating'], dtype={"user_id": int, "item_id": int, "rating": float}, header=None)
    items_file = pd.read_csv(ITEMS_FILENAME, names=["Item","Feature","BV"], dtype={"Item": int, "Feature": str, "BV": float}, header=None)
    items_file = items_file[items_file['Feature'].isin(ITEM_FEATURES)]
    # TODO: fix later for updated SCRUF branch
    out_view = history[history['type'] == ' output']
    #print(ratings_file.head())
    recommender_ids = out_view['id'].tolist()
    # TODO: janky fix, import properly
    recommender_ids = [int(id) for id in recommender_ids]

    # gini = mw.gini_wrapper(recommender_ids)
    # gini = (1-gini)/0.5

    # print(gini)

    coverage = ((len(set(recommender_ids)))/num_items)/(coverage_target)
    total_items = 0
    count = {}
    proportional_fairness = []
    for feature in ITEM_FEATURES:
        feature_count = 0  

        for id in recommender_ids:
            total_items += 1  # Overall total items

            item = items_file[items_file['Item'] == id]
            
            if item['Feature'].str.contains(feature).any():
                count[feature] = count.get(feature, 0) + 1
                feature_count += 1
    for feature, feature_count in count.items():
        if feature == "women_writer_director":
            proportional_fairness.append((feature_count / (total_items/2))/0.30)
        if feature == "non-en":
            proportional_fairness.append((feature_count / (total_items/2))/0.07)
 
    print(proportional_fairness)





    ndcg_scores = []
    normalized_lp = []
    rbo_scores = []
    user_ids = []
    for user in history['user'].unique():
        history_view = history[history['user'] == user]
        out_view = history_view[history_view['type'] == ' output']
        in_view = history_view[history_view['type'] == '__rec']

        user_ids.append(user)
        user_ratings = ratings_file[ratings_file['user_id'] == int(user)]
        obs_ids = user_ratings['item_id'].tolist()
        obs_scores = user_ratings['rating'].tolist()
        #print(user_ratings)

        recommender_ids = out_view['id'].tolist()

        recommender_ids = [int(id) for id in recommender_ids]

        ndcg_score = mw.ndcg_wrapper(obs_ids, obs_scores, recommender_ids, sorted=SCORE_SORT_VALUE)
        ndcg_scores.append(ndcg_score)
        user_original = recs_file[recs_file['user_id'] == int(user)]
        original = user_original.iloc[:, 1].to_list()

        reranked = recommender_ids
        #print(original)
        lowest_item = -1
        for element in reversed(original):
            if element in reranked:
                try:
                    lowest_item = (next(i for i, val in enumerate(original) if val == element)+1)
                except StopIteration:
                    lowest_item = -1  
                break  
        n_lowest = (lowest_item-10)/(50-10)
        normalized_lp.append(n_lowest)

        original_rbo = user_original.iloc[:10, 1].to_list()

        reranked_rbo = recommender_ids
        ranked_overlap = rbo.RankingSimilarity(original_rbo, reranked_rbo).rbo()

        rbo_scores.append(ranked_overlap)

    mean_ndcg = np.mean(ndcg_scores)
    mean_rbo = np.mean(rbo_scores)
    mean_lip = np.mean(normalized_lp)
    print(mean_lip)
    print(mean_rbo)
    print(np.mean(ndcg_scores))

metrics_data = {

        "mean_ndcg": ndcg_scores,
        "proportional_fairness": proportional_fairness,
        "rbo": rbo_scores,
        "nlip": mean_lip,
        "coverage": coverage
        }

json_filename = os.path.join("results", os.path.splitext(history_csv)[0] + ".json")
json_filename = os.path.splitext(history_csv)[0] + ".json"
with open(json_filename, 'w') as json_file:
    json.dump(metrics_data, json_file, indent=4)
