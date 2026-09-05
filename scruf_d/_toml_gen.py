import toml
import numpy as np
import pandas as pd
import pathlib
from ruamel.yaml import YAML

yaml = YAML(typ="safe")
params = yaml.load(open("params.yaml", encoding="utf-8")) #change here for new params files

folder_path = params["config"]["folder_path"]

base_toml = params["config"]["base_toml"]
def remove_suffix(input_string, suffix):
    if suffix and input_string.endswith(suffix):
        return input_string[:-len(suffix)]
    return input_string

def generate_config(base, config_number, rec_weight, choice, allocation, filename_suffix, fold):
    base_toml = toml.load(base)
    new_filename = remove_suffix(base_toml["output"]["filename"], ".json") + f"_{filename_suffix}_{rec_weight}_fold{fold}.json"
    #csv_filename = remove_suffix(base_toml["post"]["properties"]["summary_filename"], ".csv") + f"_{filename_suffix}.csv"
    base_toml["output"]["filename"] = new_filename
    #base_toml["post"]["properties"]["summary_filename"] = csv_filename
    # Check if the choice is "weighted_scoring"
    #base_toml["data"]["rec_filename"] = f"ambar_recs{fold}.csv"
    if choice == "weighted_scoring":
        base_toml["choice"]["choice_class"] = choice
    else:
        base_toml["choice"]["properties"]["whalrus_rule"] = choice
        base_toml["choice"]["properties"]["tie_breaker"] = "Random"
        base_toml["choice"]["properties"]["ignore_weights"] = "false"
        base_toml["choice"]['choice_class'] = "whalrus_scoring"
    base_toml["allocation"]["allocation_class"] = allocation
    if allocation == "weighted_product_allocation":
        base_toml["allocation"]["properties"]["compatibility_exponent"] = 2
        base_toml["allocation"]["properties"]["fairness_exponent"] = 1
    base_toml["choice"]["properties"]["recommender_weight"] = rec_weight


    name = f"{folder_path}/{remove_suffix(base.split('/')[-1], '.toml')}_{filename_suffix}_{rec_weight}_fold{fold}.toml"
    with open(name, 'w') as f:
        toml.dump(base_toml, f)
    return name, new_filename



config_number_counter = 0
path_list = []

choices = params['config']['choice']
allocations = params['config']['allocation']
rec_weights = params['config']['rec_weight']
folds = params['config']['fold']

for choice in choices:
    for allocation in allocations:
        for rec_weight in rec_weights:
            for fold in folds:
                config_number_counter += 1
                toml_name, history_name = generate_config(base_toml, config_number_counter, float(rec_weight),
                                                            choice, allocation, f"{choice}_{allocation}", fold)
                path_list.append((config_number_counter, toml_name, history_name, float(rec_weight), fold))

config_df = pd.DataFrame(path_list, columns=['Config Number', 'Config Path', 'Output Path', 'recommender_weight', 'fold'])
config_df.to_csv(f"{folder_path}/path_list.csv")