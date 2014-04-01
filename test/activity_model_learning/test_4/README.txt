CONTENT DESCRIPTION:

This folder has the files to run tests for activity model learning

run_test.py: it runs synthetic_data_generator (optionally) to generate a csv file based on adl_script.txt. Afterwards, it runs semantic_activity_annotator, which uses context_model.json to annotate activities in the previous dataset. Then, activity_clustering and activity_model_learner are launched sequentially to obtain new activity patterns. clustering_evaluation is also used to evaluate the performance of activity_clustering

COMMAND TO RUN:

python run_test.py -a adl_script.txt -d synthetic_data.csv -c context_model.json -l annotated_data.csv -r raw_results.csv -s summary.json -e evaluation.csv -p learnt_patterns.json

EXPERIMENT DESCRIPTION:

This experiment will test the activity model learner with demanding activity and sensor activation patterns, but no noise
