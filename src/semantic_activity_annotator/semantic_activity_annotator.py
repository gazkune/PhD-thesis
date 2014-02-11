# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 09:14:23 2014

@author: gazkune
"""

"""
This tool is to annotate activities from a dataset
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
    dataset_file -> csv file where action properties are with time stamps and activity label
    seed_file -> file where seed activity models are defined (special format)
    output_file -> file to write the identified activities in dataset_file using 
        seed activity models defined at seed_file as templates
"""

def parseArgs(argv):
   dataset_file = ''
   seed_file = ''
   output_file = ''
   try:
      opts, args = getopt.getopt(argv,"hd:s:o:",["dataset=","seed=","ofile="])      
   except getopt.GetoptError:
      print 'semantic_activity_annotator.py -d <dataset> -s <seed> -o <outputfile>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'semantic_activity_annotator.py -d <dataset> -s <seed> -o <outputfile>'
         sys.exit()
      elif opt in ("-d", "--dataset"):
         dataset_file = arg
      elif opt in ("-s", "--seed"):
         seed_file = arg
      elif opt in ("-o", "--ofile"):
         output_file = arg
   
   return dataset_file, seed_file, output_file
   
"""
Function to parse seed activity models in the specified file (special format)
Input:
    seed_file: the name of the file where seed activity models are defined
Output:
    seed_activities: a list of seed activity models
"""

def parseSeedActivityModels(seed_file):
    seed_activities = []
    
    seed_file = open(seed_file, 'r')
    
    not_eof = True
    line_number = 1
    while not_eof:
        line = seed_file.readline().strip('\n')
        if not line: 
            # EOF
            not_eof = False
        else:
            # Line structure:
            # Activity_name max_duration: action_prop1 action_prop2 ... action_propN
            seed = line.split(': ')
            # Check whether line is well formed
            if len(seed) != 2:
                msg = 'Bad formed line (' + str(line_number) + '): expected <Activity_name max_duration: action_prop1 action_prop2 ... action_propN>, but read: ' + str(line)
                sys.exit(msg)
                
            # Separate elements in seed to form a list [activity_name, [action_prop1, ...]]
            action_props = seed[1].split(' ')
            name = seed[0].split(' ')[0]
            try:
                duration = int(seed[0].split(' ')[1])
            except ValueError:
                sys.exit('Maximum duration expected after activity name, before :')
            
            seed_activities.append([name, duration, action_props])
            line_number = line_number + 1
            
    
    return seed_activities

"""
Function to check whether a list of actions is complete respect to a seed activity definition
"""
def completeActivity(activity_start, activity_end, activity, activity_df, seed_activities):
    actions = activity_df.iloc[activity_start:activity_end+1, 0].values
    for i in xrange(len(seed_activities)):
        if seed_activities[i][0] == activity:
            seed_actions = np.array(seed_activities[i][2]) # 0 element: name, 1 element: duration
            
    inter = np.intersect1d(actions, seed_actions)
    if len(inter) == len(seed_actions):
        return True
    else:
        return False
"""
Function to check whether activity duration is less than max_duration, specified in seed
activity models
Input:
    activity_start: starting index for the activity in activity_df (int)
    activity_end: end index for the activity in activity_df (int)
    activity: name of the activity (string)
    activity_df: the list of timestamped actions (pd.DataFrame)
    seed_activities: a list where all seed activities are defined
Output:
    True/False: True if activity duration is less than max_duration; False elsewhere
"""
def rightActivityDuration(activity_start, activity_end, activity, activity_df, seed_activities):
    duration = activity_df.index[activity_end] - activity_df.index[activity_start]    
    max_duration = datetime.timedelta(seconds=0)
    for j in xrange(len(seed_activities)):
        try:
            seed_activities[j].index(activity)
        except ValueError:
            continue
        max_duration = datetime.timedelta(seconds=seed_activities[j][1])
        break
    
    if duration < max_duration:
        return True
    else:
        return False


"""
Function that annotates the dataset contained in activity_df, using seed activity models
defined in seed_activities as templates
Input:
    activity_df: a dataset where timestamped action properties are (pd.DataFrame)
    seed_activities: seed activity models (list of list)
Output:
    annotated_activities: [[Activity, Completed, StartIndex, EndIndex], [Activity, Completed, StartIndex, EndIndex], ...]
    Completed is a boolean that indicates if the detected activity has been completed
    considering seed activity models
"""

"""
2 approaches:
    1) Iterate through all action contained in activity_df. When an action is contained in a
    seed activity (one or more), start new activity (store index). Keep on iterating until completing
    the seed activity. If activity is not completed, but an action appears that is contained in another
    activity, start a new activity and finish the last one. If the incomplete activity was not defined
    (actions contained in more than one activity), do not assign any activity
    2) Find unique actions, which are the actions that are only contained by one seed activity. 
    Store the indexes of those unique actions and expand them (left, right) until completing the seed activity model        
"""
def annotateActivities1(activity_df, seed_activities):
    # Implements approach 1
    print 'annotateActivities approach 1'  
    #activity_start = False
    activity_start = 0
    activity_end = 0    
    current_activity = np.array([])
    # annotated_activities has the following structure
    # [[Activity, Completed, StartIndex, EndIndex], [Activity, Completed, StartIndex, EndIndex], ...]
    annotated_activities = []
    for i in xrange(len(activity_df)):        
        # <i> can be used to index the row
        action = activity_df.iloc[i, 0] # actions are in column 0 always        
        
        # Iterate through seed_activities and check whether action
        # is contained in any of the activities
        activities = actionInSeedActivities(action, seed_activities)
        
        # To use intersection functions, use np.array
        activities = np.array(activities)
            
        # activities is a list of seed activity names where action
        # is contained
        # Print for debugging purposes                    
        #print 'Action:', action, 'Activities:', activities
        if len(activities) == 0:
            print 'Iteration:', i 
            print '   current_activities:', current_activity
            print '   activities:', activities
            continue        
        
        if len(current_activity) == 0 and len(activities) > 0:
            print 'Iteration:', i
            print '   current_activity:', current_activity
            print '   activities:', activities
            activity_start = i
            current_activity = activities
            continue
            
        if len(current_activity) > 0 and len(activities) > 0:
            # Check time from last action to this one and see if it is coherent with the activies
            # in current_activity
            print 'Iteration:', i
            print '   current_activity:', current_activity
            print '   activities:', activities
            aux_activities = []
            for j in xrange(len(current_activity)):
                if rightActivityDuration(i-1, i, current_activity[j], activity_df, seed_activities):
                    print '   Keep activity'
                    aux_activities.append(current_activity[j])
            
            current_activity = np.array(aux_activities)
            if len(current_activity) == 0:
                activity_start = i
                current_activity = activities
            
            # We have to play with activities and current_activity
            inter = np.intersect1d(activities, current_activity)
            # inter is the intersection between both arrays
            if len(inter) == 0:
                # empty intersection
                """
                This case should be treated carefully, specially if we consider noisy scenarios
                If we have positive noise (sensor activations that should not occur):
                    Using the completion criterion we can prevent positive noise, e.g.
                    if the activity is not completed, do not annotate and start a new activity
                If we have negative noise (missing sensor activations):
                    Completion criterion could make us not annotate activities that really occurred
                    but with a missing activation
                """
                aux_0 = list(activities)
                aux_1 = list(current_activity)
                for j in xrange(len(aux_0)):
                    aux_1.append(aux_0[j])
                    
                current_activity = np.array(aux_1)
                print 'Empty intersection:', current_activity
                """
                if len(current_activity) == 1:
                    # End current activity
                    # Is this the best policy? Should we end an activity even if it has not been
                    # completed?
                    activity_end = i - 1
                    annotated_activities.append([current_activity[0], False, activity_start, activity_end])
                # start a new activity
                current_activity = activities
                activity_start = i
                """
                continue
            else:
                # intersection is not empty
                current_activity = inter
                if len(inter) == 1:
                    # Activity has been clearly detected
                    # Check whether activity has been completed
                    if completeActivity(activity_start, i, current_activity[0], activity_df, seed_activities):
                        # End current activity
                        activity_end = i
                        # Check duration
                        if rightActivityDuration(activity_start, i, current_activity[0], activity_df, seed_activities):
                            annotated_activities.append([current_activity[0], True, activity_start, activity_end])
                            current_activity = np.array([])                        
                    else:
                        continue          
            
    # Print annotated_activities for debugging purposes
    print 'Annotated activities after first pass:'
    for i in xrange(len(annotated_activities)):
        print annotated_activities[i]
    
    # After first pass through the dataset, we have the annotated activities with 
    # completed and non-completed activities; now we have to check the non-completed ones
    # with duration information and successive actions
    for i in xrange(len(annotated_activities)):
        # Take the first non-completed activity
        if annotated_activities[i][1] == False:
            start_index = annotated_activities[i][2]
            activity = annotated_activities[i][0]
            # Search for the closest completed activity
            found = False
            increment = 0
            while not found:
                if annotated_activities[i + increment][2] == False:
                    increment = increment + 1
                else:
                    found = True
                    
            # i + increment is the index of the closest complete activity
            end_index = i + increment
            # Iterate through activity_df using start_index and end_index and find if there is
            # an action that completes current non-completed action and respects the maximum
            # duration criterion
            exit_loop = False
            increment = 0
            completed = False
            while not exit_loop:
                if completeActivity(start_index, start_index + increment, activity, activity_df, seed_activities):
                    completed = True
                    comp_index = start_index + increment
                    exit_loop = True
                else:
                    increment = increment + 1
                    if start_index + increment == end_index:
                        exit_loop = True
            # if completed is True, we found actions that completed the activity -> 
            # check time constraints
            if completed == True:                
                if rightActivityDuration(start_index, comp_index, activity, activity_df, seed_activities):
                    # Complete and legal activity
                    annotated_activities[i][1] = True
                    annotated_activities[i][3] = comp_index
                    print 'A new completed activity has been discovered!:'
                    print annotated_activities[i]
    
    # Activities that were not completed in the first pass, will remain incomplete,
    # but activities that have been completed in the secon pass, should appear as completed now
    # print complete annotated_activities (True) for debugging purposes
    # First tests suggest that if we do not have missing values, complete annotated_activities
    # capture all the activities correctly
    
    print 'Annotated activities after second pass:'
    for i in xrange(len(annotated_activities)):
        if annotated_activities[i][1] == True:
            print annotated_activities[i]

    return annotated_activities            
            
       
       
def annotateActivities2(activity_df, seed_activities):
    # Implements approach 2
    print 'annotateActivities approach 2'
    
    # annotated_activities has the following structure
    # [[Activity, Completed, StartIndex, EndIndex], [Activity, Completed, StartIndex, EndIndex], ...]
    annotated_activities = []
    
    i = 0
    while i < len(activity_df):
        # <i> can be used to index the row
        action = activity_df.iloc[i, 0] # actions are in column 0 always        
        
        # Iterate through seed_activities and check whether action
        # is contained in any of the activities
        activities = actionInSeedActivities(action, seed_activities)
        
        # To use intersection functions, use np.array
        activities = np.array(activities)
        
        if len(activities) == 0:
            i = i + 1
            continue        
        
        # Activity start index
        start_index = i
        
        for j in xrange(len(activities)):
            activity = activities[j]
            incr = 1
            # Use two booleans to handle activity recognition
            activity_detected = False
            time_out = False        
            while not activity_detected and not time_out and (start_index + incr) < len(activity_df):
                if not rightActivityDuration(start_index, start_index + incr, activity, activity_df, seed_activities):
                    time_out = True
                else:
                    if completeActivity(start_index, start_index + incr, activity, activity_df, seed_activities):
                        activity_detected = True
                        end_index = start_index + incr
                        detected_activity = activity
                incr = incr + 1
            if activity_detected == True:
                annotated_activities.append([detected_activity, True, start_index, end_index])
                i = end_index
                break
        
        i = i + 1
        
    # annotated_activities contain all the activities detected (completed always True)
    print 'Annotated activities:'
    for i in xrange(len(annotated_activities)):
        print annotated_activities[i]
        
    return annotated_activities            
       
       
"""
Function that returns the list of activities which contain action
Input:
    action: the action name (string)
    seed_activities: seed activity definitions (list of lists)
Output:
    activities: a list of activity names (list of strings)    
"""
                  
def actionInSeedActivities(action, seed_activities):
    
    activities = []
    for j in xrange(len(seed_activities)):
        try:
            seed_activities[j][2].index(action)
        except ValueError:
            continue
        activities.append(seed_activities[j][0])

    return activities
        
"""
Main function
"""

if __name__ == "__main__":   
   
   # call the argument parser 
   [dataset_file, seed_file, output_file] = parseArgs(sys.argv[1:])
   print 'Dataset:', dataset_file
   print 'Seed activity models:', seed_file
   print 'Annotated actions:', output_file
   
   # Read the dataset_file and build a DataFrame 
   activity_df = pd.read_csv(dataset_file, parse_dates=0, header=None, index_col=0)
   
   # Rename columns
   activity_df = activity_df.rename(columns={1: 'action', 2: 'real_label', 3: 'start_end'})
   
   
   # Parse the seed_file file
   seed_activities = parseSeedActivityModels(seed_file)
   print 'Seed activity models:'
   print seed_activities
   
   # Call annotateActivities function
   annotated_activities = annotateActivities2(activity_df, seed_activities)
   
      
   # Use only complete activities to create the annotated pd.DataFrame
   # Each row will be: [timestamp, action, real_label, annotated_label]
   aux_list = []
   for i in xrange(len(activity_df)):
       aux_list.append('None')
  
   
   # Iterate through annotated_activities and choose only those that are complete (True)
   # to modify annotated_labels
   for i in xrange(len(annotated_activities)):
       if annotated_activities[i][1] == True:
           # Complete activity
           start = annotated_activities[i][2]
           end = annotated_activities[i][3]
           for j in xrange(start, end + 1):
               aux_list[j] = annotated_activities[i][0]
   
   annotated_labels = pd.DataFrame(aux_list, index=activity_df.index)
   activity_df['annotated_label'] = annotated_labels
   
   print 'To store in a csv file:'
   print activity_df.head(50)
   
   activity_df.to_csv(output_file)
   
   
       