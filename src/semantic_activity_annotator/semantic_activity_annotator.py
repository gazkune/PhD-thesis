# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 09:14:23 2014

@author: gazkune
"""

"""
This tool is to annotate activities from a dataset
"""

import sys, getopt
import numpy as np
import time, datetime
import pandas as pd

"""
Function to parse arguments from command line
Input:
    argv -> command line arguments
Output:
    dataset_file -> csv file where action properties are with time stamps and activity label
    seed_file -> file where seed activity models are defined (special format)
    output_file -> file to write the identified activities in dataset_file using 
        seed activity models defined at seed_file as templates
"""

def parseArgs(argv):
   dataset_file = ''
   seed_file = ''
   output_file = ''
   try:
      opts, args = getopt.getopt(argv,"hd:s:o:",["dataset=","seed=","ofile="])      
   except getopt.GetoptError:
      print 'semantic_activity_annotator.py -d <dataset> -s <seed> -o <outputfile>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'semantic_activity_annotator.py -d <dataset> -s <seed> -o <outputfile>'
         sys.exit()
      elif opt in ("-d", "--dataset"):
         dataset_file = arg
      elif opt in ("-s", "--seed"):
         seed_file = arg
      elif opt in ("-o", "--ofile"):
         output_file = arg
   
   return dataset_file, seed_file, output_file
   
"""
Function to parse seed activity models in the specified file (special format)
Input:
    seed_file: the name of the file where seed activity models are defined
Output:
    seed_activities: a list of seed activity models
"""

def parseSeedActivityModels(seed_file):
    seed_activities = []
    
    seed_file = open(seed_file, 'r')
    
    not_eof = True
    line_number = 1
    while not_eof:
        line = seed_file.readline().strip('\n')
        if not line: 
            # EOF
            not_eof = False
        else:
            # Line structure:
            # Activity_name: action_prop1 action_prop2 ... action_propN
            seed = line.split(': ')
            # Check whether line is weel formed
            if len(seed) != 2:
                msg = 'Bad formed line (' + str(line_number) + '): expected <Activity_name: action_prop1 action_prop2 ... action_propN>, but read: ' + str(line)
                sys.exit(msg)
                
            # Separate elements in seed to form a list [activity_name, [action_prop1, ...]]
            action_props = seed[1].split(' ')
            
            seed_activities.append([seed[0], action_props])
            line_number = line_number + 1
            
    
    return seed_activities

"""
Function that annotates the dataset contained in activity_df, using seed activity models
defined in seed_activities as templates
Input:
    activity_df: a dataset where timestamped action properties are (pd.DataFrame)
    seed_activities: seed activity models (list of list)
Output:
"""
def annotateActivities(activity_df, seed_activities):
    print 'annotateActivities'


if __name__ == "__main__":
    # call the argument parser 
   [dataset_file, seed_file, output_file] = parseArgs(sys.argv[1:])
   print 'Dataset:', dataset_file
   print 'Seed activity models:', seed_file
   print 'Annotated actions:', output_file
   
   # Read the dataset_file and build a DataFrame 
   activity_df = pd.read_csv(dataset_file, parse_dates=0, header=None, index_col=0)
   
   # Parse the seed_file file
   seed_activities = parseSeedActivityModels(seed_file)
   print 'Seed activity models:'
   print seed_activities