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
Input:
    annotated_actions: [timestamp, action, real_label, start/end, annotated_label] (pd.DataFrame)
"""
def evaluate(annotated_actions):
    aux = annotated_actions[annotated_actions.start_end == 'start']
    aux = pd.concat([aux, annotated_actions[annotated_actions.start_end == 'end']])
    aux = aux.sort_index()

    # eval_table will contain the evaluation information
    # [Activity, real_occurrences, annotated_correct_occurrences]
    eval_table = []    
    for i in xrange(len(aux) - 1):
        if aux.start_end.iloc[i] == 'start':        
            activity = aux.real_label.iloc[i]
            print 'Activity:', activity
            eval_index = -1        
            if len(eval_table) == 0:
                print 'First element'
                eval_table.append([activity, 1, 0])
                eval_index = 0
            else:
                for j in xrange(len(eval_table)):
                    try:
                        eval_table[j].index(activity)
                    except ValueError:
                        continue
                    # Activity found
                    print 'Activity', activity, 'is in the evaluation table'
                    eval_index = j
                    eval_table[eval_index][1] = eval_table[eval_index][1] + 1
                    break
                if eval_index == -1:
                    # New activity which is not in the eval_table
                    print 'Activity', activity, 'is not in the evaluation table: append!'
                    eval_table.append([activity, 1, 0])
                    eval_index = len(eval_table) - 1
                
            start = aux.index[i]
            end = aux.index[i+1]
            slice_df = annotated_actions[start:end]
            activity_detected = False
            other_activity = False
            for j in xrange(len(slice_df)):            
                if slice_df.annotated_label.iloc[j] == activity:
                    activity_detected = True
                else:
                    if slice_df.annotated_label.iloc[j] != 'None':
                        # Another activity has been detected, which is not OK
                        other_activity = True
            if activity_detected == True and other_activity == False:
                eval_table[eval_index][2] = eval_table[eval_index][2] + 1
    
    # eval_table is ready. Print it for debugging
    print 'Evaluation table:'
    for i in xrange(len(eval_table)):
        print eval_table[i]
        
                        
    
    """
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
    print 'Length Real Activities:', len(real_activity_groups)
    print 'Length Annotated Activities:', len(annotated_activity_groups)

    aux_list = []
    i = 0    
    while i  < len(real_activity_groups):
        if i + 1 == len(real_activity_groups):
            # we are in the last item, just add it
            aux_list.append(real_activity_groups[i])
            break
        if real_activity_groups[i][0] == real_activity_groups[i + 1][0]:
            # Two contiguous equal activities
            if real_activity_groups[i + 1][1] - real_activity_groups[i][2] < 3:
                # Fuse both activities
                # Take into account that the criterion of distance < 3 is arbitrary
                aux_list.append([real_activity_groups[i][0], real_activity_groups[i][1], real_activity_groups[i+1][2]])
                i = i + 2
            else:
                aux_list.append(real_activity_groups[i])
                i = i + 1
        else:
            aux_list.append(real_activity_groups[i])                
            i = i + 1
                
    print 'Length Real Activities:', len(aux_list)
    print 'Length Annotated Activities:', len(annotated_activity_groups)   

    if len(aux_list) > len(annotated_activity_groups):
        max_len = len(aux_list)
    else:
        max_len = len(annotated_activity_groups)
    
    for i in xrange(max_len):
        if i < len(aux_list) and i < len(annotated_activity_groups):
            print aux_list[i], ' | ', annotated_activity_groups[i]
        elif i < len(aux_list) and i >= len(annotated_activity_groups):
            print aux_list[i], ' |  ---'
        elif i < len(annotated_activity_groups) and i >= len(aux_list):
            print '---  | ', annotated_activity_groups[i]
       """     

"""
Main function
"""

if __name__ == "__main__":
    # call the argument parser 
   inputfile = parseArgs(sys.argv[1:])
   print 'Input file:', inputfile
   
   annotated_actions = pd.read_csv(inputfile, parse_dates=0, index_col=0)   
   
   evaluate(annotated_actions)
      