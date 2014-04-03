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
import json

"""
Function to parse arguments from command line. If context_model is provided, there is no
need for seed_activity_models
Input:
    argv -> command line arguments
Output:
    dataset_file -> csv file where action properties are with time stamps and activity label
    context_model -> json file where sensors, objects and activities are described
    seed_file -> file where seed activity models are defined (special format)
    output_file -> file to write the identified activities in dataset_file using 
        seed activity models defined at seed_file as templates
"""

def parseArgs(argv):
   dataset_file = ''
   context_file = ''
   seed_file = ''
   output_file = ''
   try:
      opts, args = getopt.getopt(argv,"hd:c:s:o:",["dataset=","context=","seed=","ofile="])      
   except getopt.GetoptError:
      print 'semantic_activity_annotator.py -d <dataset> -c <context_model> -s <seed> -o <outputfile>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'semantic_activity_annotator.py -d <dataset> -c <context_model> -s <seed> -o <outputfile>'
         sys.exit()
      elif opt in ("-d", "--dataset"):
         dataset_file = arg
      elif opt in ("-c", "--context"):
         context_file = arg
      elif opt in ("-s", "--seed"):                      
         seed_file = arg         
      elif opt in ("-o", "--ofile"):
         output_file = arg
   
   if context_file != '' and seed_file != '':
       print 'WARNING: as context file has been provided, seed activity file will not be taken into account'
   return dataset_file, context_file, seed_file, output_file
   
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
function to build seed activity models, exactly as function parseSeedActivityModels does, 
but from the context_model dictionary read from the json file
Input:
    context_model: a dict where activities, objects and sensors are decribed (extracted
    from a json file)
Output:
    seed_activites: a list of seed activity models
"""
def buildSeedActivityModelsFromContext(context_model):
    activities = context_model["activities"]
    seed_activities = []
    for name in activities:        
        duration = activities[name]["duration"]
        actions = activities[name]["min_model"]
        seed_activities.append([name, duration, actions])
        
    return seed_activities
        

"""
Function to check whether a list of actions is complete respect to a seed activity definition
New criterion: check whether the actions pertaining to seed activity models occur in the same
location and that location is consistent with the location information from the activity
Input:
    activity_start: index for sensor-action that starts the activity sequence (int)
    activity_end: index for sensor-action that ends the activity sequence (int)
    activity: name of the activity (string)
    activity_df: pd.DataFrame where sensor-actions and respective activities are
    seed_activities: a list of lists that describes the seed activity models
    context_model: a dict where activities, objects and sensors are decribed (extracted
Output:
    True/False: True if the action sequence descibes an activity / False otherwise
"""
def completeActivity(activity_start, activity_end, activity, activity_df, seed_activities, context_model):
    action_col = activity_df.columns.tolist().index('action')
    actions = activity_df.iloc[activity_start:activity_end+1, action_col].values
    for i in xrange(len(seed_activities)):
        if seed_activities[i][0] == activity:
            seed_actions = np.array(seed_activities[i][2]) # 0 element: name, 1 element: duration
            
    inter = np.intersect1d(actions, seed_actions)
    # Check location consistence
    objects = context_model['objects']
    sensors = context_model['sensors']
    activities = context_model['activities']
    alocations = activities[activity]['location']
    olocations = []
    for i in xrange(len(seed_actions)):        
        j = activity_start
        end_loop = False
        while not end_loop and j <= activity_end:
            sensor_col = activity_df.columns.tolist().index('sensor')
            sensor = activity_df.iloc[j, sensor_col]
            if sensors[sensor]['action'] == seed_actions[i]:
                olocation = objects[sensors[sensor]['attached-to']]['location']
                try:
                    alocations.index(olocation)
                    if olocations != []:
                        if olocations[0] == olocation:
                            olocations.append(olocation)
                            end_loop = True
                        else:
                            j = j + 1
                    else:
                        olocations.append(olocation)
                        end_loop = True
                    
                except ValueError:
                    j = j + 1
            else:
                j = j + 1
                    
    if len(inter) == len(seed_actions) and len(olocations) == len(seed_actions):
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
Function to annotate actions with activities, from seed_activity_models
Input:
    activity_df: pd.DataFrame with sensors, actions and activities (real label)
    seed_activities: list of seed models for activities [Activity, Duration [action0, action1...]]
    context_model: dict where activities, sensors and objects are described
Output:
    annotated_activities: a list of annotated activities which the following structure
    [[Activity, Completed, StartIndex, EndIndex], [Activity, Completed, StartIndex, EndIndex], ...]
"""
       
def annotateActivities(activity_df, seed_activities, context_model):
    # Implements approach 2
    print 'annotateActivities approach 2'
    
    # annotated_activities has the following structure
    # [[Activity, Completed, StartIndex, EndIndex], [Activity, Completed, StartIndex, EndIndex], ...]
    annotated_activities = []
    
    i = 0
    while i < len(activity_df):
        # <i> can be used to index the row
        # Discover where actions are
        cols = activity_df.columns.tolist()
        action_col = cols.index('action')
        action = activity_df.iloc[i, action_col] # actions are in column 0 always        
        
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
        aux_list = []
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
                    if completeActivity(start_index, start_index + incr, activity, activity_df, seed_activities, context_model):
                        activity_detected = True
                        end_index = start_index + incr
                        detected_activity = activity
                incr = incr + 1
            if activity_detected == True:
                #annotated_activities.append([detected_activity, True, start_index, end_index])
                aux_list.append([detected_activity, True, start_index, end_index])
                #i = end_index
                #break
                
        # aux_list will contain all the activities detected from current action
        # take the shortest activity
        if len(aux_list) > 0:
            max_length = len(activity_df)
            for j in xrange(len(aux_list)):
                activity_length = aux_list[j][3] - aux_list[j][2]
                if activity_length < max_length:
                    max_length = activity_length
                    selected_activity = aux_list[j]
        
            annotated_activities.append(selected_activity)
            # Update i to start with the action that follows the end of selected activity
            i = selected_activity[3] + 1
        else:
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
Function to obtain a list of actions from activity_df sensors and context_model
sensor -> action transformations are defined in context_model
Input:
    activity_df: pd.DataFrame with time-stamped sensor activations
    context_model: dict where activities, sensors and objects are described
Output:
    actions: a list of actions
"""
def obtainActions(activity_df, context_model):
    sensors = context_model["sensors"]    
    actions = []
    for i in activity_df.index:        
        name_sensor = activity_df.loc[i, "sensor"]        
        try:
            action = sensors[name_sensor]["action"]
        except KeyError:
            msg = 'obtainActions: ' + name_sensor + ' sensor is not in the context_model; please have a look at provided dataset and context model'
            exit(msg)
        actions.append(action)
    
    return actions
        
"""
Main function
"""

def main(argv):
   # call the argument parser 
   [dataset_file, context_file, seed_file, output_file] = parseArgs(argv[1:])
   print 'Dataset:', dataset_file
   print 'Context model:', context_file
   print 'Seed activity models:', seed_file
   print 'Annotated actions:', output_file
   
   # Read the dataset_file and build a DataFrame 
   activity_df = pd.read_csv(dataset_file, parse_dates=0, index_col=0)
        
   # Build seed_activity models
   if context_file != '':
       context_model = json.loads(open(context_file).read())
       seed_activities = buildSeedActivityModelsFromContext(context_model)       
   else:
       # Parse the seed_file file
       seed_activities = parseSeedActivityModels(seed_file)
   print 'Seed activity models:'
   print seed_activities   
   
   # Add a new column to activity_df for actions
   # actions are obtained transforming sensors to actions, as indicated in
   # context_model
   action_column = obtainActions(activity_df, context_model)
   print 'Obtained actions:'
   print action_column
   action_df = pd.DataFrame(action_column, index=activity_df.index)
   activity_df['action'] = action_df   
   # Re-order columns to have [time_stamp, sensor, action, activity, start_end]
   cols = activity_df.columns.tolist()   
   cols = [cols[0]] + cols[-1:] + cols[1:-1]   
   activity_df = activity_df[cols]   
   
   # Call annotateActivities function
   annotated_activities = annotateActivities(activity_df, seed_activities, context_model)   
      
   # Use only complete activities to create the annotated pd.DataFrame
   # Each row will be: [timestamp, action, real_label, r_start_end, annotated_label, a_start_end]
   aux_list = []
   se_list = []
   for i in xrange(len(activity_df)):
       aux_list.append('None')
       se_list.append('')  
   
   # Iterate through annotated_activities and choose only those that are complete (True)
   # to modify annotated_labels
   for i in xrange(len(annotated_activities)):
       if annotated_activities[i][1] == True:
           # Complete activity
           start = annotated_activities[i][2]
           end = annotated_activities[i][3]
           se_list[start] = 'start'
           se_list[end] = 'end'
           for j in xrange(start, end + 1):
               aux_list[j] = annotated_activities[i][0]
   
   annotated_labels = pd.DataFrame(aux_list, index=activity_df.index)
   annotated_se = pd.DataFrame(se_list, index=activity_df.index)
   activity_df['annotated_label'] = annotated_labels
   activity_df['a_start_end'] = annotated_se
   
   print 'To store in a csv file:'
   print activity_df.head(50)   
   activity_df.to_csv(output_file)    


if __name__ == "__main__":   
    main(sys.argv)