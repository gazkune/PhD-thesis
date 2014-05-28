# -*- coding: utf-8 -*-
"""
Created on Tue May 27 15:57:13 2014

@author: gazkune
"""
"""
A tool to fuse several evaluation csv-s and obtain mean and standard deviation values
for existing parameters such as SA_TP, SA_FP and so on
"""

import sys, getopt
import numpy as np
import pandas as pd

"""
Function to parse arguments from command line
Input:
    argv -> command line arguments
Output:
    inputfile -> a txt file with a list of csv files to be processed
    outputfile -> the resulting final csv
"""

def parseArgs(argv):
   inputfile = ''
   outputfile = ''
   try:
      opts, args = getopt.getopt(argv,"hi:o:",["input=","output="])      
   except getopt.GetoptError:
      print 'multiple_user_evaluator.py -i <inputfile> -o <outputfile>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'multiple_user_evaluator.py -i <inputfile> -o <outputfile>'
         sys.exit()
      elif opt in ("-i", "--input"):
         inputfile = arg
      elif opt in ("-o", "--output"):
         outputfile = arg
   
   return inputfile, outputfile

"""
Function to parse the input txt and return a list pd.DataFrames
Input:
    inputfile: a txt file where csv files are lsited
Output:
    df_list: a list of pd.dataFrames. Only the percentage values are stored in each 
    df. Only 'activity', 'SA3_TP', 'SA3_FP', 'SA3_FN', 'AC_TP', 'AC_FP', 'AC_FN'
    columns are stored
"""
def parseInputFile(inputfile):
    # open input and output files
    fd = open(inputfile, 'r')
    
    # initialize empty list
    df_list = []
    
    for line in fd.readlines():
        print line
        # Use multi-index, but with 'activity' column as secondary index
        df = pd.read_csv(line[:-1], index_col = [0, 2])
        df = df[['SA3_TP', 'SA3_FP', 'SA3_FN', 'AC_TP', 'AC_FP', 'AC_FN']].loc['percentage']
        df_list.append(df)
        
    return df_list


"""
Function to calculate resultant df, which store mean and standard deviation
values for each column and activity
Input:
    df_list: a list of pd.DataFrames
Output:
    res_df: a pd.DataFrame, with activities as rows 'SA3_TP', 'SA3_FP', 
    'SA3_FN', 'AC_TP', 'AC_FP', 'AC_FN' as columns
"""

def calculateResultantDF(df_list):
    # Take the first df of the list and obtain activities
    # activities is a np.array
    activities = df_list[0].reset_index()['activity'].values
    print activities
    # Take the first element of the df_list to initialize res_df
    res_df = df_list[0].copy(deep=True)
    res_df = pd.concat([res_df, res_df], keys=['mean', 'std'])
    # Now res_df has two blocks, the first one for mean SA3_TP, SA3_FP... 
    # and the second one for standard deviations
    
    # Save into cols the columns we want to calculate
    cols = ['SA3_TP', 'SA3_FP', 'SA3_FN', 'AC_TP', 'AC_FP', 'AC_FN']
    
    # concatenate all elements from df_list
    conc_df = pd.concat(df_list)
    
    # run a loop for each column and each activity, to calculate mean
    # and standard deviation
    for col in xrange(len(cols)):
        for act in xrange(len(activities)):
            activity = activities[act]
            param = cols[col]
            # values is a np.array with all values of 'activity' for the 
            # column 'param'
            values = conc_df.loc[activity][param].values
            
            # Assign mean value in 'res_df', in the corresponing place
            res_df.loc['mean', activity][param] = np.mean(values)
            print 'Activity', activity, 'Col', param, 'mean =', np.mean(values)
            
            # Assign std value in 'res_df', in the corresponing place
            res_df.loc['std', activity][param] = np.std(values)
            print 'Activity', activity, 'Col', param, 'std =', np.std(values)
    
    return res_df
    
"""
Main function
"""

def main(argv):
   # call the argument parser 
   [inputfile, outputfile] = parseArgs(argv[1:])
   print 'Input file:', inputfile
   print 'Output file:', outputfile
   
   df_list = []
   df_list = parseInputFile(inputfile)
   
   print 'df_list length:', len(df_list)
   
   res_df = calculateResultantDF(df_list)
   
   print res_df
   
   res_df.to_csv(outputfile)

if __name__ == "__main__":   
   main(sys.argv)