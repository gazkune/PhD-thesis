# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 17:12:03 2014

@author: gazkune
"""
"""
This tool is to group sensor activations and associated actions in activity clusters
"""

import sys, getopt
import numpy as np
import time, datetime
import pandas as pd
import json
from scipy import stats
from copy import deepcopy

"""
Function to parse arguments from command line
Input:
    argv -> command line arguments
Output:
    summary_file -> json file where learnt activities, action patterns,
        object and sensor statistics, duration and location can be found
    dataset_file -> csv file where timestamped sensor activation are listed where
        [timestamp, sensor, action, annotated_label, a_start_end, location, filter, assign, d_start_end]
        has to be at least
    context_file -> file where activities, objects and sensors are described (json format)    
"""

def parseArgs(argv):
   summary_file = ''
   dataset_file = ''
   context_file = ''
   
   try:
      opts, args = getopt.getopt(argv,"hs:d:c:",["summary=","dataset=","context="])      
   except getopt.GetoptError:
      print 'activity_model_learner.py -s <summary_file> -d <dataset_file> -c <context_model>'      
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'activity_model_learner.py -s <summary_file> -d <dataset_file> -c <context_model>'         
         sys.exit()
      elif opt in ("-s", "--summary"):
         summary_file = arg      
      elif opt in ("-d", "--dataset"):
         dataset_file = arg
      elif opt in ("-c", "--context"):
         context_file = arg   
       
   return summary_file, dataset_file, context_file

"""
Function to visualize (print) learn activities in a convenient form
Input:
    learnt_activities: a dict where each activity is listed with
        [locations, occurrences, duration, patterns, actions, objects]
Output:
    print information in a convenient way to visualize better
"""

def visualizeLearntActivities(learnt_activities):
    print 'Visualize learnt activities:'
    print '----------------------------------------'
    
    for key in learnt_activities:
        print 'Activity', str(key)
        print '  Occurrences:', learnt_activities[key]['occurrences']
        print '  Duration:', learnt_activities[key]['duration']
        print '  Locations:', learnt_activities[key]['locations']
        print '  Patterns:'
        patterns = learnt_activities[key]['patterns']
        
        for i in xrange(len(patterns)):
            print ' ', float(patterns[i][0]) / float(learnt_activities[key]['occurrences']), patterns[i][1]
            
        print '  Objects:'
        object_list = learnt_activities[key]['objects']
        for i in xrange(len(object_list)):
            print ' ', float(object_list[i][0]) / float(learnt_activities[key]['occurrences']), object_list[i][1]
            
        print '  Actions:'
        action_list = learnt_activities[key]['actions']
        for i in xrange(len(action_list)):
            print ' ', float(action_list[i][0]) / float(learnt_activities[key]['occurrences']), action_list[i][1]

"""
Function to calculate edit (levenshtein) distance between two patterns
WARNING: this is not probably the original edit distance, since it considers the
order of the elements in a character sequence. In our case, we do not care
about the order of the elements
Input:
    a: pattern of actions ([action0,..., actionN])
    b: pattern of actions ([action0,..., actionN])
Output:
    dist: the edit (levenshtein) distance between two patterns
"""

#def edit_distance(a, b):
    

"""
"""

def jaccard(a, b):    
    common = len(np.intersect1d(a, b))
    total = len(set(a + b))
    return float(common) / float(total)

"""
Function to calculate definitive action patterns baed on learnt_activities
Initial idea:
1) Remove actions that occur in the same pattern more than once
2) Fuse patterns that have the actions but different order (edit distance = 0)
3) Calculate the "pattern-distance" for every 2 patterns of the same activity
   pattern_distance(P1, P2) = edit_distance(P1, P2) / (Freq_P1 - Freq_P2)
   Be careful with Freq_P1 - Freq_P2 = 0 (add a small constant to remove the danger?)
   New distance definition with Jaccard coeffecient?
   pattern_distance(P1, P2) = (1 - Jaccard(P1, P2)) / (Freq_P1 - Freq_P2)
4) Calculate mean and standard deviation of pattern distances for an activity and 
   build a threshold (heuristic), such that patterns with distances bellow that threshold should
   be fused into a pattern
"""
def calculateDefinitiveActionPatterns(learnt_activities):
    print 'Calculate definitive patterns'
    
    # Iterate through activities and implement the 4 step process for each of them
    for key in learnt_activities:
        print '---------------------------------------------'
        print '---------------------------------------------'
        print 'Activity', str(key)
        patterns0 = learnt_activities[key]['patterns']
        
        # Step 1: remove repeated actions
        patterns1 = []
        for i in xrange(len(patterns0)):
            actions = patterns0[i][1]
            deduplicated = set(actions)
            patterns1.append([patterns0[i][0], list(deduplicated)])
            # Print for initial debug
            print '  ', float(patterns1[i][0]) / float(learnt_activities[key]['occurrences']), patterns1[i][1]
        
        print '  Number of patterns after step 1:', len(patterns1)
        
        # Step 2 fuse equal patterns        
        to_fuse = np.zeros((len(patterns1), len(patterns1)))
        for i in xrange(len(patterns1)):
            for j in xrange(len(patterns1)):
                jaccard_dist = jaccard(patterns1[i][1], patterns1[j][1])               
                # Take advantage of the loop to fuse patterns
                if i != j and jaccard_dist == 1:
                    # Fuse those two patterns 
                    to_fuse[i, j] = 1                    
        
        print '  Fusion matrix:'
        print to_fuse
        
        # Use to_fuse matrix to fuse patterns and store in patterns2
        removed = []
        patterns2 = []
        for i in xrange(len(to_fuse)):
            try:
                removed.index(i)
                continue
            except ValueError:
                # Insert this pattern
                patterns2.append(patterns1[i])
                for j in xrange(len(to_fuse[i])):
                    if to_fuse[i][j] == 1:
                        # Sum frequencies
                        patterns2[i][0] = patterns2[i][0] + patterns1[j][0]
                        # Mark j to be removed
                        removed.append(j)
                        
        print '  Number of patterns after step 2:', len(patterns2)
        for i in xrange(len(patterns2)):
            if len(patterns2) < len(patterns1):
                print '  ', float(patterns2[i][0]) / float(learnt_activities[key]['occurrences']), patterns2[i][1]
            
        # Step 3: calculate Jaccard based pattern distance between every two activities        
        # Initialize jaccard_matrix with -1 values
        jaccard_matrix = np.zeros((len(patterns2), len(patterns2)))
        jaccard_matrix = jaccard_matrix - 1
        # Initialize frequencies list, where pattern frequencies are stored for convenience        
        frequencies = []
        for i in xrange(len(patterns2)):
            frequencies.append(patterns2[i][0] / float(learnt_activities[key]['occurrences']))
            for j in xrange(len(patterns2)):
                jaccard_matrix[i][j] = jaccard(patterns2[i][1], patterns2[j][1])
                     
        
        print '  Jaccard matrix for step 3:'
        print jaccard_matrix        
        
        # Calculate the JF coeffecients for each pattern
        # and store them in th jf_matrix only if pattern2 > 2
        if len(patterns2) > 2:
            #jf_matrix = np.array((len(patterns2), len(patterns2)))
            jf_matrix = jaccard_matrix
        
            for i in xrange(len(jf_matrix)):
                f = frequencies[i]
                for j in xrange(len(jf_matrix)):
                    jf_matrix[i][j] = jaccard_matrix[i][j] / f

            # Fill diagonal with zeros, since they are not important        
            np.fill_diagonal(jf_matrix, 0)
            print '  JF matrix:'
            print jf_matrix
        
            # Step 4: Implement the heuristic to fuse patterns. Fuse those patterns whose
            # JF coefficient is higher than mean(JF) + (std(JF)/2)
            # Obtain the upper triangle of the jf_matrix
            up_triangle = []
            i = 0        
            while i < len(jf_matrix):
                j = i + 1
                while j < len(jf_matrix):                
                    up_triangle.append(jf_matrix[i][j])
                    j = j + 1
                    
                i = i + 1

            # Obtain the lower triangle of the jf_matrix
            i = 1
            down_triangle = []
            while i < len(jf_matrix):
                j = 0
                while j < i:
                    down_triangle.append(jf_matrix[i][j])
                    j = j + 1
                    
                i = i + 1
                
            # Obtain a list with bot triangles to calculate the mean and std without
            # diagonal values of the jf_matrix
            both_triangles = up_triangle + down_triangle
            print '  JF mean:', np.mean(both_triangles), 'std:', np.std(both_triangles), 'median:', np.median(both_triangles)
            print '  JF score at percentile 75:', stats.scoreatpercentile(both_triangles, 75)
            # T!! It seems this last metrics can be the good one: 
            # max_i {Jaccard(P1, Pi) / Freq(P1)}
            # Initial tests suggest that we can use that metric and the 
            # combination of (mean, std) heuristic for the fourth step of the algorithm!
            # Criterion 1: use mean + std/2 on the JF matrix -> fusing_threshold_1
            # Criterion 2: use 75 percentil on the JF matrix -> fusing_threshold_2
            # Fuse patterns and store them in patterns3
            aux_1 = deepcopy(patterns2)
            aux_2 = deepcopy(patterns2)
            fusing_threshold_1 = np.mean(both_triangles) + (np.std(both_triangles)/2)
            fusing_threshold_2 = stats.scoreatpercentile(both_triangles, 75)            
            to_remove_1 = []
            to_remove_2 = []
            for i in xrange(len(patterns2)):
                jf = max(jf_matrix[i])
                jf_index = jf_matrix[i].tolist().index(jf)
                if jf > fusing_threshold_1:
                    # Fuse those two patterns 
                    aux_1[jf_index][0] = aux_1[jf_index][0] + aux_1[i][0]
                    to_remove_1.append(i)                    
                if jf > fusing_threshold_2:
                    # Fuse those two patterns
                    aux_2[jf_index][0] = aux_2[jf_index][0] + aux_2[i][0]
                    to_remove_2.append(i)
                    
            # Remove elements from patterns3
            patterns3_1 = []
            patterns3_2 = []
            for i in xrange(len(aux_1)):
                try:
                    to_remove_1.index(i)
                except ValueError:
                    patterns3_1.append(aux_1[i])
                try:
                    to_remove_2.index(i)
                except ValueError:
                    patterns3_2.append(aux_2[i])
                    
            # patterns3 has the definitive patterns
            # Print patterns3 as output for criterion 1 and 2
            print '  Number of patterns after step 4, criterion 1:', len(patterns3_1)
            for i in xrange(len(patterns3_1)):
                print '  ', float(patterns3_1[i][0]) / float(learnt_activities[key]['occurrences']), patterns3_1[i][1]
            
            
            print '  Number of patterns after step 4, criterion 2:', len(patterns3_2)
            for i in xrange(len(patterns3_2)):
                print '  ', float(patterns3_2[i][0]) / float(learnt_activities[key]['occurrences']), patterns3_2[i][1]
                    
        else:
            print 'Activity', key, 'has already two or less patterns'            
        
        
        
"""
Main function
"""

def main(argv):
    # call the argument parser
    [summary_file, dataset_file, context_file] = parseArgs(argv[1:])
    
    # Read the dataset_file and build a DataFrame 
    df = pd.read_csv(dataset_file, parse_dates=0, index_col=0)
    
    # Read and parse the summary_file
    learnt_activities = json.loads(open(summary_file).read())
    
    # For debugging purposes, visualize learnt_activities
    visualizeLearntActivities(learnt_activities)
    
    # Calculate definitive pattern for every activity
    calculateDefinitiveActionPatterns(learnt_activities)
   
if __name__ == "__main__":   
    main(sys.argv)