#!/bin/sh
source ../facct_2025_exp/venv/bin/activate

# for file in $PWD/data/w_movies/*; do
#     python3 post_processor_movies.py $file -c
for file in $PWD/data/movies_rescore_tuning/*; do
    python3 post_processor_movie.py $file -c
done
