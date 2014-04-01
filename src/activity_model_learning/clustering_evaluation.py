# -*- coding: utf-8 -*-
"""
Created on Mon Mar 31 17:38:34 2014

@author: gazkune
"""

"""
This tool is to evaluate the output of activity_clustering.py
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
    raw_results -> csv file obtained from activity_clustering
    [timestamp, sensor, action, activity, start_end, annotated_label, a_start_end, location, filter, assign, d_start_end]    
    eval_file -> file with evaluation (true/false positives and true/false negatives)    
"""

def parseArgs(argv):
    raw_results_file = ''
    eval_file = ''
    try:
      opts, args = getopt.getopt(argv,"hr:e:",["raw=","evaluation="])
    except getopt.GetoptError:
      print 'clustering_evaluation.py -r <raw_results> -e <evaluation_file>'
      sys.exit(2)
   
    for opt, arg in opts:
      if opt == '-h':
          print 'clustering_evaluation.py -r <raw_results> -e <evaluation_file>'
          sys.exit()
      elif opt in ("-r", "--raw"):
         raw_results_file = arg      
      elif opt in ("-e", "--evaluation"):
         eval_file = arg
         
    return raw_results_file, eval_file
    
"""
Function to extract activties contained in raw_df
Input:
    raw_df: pd.DataFrame with sensor, action, activity...
Output
    activities: list of extracted activities, with special 'None' activity included
"""

def extractActivities(raw_df):
    activity_index = raw_df[raw_df['activity'] != 'None'].index
    activities = []
    
    for i in xrange(len(activity_index)):
        activity = raw_df.loc[activity_index[i], 'activity']
        try:
            activities.index(activity)
        except ValueError:
            activities.append(activity)
            
    # Append 'None' activity
    activities.append('None')
    return activities

"""
Function to evaluate the performance of activity_clustering compared
to SA3 and ground-truth
Input:
    raw_df: pd.DataFrame with sensor, action, activity...
Output:
    eval_abs_df: evaluation with true/false positives and negatives (absolute numbers)
    eval_percent_df: evaluation with true/false positives and negatives (percentages)
"""
def evaluate(raw_df, activities):    

    # Build eval_df DataFrame    
    eval_abs_df = pd.DataFrame(activities, columns=['activity'])
    total_actions = []    
    
    sa3_total = [] # Total actions annotated by SA3
    sa3_tp = [] # True positives annotated by SA3 algorithm
    sa3_fp = [] # False positivies annotated by SA3
    sa3_fn = [] # False negatives annotated by SA3
    
    ac_total = [] # Total actions learnt by activity clustering
    ac_tp = [] # True positives learnt by activity clustering
    ac_fp = [] # False positives learnt by activity clustering
    ac_fn = [] # False negatives learnt by activity clustering
    
    for i in xrange(len(activities)):        
        # Calculate total actions
        index = raw_df[raw_df['activity'] == activities[i]].index
        total_actions.append(float(len(index)))
        
        # Calculate total actions annotated by SA3
        index = raw_df[raw_df['annotated_label'] == activities[i]].index
        sa3_total.append(float(len(index)))
        
        # Calculate True Positives by SA3
        index = raw_df[np.logical_and(raw_df['activity'] == activities[i], raw_df['annotated_label'] == activities[i])].index
        sa3_tp.append(float(len(index)))
        
        # Calculate False Positive actions by SA3 
        # e.g.: no MakeChocolate action -> MakeChocolate
        index = raw_df[np.logical_and(raw_df['activity'] != activities[i], raw_df['annotated_label'] == activities[i])].index
        sa3_fp.append(float(len(index)))
        
        # Calculate False Negatives by SA3
        # e.g.: MakeChocolate action -> MakeCoffee
        index = raw_df[np.logical_and(raw_df['activity'] == activities[i], raw_df['annotated_label'] != activities[i])].index
        sa3_fn.append(float(len(index)))
        
        # Calculate total actions learnt by activity clustering
        index = raw_df[raw_df['assign'] == activities[i]].index
        ac_total.append(float(len(index)))
        
        # Calculate True Positives by activity clustering
        index = raw_df[np.logical_and(raw_df['activity'] == activities[i], raw_df['assign'] == activities[i])].index
        ac_tp.append(float(len(index)))
        
        # Calculate False Positive actions by activity clustering 
        # e.g.: no MakeChocolate action -> MakeChocolate
        index = raw_df[np.logical_and(raw_df['activity'] != activities[i], raw_df['assign'] == activities[i])].index
        ac_fp.append(float(len(index)))
        
        # Calculate False Negatives by activity clustering
        # e.g.: MakeChocolate action -> MakeCoffee
        index = raw_df[np.logical_and(raw_df['activity'] == activities[i], raw_df['assign'] != activities[i])].index
        ac_fn.append(float(len(index)))
        
    
    # Absolute numbers
    eval_abs_df['total_actions'] = pd.DataFrame(total_actions)
    
    eval_abs_df['SA3_total'] = pd.DataFrame(sa3_total)
    eval_abs_df['SA3_TP'] = pd.DataFrame(sa3_tp)
    eval_abs_df['SA3_FP'] = pd.DataFrame(sa3_fp)
    eval_abs_df['SA3_FN'] = pd.DataFrame(sa3_fn)
    
    eval_abs_df['AC_total'] = pd.DataFrame(ac_total)
    eval_abs_df['AC_TP'] = pd.DataFrame(ac_tp)
    eval_abs_df['AC_FP'] = pd.DataFrame(ac_fp)
    eval_abs_df['AC_FN'] = pd.DataFrame(ac_fn)   
    
    # Percentages
    eval_percent_df = eval_abs_df.copy()
    eval_percent_df['SA3_TP'] = eval_abs_df['SA3_TP'] / eval_abs_df['total_actions']
    eval_percent_df['SA3_FP'] = eval_abs_df['SA3_FP'] / eval_abs_df['SA3_total']
    eval_percent_df['SA3_FN'] = eval_abs_df['SA3_FN'] / eval_abs_df['total_actions']
    
    eval_percent_df['AC_TP'] = eval_abs_df['AC_TP'] / eval_abs_df['total_actions']
    eval_percent_df['AC_FP'] = eval_abs_df['AC_FP'] / eval_abs_df['SA3_total']
    eval_percent_df['AC_FN'] = eval_abs_df['AC_FN'] / eval_abs_df['total_actions']    
    
    return eval_abs_df, eval_percent_df

"""
Main function
"""

def main(argv):
    # call the argument parser
    [raw_results_file, eval_file] = parseArgs(argv[1:])
    
    print 'Parsed arguments:'
    print '   ', raw_results_file
    print '   ', eval_file    
   
    # Read the annotated_file and build a DataFrame 
    raw_df = pd.read_csv(raw_results_file, parse_dates=0, index_col=0)
    
    activities = extractActivities(raw_df)
    print 'Extracted activities:'
    print activities
    
    [eval_abs_df, eval_percent_df] = evaluate(raw_df, activities)
    
    # Concat both df-s to test
    eval_df = pd.concat([eval_abs_df, eval_percent_df], keys=['absolute', 'percentage'])
    
    print 'Evaluation df (absolute numbers):'
    print eval_abs_df.head(10)    
    
    print 'Evaluation df (percentages):'
    print eval_percent_df.head(10)
    
    eval_df.to_csv(eval_file)
    

if __name__ == "__main__":   
    main(sys.argv)