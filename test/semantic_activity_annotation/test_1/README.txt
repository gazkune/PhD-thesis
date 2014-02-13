CONTENT DESCRIPTION:

This folder has the files to run tests for semantic activity annotator:

run_test.py: it runs synthetic_data_generator with the specifications detailed in adl_script.txt to generate a synthetic dataset. Afterwards, that dataset is used with seed_activity_models.txt to run semantic_activity_annotator, which writes its results in a csv file. Finally, evaluation_tool is used on the csv file to evaluate the results and write them to another file

EXPERIMENT DESCRIPTION:

We will test the behaviour of semantic_activity_annotator in presence of missing sensor activations. For that purpose, adl_script.txt will contain sensor activation patterns were a sensor activation is missing from the seed activity model. More concretely, MakeChocolate and BrushTeeth have new activation patterns with 0.01 probability. For MakeChocolate, hasChocolate was removed, while for BrushTeeth hasBrusher was removed.
