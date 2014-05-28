# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 15:32:42 2014

@author: gazkune
"""

import sys, getopt, time


from synthetic_data_generator.synthetic_data_generator import main as sdg_main
from semantic_activity_annotator.semantic_activity_annotator import main as saa_main
from activity_model_learning.activity_clustering import main as ac_main
from activity_model_learning.clustering_evaluation import main as ce_main
from activity_model_learning.activity_model_learner import main as aml_main

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
   annotated_dataset = ''
   raw_data_file = ''
   summary_results = ''
   evaluation_file = ''
   patterns_file = ''
   try:
      opts, args = getopt.getopt(argv,"ha:d:c:l:r:s:e:p:",["adl=","dataset=","context=","labeled=","raw=","summary","evaluation=","patterns="])
   except getopt.GetoptError:
      print 'run_test.py -a <adl_script> -d <synthetic_data> -c <context_model> -l <labeled_actions> -r <raw_results> -s <summary> -e <evaluation_results> -p <patterns>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'run_test.py -a <adl_script> -d <synthetic_data> -c <context_model> -l <labeled_actions> -r <raw_results> -s <summary> -e <evaluation_results> -p <patterns>'
         sys.exit()
      elif opt in ("-a", "--adl"):
         adl_script = arg
         exec_data_generator = True
      elif opt in ("-d", "--dataset"):
         synthetic_data = arg
      elif opt in ("-c", "--context"):
         context_model = arg
      elif opt in ("-l", "--labeled"):
         annotated_dataset = arg
      elif opt in ("-r", "--raw"):
         raw_data_file = arg
      elif opt in ("-s", "--summary"):
          summary_results = arg
      elif opt in ("-e", "--evaluation"):
         evaluation_file = arg
      elif opt in ("-p", "--patterns"):
         patterns_file = arg
   
   return exec_data_generator, adl_script, synthetic_data, context_model, annotated_dataset, raw_data_file, summary_results, evaluation_file, patterns_file


def main(argv):
    # call the argument parser
   [exec_data_generator, adl_script, synthetic_data, context_model, annotated_dataset, raw_data_file, summary_results, evaluation_file, patterns_file] = parseArgs(argv[1:])
   print 'Execute data generator:', exec_data_generator
   print 'Files:'
   print adl_script
   print synthetic_data
   print context_model
   print annotated_dataset
   print raw_data_file
   print summary_results
   print evaluation_file
   print patterns_file       
   
   # Call synthetic_data_generator
   if exec_data_generator == True:
       arguments = ['synthetic_data_generator.py', '-i', adl_script, '-o', synthetic_data]
       sdg_main(arguments)
       time.sleep(1)       
                   
   # Call semantic_activity_annotation
   arguments = ['semantic_activity_annotator.py', '-d', synthetic_data, '-c', context_model, '-o', annotated_dataset]
   saa_main(arguments)
   
   time.sleep(1)
   
   
   # Call activity_clustering
   # Time approach 0 (simple time distance to the centre of activity)
   raw_t0 = raw_data_file.split('.')[0] + '_t0.' + raw_data_file.split('.')[1]
   summary_t0 = summary_results.split('.')[0] + '_t0.' + summary_results.split('.')[1]
   arguments = ['activity_clustering.py', '-a', annotated_dataset, '-c', context_model, '-t', 0, '-r', raw_t0, '-s', summary_t0]
   ac_main(arguments)   
   
   time.sleep(1)
   
   # Time approach 1 (duration normalized time distance to static centre)
   raw_t1 = raw_data_file.split('.')[0] + '_t1.' + raw_data_file.split('.')[1]
   summary_t1 = summary_results.split('.')[0] + '_t1.' + summary_results.split('.')[1]
   arguments = ['activity_clustering.py', '-a', annotated_dataset, '-c', context_model, '-t', 1, '-r', raw_t1, '-s', summary_t1]
   ac_main(arguments)
   
   time.sleep(1)
   
   # Time approach 2 (duration normalized time distance to dynamic centre)
   raw_t2 = raw_data_file.split('.')[0] + '_t2.' + raw_data_file.split('.')[1]
   summary_t2 = summary_results.split('.')[0] + '_t2.' + summary_results.split('.')[1]
   arguments = ['activity_clustering.py', '-a', annotated_dataset, '-c', context_model, '-t', 2, '-r', raw_t2, '-s', summary_t2]
   ac_main(arguments)
   
   time.sleep(1)
   
   # Evaluation for time approach 0
   eval_t0 = evaluation_file.split('.')[0] + '_t0.' + evaluation_file.split('.')[1]
   arguments = ['clustering_evaluation.py', '-r', raw_t0, '-e', eval_t0]
   ce_main(arguments)
   
   time.sleep(1)
   
   # Evaluation for time approach 1
   eval_t1 = evaluation_file.split('.')[0] + '_t1.' + evaluation_file.split('.')[1]
   arguments = ['clustering_evaluation.py', '-r', raw_t1, '-e', eval_t1]
   ce_main(arguments)
   
   time.sleep(1)
   
   # Evaluation for time approach 2
   eval_t2 = evaluation_file.split('.')[0] + '_t2.' + evaluation_file.split('.')[1]
   arguments = ['clustering_evaluation.py', '-r', raw_t2, '-e', eval_t2]
   ce_main(arguments)
   
   time.sleep(1)
   
   # Activity model learner for time approach 0
   patterns_t0 = patterns_file.split('.')[0] + '_t0.' + patterns_file.split('.')[1]
   arguments = ['activity_model_learner.py', '-s', summary_t0, '-d', raw_t0, '-c', context_model, '-p', patterns_t0]
   aml_main(arguments)
   
   time.sleep(1)
   
   # Activity model learner for time approach 1
   patterns_t1 = patterns_file.split('.')[0] + '_t1.' + patterns_file.split('.')[1]
   arguments = ['activity_model_learner.py', '-s', summary_t1, '-d', raw_t1, '-c', context_model, '-p', patterns_t1]
   aml_main(arguments)
   
   time.sleep(1)
   
   # Activity model learner for time approach 0
   patterns_t2 = patterns_file.split('.')[0] + '_t2.' + patterns_file.split('.')[1]
   arguments = ['activity_model_learner.py', '-s', summary_t2, '-d', raw_t2, '-c', context_model, '-p', patterns_t2]
   aml_main(arguments)
    
if __name__ == "__main__":
   main(sys.argv)
