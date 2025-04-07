# RecSys 2025 SCRUF Experiments
## To run an expeiment
1.  run scruf/__main_MODIFY.py  from the working directory of the folder in configurations for the experiment you want to run
2.  run ./run_experiments.sh  in the post_processing folder with data folder updated and the correct post_processor chosen (movies vs music)
3.  run create_csv.py
4.  these files will now be ready to run rec_weight tuning notebook, that will create new csv's, then the output viz notebook will take those final csv's
