# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 15:29:27 2014

@author: gazkune
"""

"""
A tool to evaluate the performance of semantic_acitvity_annotator.py
"""
import sys, getopt
#import numpy as np
#import time, datetime
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
            #print 'Activity:', activity
            eval_index = -1        
            if len(eval_table) == 0:
                #print 'First element'
                eval_table.append([activity, 1, 0])
                eval_index = 0
            else:
                for j in xrange(len(eval_table)):
                    try:
                        eval_table[j].index(activity)
                    except ValueError:
                        continue
                    # Activity found
                    #print 'Activity', activity, 'is in the evaluation table'
                    eval_index = j
                    eval_table[eval_index][1] = eval_table[eval_index][1] + 1
                    break
                if eval_index == -1:
                    # New activity which is not in the eval_table
                    #print 'Activity', activity, 'is not in the evaluation table: append!'
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
Main function
"""

def main(argv):
   # call the argument parser 
   inputfile = parseArgs(argv[1:])
   print 'Input file:', inputfile
   
   annotated_actions = pd.read_csv(inputfile, parse_dates=0, index_col=0)   
   
   evaluate(annotated_actions)

if __name__ == "__main__":   
   main(sys.argv)
