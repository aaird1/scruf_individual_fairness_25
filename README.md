Here’s your content rewritten in clean, organized Markdown format:

```markdown
# Integrating Individual and Group Fairness for Recommender Systems through Social Choice

## SCRUF-D

**SCRUF-D** stands for **Social Choice for Recommendation Under Fairness - Dynamic**.

This repository contains an implementation of the SCRUF-D architecture, based on:

> Burke, R., Mattei, N., Grozin, V., Voida, A., & Sonboli, N. (2022, July).  
> *Multi-agent Social Choice for Dynamic Fairness-aware Recommendation*.  
> In *Adjunct Proceedings of the 30th ACM Conference on User Modeling, Adaptation and Personalization* (pp. 234–244).

> ⚠️ **Note**: Requires **Python 3.9 or earlier** due to compatibility with functions in the `Whalrus` package.

---

## Repository Structure

- `configurations/`: Contains experiment configuration files (.toml)
- `post_processing/`: Scripts for exporting results to CSVs and running analysis
- `scruf_d/`: Core SCRUF-D implementation and environment

---

## Installation

1. Create a Python virtual environment:

   ```bash
   python3 -m venv <environment_name>
   ```

2. Activate the virtual environment:

   ```bash
   source <environment_name>/bin/activate  # On Linux/Mac
   .\<environment_name>\Scripts\activate   # On Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r scruf_d/requirements.txt
   ```

---

## Running the Experiment

1. Navigate to the configuration folder for the experiment you want to run.
2. From that directory, execute the main experiment script:

   ```bash
   python ../../../scruf_d/__main__recsys_25.py
   ```

   For example, if you're in:

   ```bash
   configurations/movie_experiments/all
   ```

   Run:

   ```bash
   python ../../../scruf_d/__main__recsys_25.py
   ```

   This will generate multiple `.toml` files and execute the experiment with different configurations.

---

## Post-Processing

1. Navigate to the `post_processing/` directory.
2. Run one of the following scripts based on your dataset:

   ```bash
   ./run_movie_experiments.sh
   ./run_music_experiments.sh
   ```

   Ensure the `data/` folder is updated appropriately.

3. Once completed, you can run the `rec_weight_tuning` notebook to generate new CSVs.
4. Use the final output CSVs with the `output visualization` notebook to produce plots and visual results.
```