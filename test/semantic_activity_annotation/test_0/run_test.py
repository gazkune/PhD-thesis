# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 15:32:42 2014

@author: gazkune
"""

import sys, os, getopt, time
sys.path.append(os.path.abspath("/home/gazkune/repositories/gorka.azkune/src/synthetic_data_generator"))
from synthetic_data_generator import main as sdg_main
sys.path.append(os.path.abspath("/home/gazkune/repositories/gorka.azkune/src/semantic_activity_annotator"))
from semantic_activity_annotator import main as saa_main
from evaluation_tool import main as eval_main

"""
Function to parse arguments from command line
Input:
    argv -> command line arguments
Output:
    
"""

def parseArgs(argv):
   adl_script = ''
   synthetic_data = ''
   seed_activity_models = ''
   labeled_actions = ''
   evaluation_results = ''
   try:
      opts, args = getopt.getopt(argv,"ha:d:s:l:e:",["adl=","dataset=","seed=","labeled=","evaluation="])
   except getopt.GetoptError:
      print 'run_test.py -a <adl_script> -d <synthetic_data> -s <seed_activity_models> -l <labeled_actions> -e <evaluation_results>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'run_test.py -a <adl_script> -d <synthetic_data> -s <seed_activity_models> -l <labeled_actions> -e <evaluation_results>'
         sys.exit()
      elif opt in ("-a", "--adl"):
         adl_script = arg
      elif opt in ("-d", "--dataset"):
         synthetic_data = arg
      elif opt in ("-s", "--seed"):
         seed_activity_models = arg
      elif opt in ("-l", "--labeled"):
         labeled_actions = arg
      elif opt in ("-e", "--evaluation"):
         evaluation_results = arg
   
   return adl_script, synthetic_data, seed_activity_models, labeled_actions, evaluation_results


def main(argv):
    # call the argument parser 
   [adl_script, synthetic_data, seed_activity_models, labeled_actions, evaluation_results] = parseArgs(argv[1:])
   print 'Files:'
   print adl_script
   print synthetic_data
   print seed_activity_models
   print labeled_actions
   print evaluation_results
   
   # Call synthetic_data_generator   
   arguments = ['synthetic_data_generator.py', '-i', adl_script, '-o', synthetic_data]
   sdg_main(arguments)
   
   time.sleep(1)
   
   # Call semantic_activity_annotation
   arguments = ['semantic_activity_annotator.py', '-d', synthetic_data, '-s', seed_activity_models, '-o', labeled_actions]
   saa_main(arguments)
   
   time.sleep(1)
   
   # Call evaluation_tool
   arguments = ['evaluation_tool.py', '-i', labeled_actions]
   eval_main(arguments)
    
if __name__ == "__main__":
   main(sys.argv)
