# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 09:50:49 2014

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

"""
Function to parse arguments from command line
Input:
    argv -> command line arguments
Output:
    annotated_file -> csv file obtained from semantic_activity_annotator
    [timestamp, sensor, action, activity, start_end, annotated_label, a_start_end]
    context_file -> file where activities, objects and sensors are described (json format)
    raw_data_file -> csv file where results will be provided
    [timestamp, sensor, action, activity, start_end]
    summary_file -> json file where final result summary will be provided
    {activity_name: format to be decided!}
"""

def parseArgs(argv):
   annotated_file = ''
   context_file = ''   
   raw_data_file = ''
   summary_file = ''
   try:
      opts, args = getopt.getopt(argv,"ha:c:r:s:",["annotated=","context=","raw=","summary="])      
   except getopt.GetoptError:
      print 'activity_clustering.py -a <annotated_actions> -c <context_model> -r <raw_data_file> -s <summary_file>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'activity_clustering.py -a <annotated_actions> -c <context_model> -r <raw_data_file> -s <summary_file>'
         sys.exit()
      elif opt in ("-a", "--annotated"):
         annotated_file = arg      
      elif opt in ("-c", "--context"):
         context_file = arg
      elif opt in ("-r", "--raw"):
         raw_data_file = arg
      elif opt in ("-s", "--summary"):         
         summary_file = arg      
   
   return annotated_file, context_file, raw_data_file, summary_file
   
"""
Function to parse context_file, a json file where activities, sensors and objects
are described in terms of type and location
Input:
    context_file -> file where activities, objects and sensors are described (json format)
Output:
    activities -> dict of activities with their properties
    objects -> dict with objects with their properties
    sensors -> dict with sensors with their properties
"""

def parseDescription(context_file):
    description = json.loads(open(context_file).read())
    
    activities = description['activities']
    objects = description['objects']
    sensors = description['sensors']
    
    return activities, objects, sensors

"""
Function to check whether the location of a sensor-object is compatible with the locations
of an activity
Input:
    activity: name of the activity (string)
    sensor: name of the sensor (string)
    objects: dict of objects
    sensors: dict of sensors
    activities: dict of activities
Output:
    True/False
"""
def checkLocationCompatibility(activity, sensor, objects, sensors, activities):
    olocation = objects[sensors[sensor]['attached-to']]['location'] # string
    alocation = activities[activity]['location'] # list of strings
    try:
        alocation.index(olocation)
        return True
    except ValueError:
        return False

"""
Function to check whether the types of a sensor-object are compatible with the types
of an activity
Input:
    activity: name of the activity (string)
    sensor: name of the sensor (string)
    objects: dict of objects
    sensors: dict of sensors
    activities: dict of activities
Output:
    True/False
"""
def checkTypeCompatibility(activity, sensor, objects, sensors, activities):
    otype = np.array(objects[sensors[sensor]['attached-to']]['type'])
    atype = np.array(activities[activity]['type'])
    # Use np.array to compute intersection
    inter = np.intersect1d(otype, atype)
    if len(inter) == 0:
        return False
    else:
        return True


"""
Function to filter insider sensor-actions. Two criterions are used for this filtering
1) Check whether the action is in the minimal model of that activity
2) If not, check whether the sensor-action type and location are compatible with
that activity
Input:
    annotated_df: pd.DataFrame where at least the following info is required
    [timestamp, sensor, action, annotated_label, a_start_end]
    activities: dict with activity info obtained from context_model
    objects: dict with object info obtained from context_model
    sensors: dict with sensor info obtained from context_model
Output:
    filtered_df: pd.DataFrame where insiders have been filtered, but outsiders are still present
    to filter, a new column 'filter' has been added to filtered_df
"""
def filterInsiders(annotated_df, activities, objects, sensors):
    aux_df = annotated_df[annotated_df['annotated_label'] != 'None']
    
    filtered_df = annotated_df
    filtered_df['filter'] = pd.DataFrame(['No']*len(annotated_df), index = annotated_df.index)
    
    for index in aux_df.index:
        sensor = aux_df.loc[index, 'sensor']
        action = aux_df.loc[index, 'action']
        # filter sensor-action if one of 2 criteria doesn't apply
        # check whether action is in the minimal model
        annotated_activity = aux_df.loc[index, 'annotated_label']
        min_model = activities[annotated_activity]['min_model']
        try:
            min_model.index(action)
        except ValueError:
            # Action is not in minimal model
            # Check location and type
            loc = checkLocationCompatibility(annotated_activity, sensor, objects, sensors, activities)    
            typ = checkTypeCompatibility(annotated_activity, sensor, objects, sensors, activities)
            if typ == False or loc == False:
                # Filter sensor-action from filtered_df
                filtered_df.loc[index, 'filter'] = 'Yes'
            
    return filtered_df

"""
Function to compute outsider sensor-actions. As single user - single activity
is assumed, it has to be decided whether those
sensor-actions pertain to the previous activity, the next activity or none.
Three parameters will be used to compute it:
1) Time (not clear yet how to handle this)
2) Location (location compatibility between activity and sensor-action)
3) Type (type compatibility between activity and sensor-action)
Input:
    filtered_df: pd.DataFrame where at least the following info is required
    [timestamp, sensor, action, annotated_label, a_start_end, filter]
    activities: dict with activity info obtained from context_model
    objects: dict with object info obtained from context_model
    sensors: dict with sensor info obtained from context_model
Output:
    resulting_df: pd.DataFrame where the following info is provided
    [timestamp, sensor, action, annotated_label, a_start_end, filter, assign]
    where 'assign' column refers to the final activity of the sensor-action
"""
def computeOutsiders(filtered_df, activities, objects, sensors):
    # store outsider sensor-actions
    outsiders_df = filtered_df[filtered_df['annotated_label'] == 'None']
    # store [timestamp, annotated_label, a_start_end] for all activities
    # that have been detected
    activity_df = filtered_df[np.logical_or(filtered_df['a_start_end'] == 'start', filtered_df['a_start_end'] == 'end')]
    activity_df = activity_df[['annotated_label', 'a_start_end']] 
    # Generate the last column 'assign'
    assign = ['None']*len(filtered_df)
    assign_col = pd.DataFrame(assign, index=filtered_df.index)
    filtered_df['assign'] = assign_col
    for index in filtered_df.index:
        if filtered_df.loc[index, 'annotated_label'] != 'None' and filtered_df.loc[index, 'filter'] != 'Yes':            
            filtered_df.loc[index, 'assign'] = filtered_df.loc[index, 'annotated_label']
    
    # Print for debugging purposes
    #print 'computeOutsiders: filtered_df'
    #print filtered_df.head(50)
    # For each action-sensor find its previous and next activity
    previous_activity = {}
    next_activity = {}
    last_j = 0
    #count_outsiders = 0
    for i in outsiders_df.index:
        # Use next_j to store where we start iterating for activities
        j = last_j
        while j < len(activity_df):
            # Update j = j + 2, since two blocks form one activity (start, end)
            # Special case: j + 2 == len(activity_df) (last activity) and
            # sensor-action is before that activity -> there is no next_activity
            if j + 2 == len(activity_df) and i > activity_df.index[j+1]:
                previous_activity = {'name' : activity_df.loc[activity_df.index[j], 
                                                          'annotated_label'],
                                     'start_time' : activity_df.index[j], 
                                     'end_time' : activity_df.index[j+1]}
                next_activity = {}
                # Update last_j
                last_j = j
                break
            if i < activity_df.index[j]:                
                if j == 0:
                    previous_activity = {}
                    next_activity = {'name' : activity_df.loc[activity_df.index[j], 
                                                          'annotated_label'], 
                                     'start_time' : activity_df.index[j], 
                                     'end_time' : activity_df.index[j+1]}
                if j > last_j:
                    previous_activity = {'name' : activity_df.loc[activity_df.index[j-1],
                                                                  'annotated_label'],
                                        'start_time' : activity_df.index[j-2],
                                        'end_time' : activity_df.index[j-1]}
                    next_activity = {'name' : activity_df.loc[activity_df.index[j], 
                                                          'annotated_label'], 
                                     'start_time' : activity_df.index[j], 
                                     'end_time' : activity_df.index[j+1]}
                # Update last_j
                last_j = j
                break
            # Update j
            j = j + 2
        
        # sensor-action is between previous and next activities
        #print i, 'sensor-action', outsiders_df.loc[i, 'sensor']
        #print '   previous:', previous_activity
        #print '   next:', next_activity
        # Use location, type and time information to decide whether sensor-action
        # should be included in the annotated_label
        sensor = outsiders_df.loc[i, 'sensor']        
        # Check location and type compatibility with previous activity (if it exists)        
        # TODO: for location compatibility: even though an activity may be perfomed
        # in several locations, it would be nice to infer from data where it has
        # been actually performed and use that location for location compatibility
        if previous_activity != {}:
            activity = previous_activity['name']
            p_loc_ok = checkLocationCompatibility(activity, sensor, objects, sensors, activities) == True
            p_type_ok = checkTypeCompatibility(activity, sensor, objects, sensors, activities) == True 
            # Check time (Gaussian criterion)
            [p_in_range, p_delta_centre, p_delta_closest] = timeManagement(i, previous_activity, True, activities)
        else:
            p_loc_ok = False
            p_type_ok = False
        # Check location and type compatibility with previous activity (if it exists)    
        if next_activity != {}:
            activity = next_activity['name']
            n_loc_ok = checkLocationCompatibility(activity, sensor, objects, sensors, activities) == True
            n_type_ok = checkTypeCompatibility(activity, sensor, objects, sensors, activities) == True 
            # Check time (Gaussian criterion)
            [n_in_range, n_delta_centre, n_delta_closest] = timeManagement(i, next_activity, False, activities)
        else:
            n_loc_ok = False
            n_type_ok = False
            
        print 'Sensor:', sensor, 't:', i    
        if p_loc_ok == True and p_type_ok == True:      
            print '   previous:', previous_activity['name']
            print '   start:', previous_activity['start_time'], ', end:', previous_activity['end_time']
            print '   in_range:', p_in_range
            print '   delta_centre:', p_delta_centre.seconds
            print '   delta_closest:', p_delta_closest.seconds
        else:
            if previous_activity != {}:
                print '   not compatible with previous activity', previous_activity['name']
            else:
                print '   there is no previous activity'
        if n_loc_ok == True and n_type_ok == True:      
            print '   next:', next_activity['name']
            print '   start:', next_activity['start_time'], ', end:', next_activity['end_time']
            print '   in_range:', n_in_range
            print '   delta_centre:', n_delta_centre.seconds
            print '   delta_closest:', n_delta_closest.seconds
        else:
            if next_activity != {}:
                print '   not compatible with next activity', next_activity['name']
            else:
                print '   there is no next activity'
                
        # TODO: decide how to handle time distance in case an action is in range 
        # with previous and next. Issues:
        # 1) Consider time distance relative to expected duration (time/duration)
        # 2) Consider the portion of duration covered by previous and next activities
            
"""
Function to manage time issues between a sensor-action and an activity
Criterion: Gaussian criterion
Input:
    sensor_timestamp: timestamp of the sensor-action (pd.tslib.Timestamp)
    activity: a dict describing an activity {'name', 'start_time', 'end_time'}
    where start_time and end_time are pd.tslib.Timestamp
    previous: boolean that indicates whether activity is before sensor-action
    activities: dict with activity description from context_model
Output:
    in_range: True if sensor_timestamp is inside 2*sigma (from start_time, end_time)
    delta_centre: time distance between sensor-action and activity centre
        (datetime.timedelta)
    delta_closest: time distance between sensor-action and closest start or end
        (datetime.timedelta)
"""
def timeManagement(sensor_timestamp, activity, previous, activities):
    diff = activity['end_time'] - activity['start_time']
    sec = diff.seconds / 2.0
    delta = datetime.timedelta(seconds=sec)
    centre = activity['start_time'] + delta
    if previous == True:
        delta_closest = sensor_timestamp - activity['end_time']        
        delta_centre = sensor_timestamp - centre
        # Compute in_range
        duration = activities[activity['name']]['duration']
        double_sigma = centre + datetime.timedelta(seconds=duration)
        in_range = sensor_timestamp < double_sigma
    else:
        delta_closest = activity['start_time'] - sensor_timestamp
        delta_centre = centre - sensor_timestamp
        # Compute in_range
        duration = activities[activity['name']]['duration']
        double_sigma = centre - datetime.timedelta(seconds=duration)
        in_range = sensor_timestamp > double_sigma
        
    return in_range, delta_centre, delta_closest
        
        
            
"""
Main function
"""

def main(argv):
   # call the argument parser 
   [annotated_file, context_file, raw_data_file, summary_file] = parseArgs(argv[1:])
   print 'Parsed arguments:'
   print '   ', annotated_file
   print '   ', context_file
   print '   ', raw_data_file
   print '   ', summary_file
   
   # Read the annotated_file and build a DataFrame 
   annotated_df = pd.read_csv(annotated_file, parse_dates=0, index_col=0)
   
   #print 'Annotated actions:'
   #print annotated_df.head(50)
   
   # Parse context_file to obtain activities and actions       
   [activities, objects, sensors] = parseDescription(context_file)
   
   # Decide whether sensor-actions inside annotated activities (r_start_end)
   # are really from that activity
   filtered_df = filterInsiders(annotated_df, activities, objects, sensors)
   #print 'After insider filtering:'
   #print filtered_df[filtered_df['filter'] == 'Yes']
   
   # Decide whether outsider sensor-actions pertain to an activity
   resulting_df = computeOutsiders(filtered_df, activities, objects, sensors)
   
   

   
if __name__ == "__main__":   
    main(sys.argv)