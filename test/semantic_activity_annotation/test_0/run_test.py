# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 15:32:42 2014

@author: gazkune
"""

import sys, getopt, time

#import synthetic_data_generator.synthetic_data_generator
from synthetic_data_generator.synthetic_data_generator import main as sdg_main
from semantic_activity_annotator.semantic_activity_annotator import main as saa_main
from semantic_activity_annotator.evaluation_tool import main as eval_main

"""
Function to parse arguments from command line
Input:
    argv -> command line arguments
Output:
    
"""

def parseArgs(argv):
   exec_data_generator = False 
   adl_script = ''
   synthetic_data = ''
   context_model = ''
   seed_activity_models = ''
   labeled_actions = ''
   evaluation_results = ''
   try:
      opts, args = getopt.getopt(argv,"ha:d:c:s:l:e:",["adl=","dataset=","context=","seed=","labeled=","evaluation="])
   except getopt.GetoptError:
      print 'run_test.py -a <adl_script> -d <synthetic_data> -c <context_model> -s <seed_activity_models> -l <labeled_actions> -e <evaluation_results>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'run_test.py -a <adl_script> -d <synthetic_data> -c <context_model> -s <seed_activity_models> -l <labeled_actions> -e <evaluation_results>'
         sys.exit()
      elif opt in ("-a", "--adl"):
         adl_script = arg
         exec_data_generator = True
      elif opt in ("-d", "--dataset"):
         synthetic_data = arg
      elif opt in ("-c", "--context"):
         context_model = arg
      elif opt in ("-s", "--seed"):
         seed_activity_models = arg
      elif opt in ("-l", "--labeled"):
         labeled_actions = arg
      elif opt in ("-e", "--evaluation"):
         evaluation_results = arg
   
   return exec_data_generator, adl_script, synthetic_data, context_model, seed_activity_models, labeled_actions, evaluation_results


def main(argv):
    # call the argument parser 
   [exec_data_generator, adl_script, synthetic_data, context_model, seed_activity_models, labeled_actions, evaluation_results] = parseArgs(argv[1:])
   print 'Execute data generator:', exec_data_generator
   print 'Files:'
   print adl_script
   print synthetic_data
   print context_model
   print seed_activity_models
   print labeled_actions
   print evaluation_results
   
   if context_model != '':
       print 'run_test: WARNING: as context_model has been provided, seed activity models file will not be used'
       
   
   # Call synthetic_data_generator
   if exec_data_generator == True:
       arguments = ['synthetic_data_generator.py', '-i', adl_script, '-o', synthetic_data]
       sdg_main(arguments)
       time.sleep(1)       
                   
   # Call semantic_activity_annotation
   arguments = ['semantic_activity_annotator.py', '-d', synthetic_data, '-c', context_model, '-s', seed_activity_models, '-o', labeled_actions]
   saa_main(arguments)
   
   time.sleep(1)
   
   # Call evaluation_tool
   arguments = ['evaluation_tool.py', '-i', labeled_actions, '-o', evaluation_results]
   eval_main(arguments)
    
if __name__ == "__main__":
   main(sys.argv)
