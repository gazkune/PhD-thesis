CONTENT DESCRIPTION:

This folder has the files to run tests for semantic activity annotator:

run_test.py: it runs synthetic_data_generator with the specifications detailed in adl_script.txt to generate a synthetic dataset. Afterwards, that dataset is used with seed_activity_models.txt to run semantic_activity_annotator, which writes its results in a csv file. Finally, evaluation_tool is used on the csv file to evaluate the results and write them to another file

EXPERIMENT DESCRIPTION:

The idea in this experiment is to design seed activity models that do not have unique actions. Imagine we have actions A, B, C and D.

Seed 1: A B C
Seed 2: C B D
Seed 3: D B A

Generate a synthetic data base which contains more actions (E, F, G...) and see how the semantic_activity_annotator performs
