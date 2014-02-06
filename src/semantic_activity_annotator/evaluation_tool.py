# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 15:29:27 2014

@author: gazkune
"""

"""
A tool to evaluate the performance of semantic_acitvity_annotator.py
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
    inputfile -> csv file where action properties are with time stamps, real activity label and
    annotated label    
"""

def parseArgs(argv):
   inputfile = ''   
   try:
      opts, args = getopt.getopt(argv,"hi:",["input="])      
   except getopt.GetoptError:
      print 'evaluation_tool.py -i <inputfile>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'evaluation_tool.py -i <inputfile>'
         sys.exit()
      elif opt in ("-i", "--input"):
         inputfile = arg      
   
   return inputfile

"""
The evaluation function
Approach: first of all, detect activity groups in the column real_label. If there is an action
labeled as 'None' between start and end of an activity, we know it is noise, so filter. Detect also
activity groups in the column annotated_label. Check if activity groups in annotated_labels 
intersect with the activity groups in real_label
Input:
    annotated_actions: [timestamp, action, real_label, annotated_label] (pd.DataFrame)
"""
def evaluate(annotated_actions):
    real_activity_groups = []
    annotated_activity_groups = []
    real_start_index = -1
    real_end_index = -1
    annotated_start_index = -1
    annotated_end_index = -1
    for i in xrange(len(annotated_actions)):
        # Real activity groups
        if real_start_index == -1:
            # No group started
            if annotated_actions.real_label.iloc[i] != 'None':
                real_start_index = i
                real_activity = annotated_actions.real_label.iloc[i]
        else:
            if annotated_actions.real_label.iloc[i] != real_activity:
                real_end_index = i - 1
                real_activity_groups.append([real_activity, real_start_index, real_end_index])
                if annotated_actions.real_label.iloc[i] != 'None':
                    real_start_index = i
                    real_activity = annotated_actions.real_label.iloc[i]
                else:
                    real_start_index = -1
        # Annotated activity groups
        if annotated_start_index == -1:
            # No group started
            if annotated_actions.annotated_label.iloc[i] != 'None':
                annotated_start_index = i
                annotated_activity = annotated_actions.annotated_label.iloc[i]
        else:
            if annotated_actions.annotated_label.iloc[i] != annotated_activity:
                annotated_end_index = i - 1
                annotated_activity_groups.append([annotated_activity, annotated_start_index, annotated_end_index])
                if annotated_actions.annotated_label.iloc[i] != 'None':
                    annotated_start_index = i
                    annotated_activity = annotated_actions.annotated_label.iloc[i]
                else:
                    annotated_start_index = -1
    
    # Filter 'None' labels in real_activity_groups when appropriate
    # Print both lists before for debugginf pruposes
    print 'Real activity groups:'
    for i in xrange(len(real_activity_groups)):
        print real_activity_groups[i]
    print 'Annotated activity groups:'
    for i in xrange(len(annotated_activity_groups)):
        print annotated_activity_groups[i]
    print 'Length Real Activities:', len(real_activity_groups)
    print 'Length Annotated Activities:', len(annotated_activity_groups)

"""
Main function
"""

if __name__ == "__main__":
    # call the argument parser 
   inputfile = parseArgs(sys.argv[1:])
   print 'Input file:', inputfile
   
   annotated_actions = pd.read_csv(inputfile, parse_dates=0, index_col=0)
   
   evaluate(annotated_actions)
      