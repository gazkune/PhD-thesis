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

if __name__ == "__main__":   
    main(sys.argv)