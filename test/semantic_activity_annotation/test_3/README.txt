CONTENT DESCRIPTION:

This folder has the files to run tests for semantic activity annotator:

run_test.py: it runs synthetic_data_generator with the specifications detailed in adl_script.txt to generate a synthetic dataset. Afterwards, that dataset is used with seed_activity_models.txt to run semantic_activity_annotator, which writes its results in a csv file. Finally, evaluation_tool is used on the csv file to evaluate the results and write them to another file

EXPERIMENT DESCRIPTION:

In this experiment we follow the work done in test_2, but now we add possitive noise, to see the behaviour of semantic_activity_annotator with that kind of seed models with non-unique actions and sensor noise
