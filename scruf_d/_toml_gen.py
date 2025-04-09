import toml
import pandas as pd
from ruamel.yaml import YAML
import itertools

yaml = YAML(typ="safe")

# Load parameters from YAML
params = yaml.load(open("params.yaml", encoding="utf-8"))
folder_path = params["config"]["folder_path"]
base_toml_file = params["config"]["base_toml"]

# Extract choices, allocations, and recommender weights
choices = params["config"]["choice"]
allocations = params["config"]["allocation"]
rec_weights = params["config"]["rec_weight"]

# Extract agent delta values
agent_deltas = params["config"].get("agent", {})


def remove_suffix(input_string, suffix):
    """Remove a specific suffix from a string."""
    if suffix and input_string.endswith(suffix):
        return input_string[:-len(suffix)]
    return input_string

def generate_agent_combinations():
    """Generate all possible agent delta combinations."""
    agent_keys = list(agent_deltas.keys())  # ['one', 'two']
    agent_value_combinations = list(itertools.product(*agent_deltas.values()))

    return [
        {agent_keys[i]: agent_value_combinations[j][i] for i in range(len(agent_keys))}
        for j in range(len(agent_value_combinations))
    ]


def update_agent_deltas(base_toml, agent_delta_config):
    """Update agent delta values in the correct TOML format."""
    if "agent" not in base_toml:
        base_toml["agent"] = {}

    for agent_key, delta in agent_delta_config.items():
        if agent_key in base_toml["agent"]:  # Ensure the agent exists in the TOML file
            if "preference" not in base_toml["agent"][agent_key]:
                base_toml["agent"][agent_key]["preference"] = {}
            base_toml["agent"][agent_key]["preference"]["delta"] = delta
    return base_toml

def format_agent_deltas(agent_delta_config):
    """Format agent deltas into a filename-friendly string."""
    return "_".join([f"agent{key}-{delta}" for key, delta in agent_delta_config.items()])

def generate_config(base, config_number, rec_weight, choice, allocation, agent_delta_config):
    """Generate and save a modified TOML configuration file."""
    base_toml = toml.load(base)

    # Update agent deltas
    base_toml = update_agent_deltas(base_toml, agent_delta_config)

    # Format deltas into filename
    delta_str = format_agent_deltas(agent_delta_config)
    
    choice2 = choice
    if choice == "weighted_scoring":
        choice2 = "Rescore"

    allocation2 = allocation
    if allocation == "weighted_product_allocation":
        allocation2 = "Product"
    if allocation == "product_lottery":
        allocation2 = "lottery"
    if allocation == "least_fair":
        allocation2 = "leastFair"

    # Modify output filenames with deltas
    base_filename = remove_suffix(base_toml["output"]["filename"], ".json")
    new_filename = f"{base_filename}_{choice2}_{allocation2}_{rec_weight}_{delta_str}.json"
    base_toml["output"]["filename"] = new_filename

    # Set choice properties
    if choice == "weighted_scoring":
        base_toml["choice"]["choice_class"] = choice
    else:
        base_toml["choice"]["properties"]["whalrus_rule"] = choice
        base_toml["choice"]["properties"]["tie_breaker"] = "Random"
        base_toml["choice"]["properties"]["ignore_weights"] = "false"
        base_toml["choice"]['choice_class'] = "whalrus_scoring"
    
    # Set allocation properties
    base_toml["allocation"]["allocation_class"] = allocation
    if allocation == "weighted_product_allocation":
        base_toml["allocation"]["properties"]["compatibility_exponent"] = 2
        base_toml["allocation"]["properties"]["fairness_exponent"] = 1
    
    base_toml["choice"]["properties"]["recommender_weight"] = rec_weight

    # Generate config filename with deltas
    config_name = f"{folder_path}/{remove_suffix(base.split('/')[-1], '.toml')}_{choice2}_{allocation2}_{rec_weight}_{delta_str}.toml"
    
    # Save the modified TOML file
    with open(config_name, 'w') as f:
        toml.dump(base_toml, f)

    return config_name, new_filename

# Generate configurations
config_number_counter = 0
path_list = []
agent_combinations = generate_agent_combinations()


for choice in choices:
    for allocation in allocations:
        for rec_weight in rec_weights:
            for agent_delta_config in agent_combinations:
                config_number_counter += 1
                toml_name, history_name = generate_config(
                    base_toml_file, 
                    config_number_counter, 
                    float(rec_weight),
                    choice, 
                    allocation, 
                    agent_delta_config
                )
                path_list.append((config_number_counter, toml_name, history_name, float(rec_weight), agent_delta_config))

# Save the generated configuration paths
config_df = pd.DataFrame(path_list, columns=['Config Number', 'Config Path', 'Output Path', 'Recommender Weight', 'Agent Deltas'])
config_df.to_csv(f"{folder_path}/path_list.csv", index=False)



