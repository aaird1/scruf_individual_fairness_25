import os
import sys
import subprocess
from pathlib import Path
import csv
import statistics
import json

directory = Path("data/movies")

script = "post_processor_movie.py"

for file_path in directory.glob("*"):
    if file_path.is_file():
        print(f"Processing {file_path}...")
        subprocess.run([sys.executable, script, str(file_path), "-c"])


json_directory = "data/movies/"  
output_csv = "movie_weights_full.csv"

# Initialize a list to store the processed data
data_list = []

# Loop through all JSON files in the directory
for filename in os.listdir(json_directory):
    if filename.endswith(".json"):  # Only process JSON files
        file_path = os.path.join(json_directory, filename)
       # print(filename)
        
        # Open and load the JSON file
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
            
            # Split the filename by underscores and use as separate columns
            filename_parts = filename.replace(".json", "").split("_")
            
            # Ensure the list is long enough, add empty strings for missing parts if needed
            filename_parts.extend([''] * (9 - len(filename_parts)))  # Adjust 5 to your max column length
            
            # Extract relevant fields and include the filename
            record = {
                "data": filename_parts[0],
                "agents": filename_parts[1],
                "choice": filename_parts[2],
                "allocation": filename_parts[3],
                "weight": filename_parts[4],
                "one": filename_parts[5],
                "two": filename_parts[6],
                "three": filename_parts[7],
                "four": filename_parts[8],
                #"mean_ndcg": data.get("mean_ndcg", ""),
                "mean_ndcg": statistics.mean(data["mean_ndcg"]) if isinstance(data.get("mean_ndcg"), list) else None,
                "mean_rbo": statistics.mean(data["rbo"]) if isinstance(data.get("rbo"), list) else None,
                "coverage": data.get("coverage", ""),
                # Flatten proportional_fairness into separate columns
                "proportional_fairness_women": data.get("proportional_fairness", [None, None])[0],
                "proportional_fairness_non-en": data.get("proportional_fairness", [None, None])[1],
                #"mean_rbo": data.get("rbo"),
                "nlip": data.get("nlip"),
                "gini": data.get("gini", "")
                
            }
            data_list.append(record)

# Write the data to a CSV file
with open(output_csv, 'w', newline='') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=data_list[0].keys())
    writer.writeheader()
    writer.writerows(data_list)

print(f"Data saved to {output_csv}")
