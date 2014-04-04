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
    patterns_file -> file where learnt patterns will be stored (json format)
"""

def parseArgs(argv):
   summary_file = ''
   dataset_file = ''
   context_file = ''
   patterns_file = ''
   
   try:
      opts, args = getopt.getopt(argv,"hs:d:c:p:",["summary=","dataset=","context=", "patterns="])
   except getopt.GetoptError:
      print 'activity_model_learner.py -s <summary_file> -d <dataset_file> -c <context_model> -p <patterns>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'activity_model_learner.py -s <summary_file> -d <dataset_file> -c <context_model> -p <patterns>'
         sys.exit()
      elif opt in ("-s", "--summary"):
         summary_file = arg      
      elif opt in ("-d", "--dataset"):
         dataset_file = arg
      elif opt in ("-c", "--context"):
         context_file = arg
      elif opt in ("-p", "--patterns"):
         patterns_file = arg
       
   return summary_file, dataset_file, context_file, patterns_file

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
    dist: the modified edit (levenshtein) distance between two patterns
"""

def edit_distance(a, b):
    return len(set(a + b)) - len(np.intersect1d(a, b))
    

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
Input:
    learnt_activities: dict with patterns extracted by activity_clustering for each activity
Output:
    learnt_patterns: dict with the final patterns learnt by function
"""
def calculateDefinitiveActionPatterns(learnt_activities):
    print 'Calculate definitive patterns'
    learnt_patterns = {}
    
    # Iterate through activities and implement the 4 step process for each of them
    for key in learnt_activities:
        print '---------------------------------------------'
        print '---------------------------------------------'
        print 'Activity', str(key)        
        patterns0 = learnt_activities[key]['patterns']
        # patterns0[i][0] is the number of occurrences of that activity
        # tranform it to [0, 1] frequencies        
        
        # Step 1: remove repeated actions and calculate frequencies
        patterns1 = []
        for i in xrange(len(patterns0)):
            actions = patterns0[i][1]
            deduplicated = set(actions)
            freq = float(patterns0[i][0]) / float(learnt_activities[key]['occurrences'])
            patterns1.append([freq, list(deduplicated)])            
            # Print for initial debug
            print '  ', patterns1[i][0], patterns1[i][1]
        
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
        #patterns2 = fusePatterns(patterns1, to_fuse)
        
        patterns2 = []
        action_patterns = []
        freq_patterns = []
        targets = {}
        for i in xrange(len(to_fuse)):
            one = max(to_fuse[i])
            one_index = to_fuse[i].tolist().index(one)
            
            if one == 0:
                # this pattern doesn't have to be fused, but append it
                action_patterns.append(patterns1[i][1])
                freq_patterns.append(patterns1[i][0])
            elif one == 1:
                if patterns1[i][0] > patterns1[one_index][0]:                
                    # Check whether i is already in targets dict
                    try:
                        target = targets[i]
                    except KeyError:
                        target = i
                    
                    actions = patterns1[target][1]
                    try:
                        index = action_patterns.index(actions)
                        freq_patterns[index] = freq_patterns[index] + patterns1[one_index][0]
                    
                    except ValueError:
                        action_patterns.append(actions)
                        freq_patterns.append(patterns1[target][0] + patterns1[one_index][0])
                        
                    to_fuse[one_index][i] = 2 # Don't fuse again, but don't be zero either
                    targets[one_index] = target
                else:
                    # Check whether one_index is already in targets dict
                    try:
                        target = targets[one_index]
                    except KeyError:
                        target = one_index
                    
                    actions = patterns1[target][1]
                    try:
                        index = action_patterns.index(actions)
                        freq_patterns[index] = freq_patterns[index] + patterns1[i][0]
                    
                    except ValueError:
                        action_patterns.append(actions)
                        freq_patterns.append(patterns1[i][0] + patterns1[target][0])
                    
                    
                    to_fuse[one_index][i] = 2 # Don't fuse again, but don't be zero either
                    targets[i] = target
                    
        # action_patterns and freq_patterns have to aligned index-wise
        # build fused_patterns combining both
        for i in xrange(len(action_patterns)):
            patterns2.append([freq_patterns[i], action_patterns[i]])
                            
            
        # Step 3: calculate Jaccard based pattern distance between every two activities        
        # Initialize jaccard_matrix with -1 values
        jaccard_matrix = np.zeros((len(patterns2), len(patterns2)))
        jaccard_matrix = jaccard_matrix - 1
        edit_matrix = np.zeros((len(patterns2), len(patterns2)))
        # Initialize frequencies list, where pattern frequencies are stored for convenience        
        frequencies = []
        for i in xrange(len(patterns2)):
            frequencies.append(patterns2[i][0])
            for j in xrange(len(patterns2)):
                jaccard_matrix[i][j] = jaccard(patterns2[i][1], patterns2[j][1])
                edit_matrix[i][j] = edit_distance(patterns2[i][1], patterns2[j][1])
                     
        
        print '  Jaccard matrix for step 3:'
        print jaccard_matrix
        #print '  Edit matrix:'
        #print edit_matrix
        
        # Calculate the JF coeffecients for each pattern
        # and store them in th jf_matrix only if pattern2 > 2
        if len(patterns2) > 2:
            #jf_matrix = np.array((len(patterns2), len(patterns2)))
            jf_matrix = deepcopy(jaccard_matrix)
            ef_matrix = np.zeros((len(patterns2), len(patterns2)))
        
            for i in xrange(len(jf_matrix)):
                f = frequencies[i]
                for j in xrange(len(jf_matrix)):
                    jf_matrix[i][j] = jaccard_matrix[i][j] / f
                    ef_matrix[i][j] = edit_matrix[i][j] * f

            # Fill diagonal with zeros, since they are not important        
            np.fill_diagonal(jf_matrix, 0)
            #print '  EF matrix:'
            #print ef_matrix
        
            # Step 4: Implement the heuristic to fuse patterns. Fuse those patterns whose
            # JF coefficient is higher than mean(JF) + (std(JF)/2)   
            
            # test a new approach -> outlier detection with leave one-out method
            #new_patterns = leaveOneOut(patterns2, learnt_activities[key]['occurrences'])
            
            # Another approach: use only Jaccard distance to fuse patterns
            patterns3 = deepcopy(patterns2)
            pat_length = len(patterns3)
            end_loop = False
            while not end_loop:
                # Re-calculate Jaccard matrix
                jaccard_matrix = np.zeros((len(patterns3), len(patterns3)))
                for i in xrange(len(patterns3)):
                    for j in xrange(len(patterns3)):
                        jaccard_matrix[i][j] = jaccard(patterns3[i][1], patterns3[j][1])
                patterns3 = medianBasedOutliers(patterns3, jaccard_matrix)                
                if len(patterns3) == pat_length or len(patterns3) <= 2:
                    end_loop = True
                else:
                    pat_length = len(patterns3)    
                    
            # patterns3 has the definitive patterns            
                    
        else:
            patterns3 = deepcopy(patterns2)            
            print 'Activity', key, 'has already two or less patterns'
        
        # Print patterns3 as output for criterion 1 and 2
        # For now, we only have one criterion
        """            
        print '  Number of patterns after step 4, criterion 1:', len(patterns3_1)
        for i in xrange(len(patterns3_1)):
            patterns3_1[i][0] = float(patterns3_1[i][0]) / float(learnt_activities[key]['occurrences'])
            print '  ', patterns3_1[i][0], patterns3_1[i][1]
                        
        print '  Number of patterns after step 4, criterion 2:', len(patterns3_2)
        for i in xrange(len(patterns3_2)):
            patterns3_2[i][0] = float(patterns3_2[i][0]) / float(learnt_activities[key]['occurrences'])
            print '  ', patterns3_2[i][0], patterns3_2[i][1]
        
        """
        # Add patterns3 to learnt_patterns
        cr = {}
        cr['criterion1'] = patterns3
        #cr['criterion2'] = patterns3_2
        learnt_patterns[key] = cr
        
    
    return learnt_patterns

"""
Function to fuse patterns (suming their frequencies) based on the
fusion_matrix provided
Input:
    patterns: a list of patterns to be fused
        [[freq, [action0,..., actionN]], [freq, [action0,..., actionN]]]
    fusion_matrix: a matrix of len(patterns) x len(patterns) size
        if fusion_matrix[i, j] == 1, fuse pattern i with j
Output:
    fused_patterns: the new list of fused patterns
"""
# TODO: Check this function to use where needed. It seems there is a problem
# when calling, since frequencies were not well sumed in a test I did
def fusePatterns(patterns, fusion_matrix):
    fused_patterns = []
    action_patterns = []
    freq_patterns = []
    targets = {}
    for i in xrange(len(fusion_matrix)):
        one = max(fusion_matrix[i])
        one_index = fusion_matrix[i].tolist().index(one)
            
        if one == 0:
            # this pattern doesn't have to be fused, but append it
            action_patterns.append(patterns[i][1])
            freq_patterns.append(patterns[i][0])
        elif one == 1:
            if patterns[i][0] > patterns[one_index][0]:                
                # Check whether i is already in targets dict
                try:
                    target = targets[i]
                except KeyError:
                    target = i
                    
                actions = patterns[target][1]
                try:
                    index = action_patterns.index(actions)
                    freq_patterns[index] = freq_patterns[index] + patterns[one_index][0]
                    
                except ValueError:
                    action_patterns.append(actions)
                    freq_patterns.append(patterns[target][0] + patterns[one_index][0])
                        
                fusion_matrix[one_index][i] = 2 # Don't fuse again, but don't be zero either
                targets[one_index] = target
            else:
                # Check whether one_index is already in targets dict
                    try:
                        target = targets[one_index]
                    except KeyError:
                        target = one_index
                    
                    actions = patterns[target][1]
                    try:
                        index = action_patterns.index(actions)
                        freq_patterns[index] = freq_patterns[index] + patterns[i][0]
                    
                    except ValueError:
                        action_patterns.append(actions)
                        freq_patterns.append(patterns[i][0] + patterns[target][0])
                    
                    
                    fusion_matrix[one_index][i] = 2 # Don't fuse again, but don't be zero either
                    targets[i] = target
                    
        # action_patterns and freq_patterns have to aligned index-wise
        # build fused_patterns combining both
        for i in xrange(len(action_patterns)):
            fused_patterns.append([freq_patterns[i], action_patterns[i]])

    return fused_patterns

"""
"""
def medianBasedOutliers(patterns, matrix):
    #print patterns
    #print matrix
    [up_triangle, down_triangle] = obtainBothTriangles(matrix)    
    both_triangles = up_triangle + down_triangle
    median = np.median(both_triangles)
    dist = np.abs(both_triangles - median)
    deviation = sum(dist) / len(dist)
    fusing_threshold = max(0.7, median + deviation)
    print '  Jaccard median:', median, 'std:', deviation
    print '  Jaccard fusing threshold:', fusing_threshold

    # Now we have the threshold, fuse patterns
    # Before doing so, fill diagonal with 0
    np.fill_diagonal(matrix, 0)
    
    to_fuse = np.zeros((len(patterns), len(patterns)))
    for i in xrange(len(to_fuse)):
        max_value = max(matrix[i])
        max_index = matrix[i].tolist().index(max_value)
        if max_value >= fusing_threshold:
            to_fuse[i][max_index] = 1
    
    
    print '  Patterns to be fused:'
    print to_fuse
    
    fused_patterns = []
    action_patterns = []
    freq_patterns = []
    targets = {}
    for i in xrange(len(to_fuse)):
        one = max(to_fuse[i])
        one_index = to_fuse[i].tolist().index(one)
        
        if one == 1:
            if patterns[i][0] > patterns[one_index][0]:                
                # Check whether i is already in targets dict
                try:
                    target = targets[i]
                except KeyError:
                    target = i
                
                actions = patterns[target][1]
                try:
                    index = action_patterns.index(actions)
                    freq_patterns[index] = freq_patterns[index] + patterns[one_index][0]
                    
                except ValueError:
                    action_patterns.append(actions)
                    freq_patterns.append(patterns[target][0] + patterns[one_index][0])                    
                    
                to_fuse[one_index][i] = 2 # Don't fuse again, but don't be zero either
                targets[one_index] = target
            else:
                # Check whether one_index is already in targets dict
                try:
                    target = targets[one_index]
                except KeyError:
                    target = one_index
                    
                actions = patterns[target][1]
                try:
                    index = action_patterns.index(actions)
                    freq_patterns[index] = freq_patterns[index] + patterns[i][0]
                    
                except ValueError:
                    action_patterns.append(actions)
                    freq_patterns.append(patterns[i][0] + patterns[target][0])
                    
                    
                to_fuse[one_index][i] = 2 # Don't fuse again, but don't be zero either
                targets[i] = target
        elif one == 0:
            # this pattern doesn't have to be fused, but append it
            action_patterns.append(patterns[i][1])
            freq_patterns.append(patterns[i][0])
    
    # action_patterns and freq_patterns have to aligned index-wise
    # build fused_patterns combining both
    for i in xrange(len(action_patterns)):
        fused_patterns.append([freq_patterns[i], action_patterns[i]])
                
    
    print '  Fused patterns:'
    for i in xrange(len(fused_patterns)):
        print '  ', fused_patterns[i][0], fused_patterns[i][1]
        
    return fused_patterns


"""
Function to obtain up and down triangle of a square matrix
Input:
    m: input square matrix (np.array)
Output:
    up_triangle: list of values in the up triangle
    down_triangle: list of values in the down triangle
"""
def obtainBothTriangles(m):
    # Make sure matrix is square
    if m.shape[0] != m.shape[1]:
        exit('obtainBothTriangles: matrix is not square')
    
    up_triangle = []
    i = 0        
    while i < len(m):
        j = i + 1
        while j < len(m):                
            up_triangle.append(m[i][j])
            j = j + 1
                    
        i = i + 1

    # Obtain the lower triangle of the jf_matrix
    i = 1
    down_triangle = []
    while i < len(m):
        j = 0
        while j < i:
            down_triangle.append(m[i][j])
            j = j + 1
                    
        i = i + 1
    
    return up_triangle, down_triangle

"""
Function to detect outliers based on leave one-out method
Input:
    patterns: list of lists ([[m, [action,..., action]], [n, [action,..., action]]])
    occurrences: total occurrences of the activity
Output:
    new_patterns: the same format, but fusing fusable patterns    
"""
def leaveOneOut(patterns, occurrences):
    new_patterns = deepcopy(patterns)
    for i in xrange(len(new_patterns)):
        new_patterns[i][0] = float(new_patterns[i][0]) / float(occurrences)
    
    end_loop = False
    while not end_loop:
        if len(new_patterns) <= 2:
            end_loop = True
        else:
            # Calculate JF matrix for patterns
            jf_matrix = np.zeros((len(new_patterns), len(new_patterns)))
            for i in xrange(len(jf_matrix)):
                for j in xrange(len(jf_matrix)):                    
                    jf_matrix[i][j] = jaccard(new_patterns[i][1], new_patterns[j][1]) / new_patterns[i][0]
            
            np.fill_diagonal(jf_matrix, 0)
            # print JF matrix for debugging
            print '  JF matrix:'
            print jf_matrix
            # Take the maximum number of each row
            max_values = []
            for i in xrange(len(jf_matrix)):
                col = jf_matrix[i].tolist().index(max(jf_matrix[i]))
                max_values.append(max(jf_matrix[i]))
            # Leave max out
            out_index = max_values.index(max(max_values))
            out_value = max(max_values)
            # Calculate threshold as a sum of mean and std for max_values, 
            # after removing out_value
            max_values.remove(out_value)
            fusing_threshold = np.mean(max_values) + 5 * np.std(max_values)
            # Check threshold with max_value
            if out_value > fusing_threshold:
                print '  Fuse', out_index, 'with', col
                new_patterns[col][0] = new_patterns[col][0] + new_patterns[out_index][0]
                new_patterns.remove(new_patterns[out_index])
                print '  New patterns:'
                for i in xrange(len(new_patterns)):
                    print '  ', new_patterns[i][0], new_patterns[i][1]
            else:
                end_loop = True
            
    return new_patterns
       
"""
Main function
"""

def main(argv):
    # call the argument parser
    [summary_file, dataset_file, context_file, patterns_file] = parseArgs(argv[1:])
    
    # Read the dataset_file and build a DataFrame 
    df = pd.read_csv(dataset_file, parse_dates=0, index_col=0)
    
    # Read and parse the summary_file
    learnt_activities = json.loads(open(summary_file).read())
    
    # For debugging purposes, visualize learnt_activities
    #visualizeLearntActivities(learnt_activities)
    
    # Calculate definitive pattern for every activity
    learnt_patterns = calculateDefinitiveActionPatterns(learnt_activities)
    
    print '------------------------------'
    print '------------------------------'
    print 'Learnt patterns for each activity:'
    for key in learnt_patterns:
        print 'Activity', key
        print '  Criterion 1:'
        patterns = learnt_patterns[key]['criterion1']
        for i in xrange(len(patterns)):
            print '    ', patterns[i][0], patterns[i][1]
        """
        print '  Criterion 2:'
        patterns = learnt_patterns[key]['criterion2']
        for i in xrange(len(patterns)):
            print '    ', patterns[i][0], patterns[i][1]
           """ 
    # Write learnt_patterns to patterns_file
    # Write the json file sumarry_file
    with open(patterns_file, 'w') as outfile:
       json.dump(learnt_patterns, outfile, indent=4)
   
if __name__ == "__main__":   
    main(sys.argv)