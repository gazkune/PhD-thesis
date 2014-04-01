CONTENT DESCRIPTION:

This folder has the files to run tests for activity model learning

run_test.py: it runs synthetic_data_generator (optionally) to generate a csv file based on adl_script.txt. Afterwards, it runs semantic_activity_annotator, which uses context_model.json to annotate activities in the previous dataset. Then, activity_clustering and activity_model_learner are launched sequentially to obtain new activity patterns. clustering_evaluation is also used to evaluate the performance of activity_clustering

EXPERIMENT DESCRIPTION:

There is no special experiment here. This folder is used to test the approach and run initial experiments. Formal experiments will be in other folders (test_1, test_2, test_3...) with the corresponding experiment descriptions
