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
    time_approach -> int (0, 1, 2) to decide what time approach to use
    raw_data_file -> csv file where results will be provided
    [timestamp, sensor, action, activity, start_end]
    summary_file -> json file where final result summary will be provided
    {activity_name: format to be decided!}
"""

def parseArgs(argv):
   annotated_file = ''
   context_file = ''
   time_approach = -1
   raw_data_file = ''
   summary_file = ''
   try:
      opts, args = getopt.getopt(argv,"ha:c:t:r:s:",["annotated=","context=","time=","raw=","summary="])      
   except getopt.GetoptError:
      print 'activity_clustering.py -a <annotated_actions> -c <context_model> -t <time_approach> -r <raw_data_file> -s <summary_file>'
      print 'For time approach:'
      print '   0: simple time distance to the centre of the activity'
      print '   1: duration normalized time distance to static centre'
      print '   2: duration normalized time distance to dynamic centre'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'activity_clustering.py -a <annotated_actions> -c <context_model> -t <time_approach> -r <raw_data_file> -s <summary_file>'
         print 'For time approach:'
         print '   0: simple time distance to the centre of the activity'
         print '   1: duration normalized time distance to static centre'
         print '   2: duration normalized time distance to dynamic centre'
         sys.exit()
      elif opt in ("-a", "--annotated"):
         annotated_file = arg      
      elif opt in ("-c", "--context"):
         context_file = arg
      elif opt in ("-t", "--time"):
         time_approach = int(arg)
      elif opt in ("-r", "--raw"):
         raw_data_file = arg
      elif opt in ("-s", "--summary"):         
         summary_file = arg      
   
   if not time_approach in [0, 1, 2]:
       msg = 'time has to be 0, 1 or 2 and not ' + str(time_approach)
       exit(msg)
       
   return annotated_file, context_file, time_approach, raw_data_file, summary_file
   
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
    [timestamp, sensor, action, annotated_label, a_start_end, location]
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
        location = aux_df.loc[index, 'location']
        # filter sensor-action if one of 2 criteria doesn't apply
        # check whether action is in the minimal model
        annotated_activity = aux_df.loc[index, 'annotated_label']
        min_model = activities[annotated_activity]['min_model']
        try:
            min_model.index(action)
        except ValueError:
            # Action is not in minimal model
            # Check location and type
            #loc = checkLocationCompatibility(annotated_activity, sensor, 
            #                                 objects, sensors, activities)
            olocation = objects[sensors[sensor]['attached-to']]['location']
            if olocation != location:
                loc = False
            else:
                loc = True
                
            typ = checkTypeCompatibility(annotated_activity, sensor, 
                                         objects, sensors, activities)
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
    time_approach: int to specify what time approach we should use
        0: simple time distance to the centre of the activity
        1: duration normalized time distance to static centre
        2: duration normalized time distance to dynamic centre
Output:
    resulting_df: pd.DataFrame where the following info is provided
    [timestamp, sensor, action, annotated_label, a_start_end, filter, assign]
    where 'assign' column refers to the final activity of the sensor-action
"""
def computeOutsiders(filtered_df, activities, objects, sensors, time_approach):
    # store outsider sensor-actions    
    outsider_index = filtered_df[filtered_df['annotated_label'] == 'None'].index
    # Copy the 'annotated_label' column to generate a new column in filtered_df
    filtered_df['assign'] = filtered_df['annotated_label']
    # TODO: Add another column for definitive start/end
    filtered_df['d_start_end'] = filtered_df['a_start_end']
    
    #print 'Filtered df with new columns:'
    #print filtered_df['d_start_end'].head(50)
        
    # TODO: do not forget to change the assign value for those sensor-actions
    # whose 'filter' value is 'Yes' when outsiders have been processed (end of the function)
    
    # store indexes from activities ('start' and 'end' indexes for 'a_start_end' labels)    
    activity_index = filtered_df[np.logical_or(filtered_df['a_start_end'] == 'start', filtered_df['a_start_end'] == 'end')].index    
    act_index_list = activity_index.tolist()
        
    # For each action-sensor find its previous and next activity
    previous_activity = {}
    next_activity = {}
    last_j = 0
    #count_outsiders = 0
    #for i in outsiders_df.index:
    for i in outsider_index:
        # Use next_j to store where we start iterating for activities
        j = last_j        
        while j < len(activity_index):
            # Update j = j + 2, since two blocks form one activity (start, end)
            # Special case: j + 2 == len(activity_df) (last activity) and
            # sensor-action is before that activity -> there is no next_activity            
            if j + 2 == len(activity_index) and i > activity_index[j+1]:
                previous_activity = {'name' : filtered_df.loc[activity_index[j], 
                                                          'annotated_label'],
                                     'start_time' : activity_index[j], 
                                     'end_time' : activity_index[j+1],
                                     'location' : filtered_df.loc[activity_index[j], 'location']}
                next_activity = {}
                # Update last_j
                last_j = j
                break
            
            if i < activity_index[j]:
                if j == 0:
                    previous_activity = {}
                    next_activity = {'name' : filtered_df.loc[activity_index[j], 
                                                          'annotated_label'], 
                                     'start_time' : activity_index[j], 
                                     'end_time' : activity_index[j+1],
                                     'location' : filtered_df.loc[activity_index[j], 'location']}
                if j > last_j:
                    previous_activity = {'name' : filtered_df.loc[activity_index[j-1],
                                                                  'annotated_label'],
                                        'start_time' : activity_index[j-2],
                                        'end_time' : activity_index[j-1],
                                        'location' : filtered_df.loc[activity_index[j-1], 'location']}
                    next_activity = {'name' : filtered_df.loc[activity_index[j], 
                                                          'annotated_label'], 
                                     'start_time' : activity_index[j], 
                                     'end_time' : activity_index[j+1],
                                     'location' : filtered_df.loc[activity_index[j], 'location']}
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
        sensor = filtered_df.loc[i, 'sensor']
        
        # T!! WARNING! Due to dynamic activity centre calculation
        # a sensor-action that was an outsider at the beginning can be an insider
        # now, since a previous sensor-action could be included in the next activity
        # In that case, current sensor-action would consider that the activity in which
        # is located is a previous activity. Check whether the sensor-action is actually
        # an insider of a expanded activity
        if previous_activity != {}:
            activity = previous_activity['name']
            if previous_activity['start_time'] < i and i < previous_activity['end_time']:
                print i, 'sensor:', sensor, 'is now an insider of', activity
                # Treat it as an insider -> if location and type are compatible, assign activity
                loc_ok  = previous_activity['location'] == objects[sensors[sensor]['attached-to']]['location']
                type_ok = checkTypeCompatibility(activity, sensor, objects, sensors, activities)
                if type_ok and loc_ok:
                    filtered_df.loc[i, 'assign'] = activity
                    print '   assign to', activity
                else:
                    filtered_df.loc[i, 'filter'] = 'Yes'
                    print '   not compatible with', activity
                continue
        
        # Check location and type compatibility with previous activity (if it exists)        
        # TODO: for location compatibility: even though an activity may be perfomed
        # in several locations, it would be nice to infer from data where it has
        # been actually performed and use that location for location compatibility
        # I added a location column to activity_df, where inferred location
        # for each activity can be found
        if previous_activity != {}:
            activity = previous_activity['name']
            #p_loc_ok = checkLocationCompatibility(activity, sensor, objects, sensors, activities) == True
            p_loc_ok = previous_activity['location'] == objects[sensors[sensor]['attached-to']]['location']
            p_type_ok = checkTypeCompatibility(activity, sensor, objects, sensors, activities) == True 
            # Time management 
            [p_in_range, p_delta_centre, p_delta_closest, p_dtime_dist, p_stime_dist] = timeManagement(i, previous_activity, True, activities)
        else:
            p_loc_ok = False
            p_type_ok = False
        # Check location and type compatibility with previous activity (if it exists)    
        if next_activity != {}:
            activity = next_activity['name']
            n_loc_ok = next_activity['location'] == objects[sensors[sensor]['attached-to']]['location']
            n_type_ok = checkTypeCompatibility(activity, sensor, objects, sensors, activities) == True 
            # Time management
            [n_in_range, n_delta_centre, n_delta_closest, n_dtime_dist, n_stime_dist] = timeManagement(i, next_activity, False, activities)
            # in case of next activity, dynamic and static time distance are the same
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
            print '   dynamic time_dist:', p_dtime_dist
            print '   static time_dist:', p_stime_dist
        else:
            if previous_activity != {}:
                print '   not compatible with previous activity', previous_activity['name']
                #print '   object location', objects[sensors[sensor]['attached-to']]['location'], 'Activity location:', previous_activity['location']
            else:
                print '   there is no previous activity'
        if n_loc_ok == True and n_type_ok == True:      
            print '   next:', next_activity['name']
            print '   start:', next_activity['start_time'], ', end:', next_activity['end_time']
            print '   in_range:', n_in_range
            print '   delta_centre:', n_delta_centre.seconds
            print '   delta_closest:', n_delta_closest.seconds
            print '   time_dist:', n_stime_dist
        else:
            if next_activity != {}:
                print '   not compatible with next activity', next_activity['name']
                #print '   object location', objects[sensors[sensor]['attached-to']]['location'], 'Activity location:', next_activity['location']
            else:
                print '   there is no next activity'
                
        # TODO: decide how to handle time distance in case an action is in range 
        # with previous and next. Issues:
        # 1) Consider time distance relative to expected duration (time/duration)
        # 2) Consider the portion of duration covered by previous and next activities
                
        # Decide whether sensor-action pertains to previous, next or none
        # Use p/n_loc_ok, p/n_type_ok and p/n_in_range 
        # Use time_approach for time management criterion
        previous_ok = p_loc_ok and p_type_ok and p_in_range
        next_ok = n_loc_ok and n_type_ok and n_in_range
        
        if not previous_ok and not next_ok:
            print '   Not assigned'
        elif previous_ok and not next_ok:
            # sensor-action pertains to previous activity
            filtered_df.loc[i, 'assign'] = previous_activity['name']
            print '   Assigned to previous activity'
            # Change 'd_start_end' column value for previous activity
            filtered_df.loc[previous_activity['end_time']:i, 'd_start_end'] = np.nan
            filtered_df.loc[i, 'd_start_end'] = 'end'            
                
        elif not previous_ok and next_ok:
            # sensor-action pertains to next activity
            filtered_df.loc[i, 'assign'] = next_activity['name']
            print '   Assigned to next activity'
            # Change 'd_start_end' column value for next activity
            if filtered_df.loc[next_activity['start_time'], 'd_start_end'] == 'start':
                filtered_df.loc[next_activity['start_time'], 'd_start_end'] = np.nan
                filtered_df.loc[i, 'd_start_end'] = 'start'
            # for dynamic centre calculation, we have to modify activity_index
            # to include current sensor-action's timestamp in next activity
            if time_approach == 2:                
                pos = act_index_list.index(next_activity['start_time'])
                activity_index = activity_index.insert(pos, i)
                activity_index = activity_index.drop(next_activity['start_time'])
                act_index_list = activity_index.tolist()
                #print '   New limits:', activity_index[pos], ',', activity_index[pos+1]
                #exit()
        elif previous_ok and next_ok:
            # Both are possible, use time criterion
            if time_approach == 0:
                # Distance to centre
                if p_delta_centre <= n_delta_centre:
                    # Previous activity
                    filtered_df.loc[i, 'assign'] = previous_activity['name']
                    print '   Assigned to previous activity'
                    # Change 'd_start_end' column value for previous activity
                    filtered_df.loc[previous_activity['end_time']:i, 'd_start_end'] = np.nan
                    filtered_df.loc[i, 'd_start_end'] = 'end'
                else:
                    # Next activity
                    filtered_df.loc[i, 'assign'] = next_activity['name']
                    print '   Assigned to next activity'
                    # Change 'd_start_end' column value for next activity
                    if filtered_df.loc[next_activity['start_time'], 'd_start_end'] == 'start':
                        filtered_df.loc[next_activity['start_time'], 'd_start_end'] = np.nan
                        filtered_df.loc[i, 'd_start_end'] = 'start'
            elif time_approach == 1:
                # Distance to static centre
                if p_stime_dist <= n_stime_dist:
                    # Previous activity
                    filtered_df.loc[i, 'assign'] = previous_activity['name']
                    print '   Assigned to previous activity'
                    # Change 'd_start_end' column value for previous activity
                    filtered_df.loc[previous_activity['end_time']:i, 'd_start_end'] = np.nan
                    filtered_df.loc[i, 'd_start_end'] = 'end'
                else:
                    # Next activity
                    filtered_df.loc[i, 'assign'] = next_activity['name']
                    print '   Assigned to next activity'
                    # Change 'd_start_end' column value for next activity
                    if filtered_df.loc[next_activity['start_time'], 'd_start_end'] == 'start':
                        filtered_df.loc[next_activity['start_time'], 'd_start_end'] = 'harl'
                        filtered_df.loc[i, 'd_start_end'] = 'start'
            elif time_approach == 2:
                # Distance to dynamic centre
                if p_dtime_dist <= n_dtime_dist:
                    # Previous activity
                    filtered_df.loc[i, 'assign'] = previous_activity['name']
                    print '   Assigned to previous activity'
                    # Change 'd_start_end' column value for previous activity
                    filtered_df.loc[previous_activity['end_time']:i, 'd_start_end'] = np.nan
                    filtered_df.loc[i, 'd_start_end'] = 'end'
                else:
                    # Next activity
                    filtered_df.loc[i, 'assign'] = next_activity['name']
                    print '   Assigned to next activity'
                    # Change 'd_start_end' column value for next activity
                    if filtered_df.loc[next_activity['start_time'], 'd_start_end'] == 'start':
                        filtered_df.loc[next_activity['start_time'], 'd_start_end'] = np.nan
                        filtered_df.loc[i, 'd_start_end'] = 'start'
                    # for dynamic centre calculation, we have to modify activity_index
                    # to include current sensor-action's timestamp in next activity
                    pos = act_index_list.index(next_activity['start_time'])
                    activity_index = activity_index.insert(pos, i)
                    activity_index = activity_index.drop(next_activity['start_time'])
                    act_index_list = activity_index.tolist()
                    #print '   New limits:', activity_index[pos], ',', activity_index[pos+1]
                    #exit()
    
    # All outsiders processed: filter the results with insiders
    to_be_filtered = filtered_df[filtered_df['filter'] == 'Yes']
    filtered_df.loc[to_be_filtered.index, 'assign'] = 'None'
    
    return filtered_df
    
    
"""
Function to manage time issues between a sensor-action and an activity
Criterion: Gaussian criterion
Input:
    sensor_timestamp: timestamp of the sensor-action (pd.tslib.Timestamp)
    activity: a dict describing an activity {'name', 'start_time', 'end_time', 'location'}
    where start_time and end_time are pd.tslib.Timestamp
    previous: boolean that indicates whether activity is before sensor-action    
    activities: dict with activity description from context_model
Output:
    in_range: True if sensor_timestamp is inside 2*sigma (from start_time, end_time)
    delta_centre: time distance between sensor-action and activity centre
        (datetime.timedelta)
    delta_closest: time distance between sensor-action and closest start or end
        (datetime.timedelta)
    dyn_time_dist: time distance using the metrics defined |T_action - C_activity|/duration
        where T_action is the timestamp of the action, C_activity is the centre of the activity
        (its calculation is based on duration if activity is previous) and duration is obtained
        from the context_model
        (float)
    st_time_dist: time distance using the metrics defined |T_action - C_activity|/duration
        where T_action is the timestamp of the action, C_activity is the centre of the activity
        (static calculation) and duration is obtained
        from the context_model.
        (float) 
    
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
        # Compute time_dist
        a_duration = activities[activity['name']]['duration'] # int
        a_half_duration = a_duration / 2.0 # float
        h_centre = activity['start_time'] + datetime.timedelta(seconds=a_half_duration)
        if h_centre > sensor_timestamp:
            h_delta = h_centre - sensor_timestamp
        else:
            h_delta = sensor_timestamp - h_centre
        dyn_time_dist = h_delta.seconds / float(a_duration)
        st_time_dist = delta_centre.seconds / float(a_duration)
    else:
        delta_closest = activity['start_time'] - sensor_timestamp
        delta_centre = centre - sensor_timestamp
        # Compute in_range
        duration = activities[activity['name']]['duration']
        double_sigma = centre - datetime.timedelta(seconds=duration)
        in_range = sensor_timestamp > double_sigma
        # Compute time_dist
        a_duration = activities[activity['name']]['duration'] # int        
        st_time_dist = delta_centre.seconds / float(a_duration)
        dyn_time_dist = st_time_dist
        
    return in_range, delta_centre, delta_closest, dyn_time_dist, st_time_dist
        
"""
Function to test the location inference idea. The idea is to infere the location of
a concrete activity from all the possible locations where an activity can be performed.
For that purpose, we can use the sensors-objects used in that concrete activity
Input:
    annotated_df: pd.DataFrame where sensor-actions have been annotated with activity labels
    activities: dict which describes activities obtained from context_model
    objects: dict which describes objects obtained from context_model
    activities: dict which describes sensors obtained from context_model
Output:
    location_df: pd.DataFrame with the same index as annotated_df and inferred location
    for each activity (if there is not activity, location = None)
"""
def locationInferenceFromActivity(annotated_df, activities, objects, sensors):
    
    labeled_activities = annotated_df[annotated_df['annotated_label'] != 'None']
    i = 0
    index = labeled_activities.index
    # a list of activity locations
    aux_list = ['None'] * len(annotated_df)
    location_df = pd.DataFrame(aux_list, index=annotated_df.index)
    while i < len(labeled_activities):
        activity = labeled_activities.loc[index[i], 'annotated_label']
        a_locations = activities[activity]['location'] # list of strings
        o_locations = []
        while i < len(labeled_activities) and labeled_activities.loc[index[i], 'annotated_label'] == activity:
            if labeled_activities.loc[index[i], 'a_start_end'] == 'start':
                start_index = i
            if labeled_activities.loc[index[i], 'a_start_end'] == 'end':
                end_index = i
            sensor = labeled_activities.loc[index[i], 'sensor']
            action = sensors[sensor]['action']
            olocation = objects[sensors[sensor]['attached-to']]['location']
            try:
                min_model = activities[activity]['min_model']
                min_model.index(action)
                o_locations.append(olocation)
                i = i + 1
            except ValueError:
                i = i + 1
                continue
        
        for j in xrange(1, len(o_locations)):
            if o_locations[j] != o_locations[j-1]:
                msg = 'Error: for activity '+ activity + ' different locations have been found: ' + str(o_locations) + '\n t: ' + str(index[i])
                exit(msg)
        try:
            loc_index = a_locations.index(o_locations[0])
            location_df.loc[index[start_index]:index[end_index]] = a_locations[loc_index]
            #print 'Location for activity', activity, 'is', a_locations[loc_index]
        except ValueError:
            msg = 'Location ' + o_locations[0] + ' is not modeled for activity ' + activity
            
    return location_df
            
"""
Function to build the summary file. Information in the summary file:
Activity:
    name: the name of the activity (string) (this will be the key of the dict)
    occurrences: occurrences in the dataset provided, as labeled by the learning system (int)
    objects: list of objects and their frequencies (list of [freq, obj-name])
    actions: list of actions and their frequencies (list of [freq. action-name])
    patterns: activity patterns and their frequencies (list of [freq, [action0, ..., actionN])
    duration: average duration and standard deviation (list [avg, std])
    location: location where activity has been executed and frequency (list [freq, location])
Input:
    resulting_df: pd.DataFrame with at least the following info 
        [timestamp, sensor, action, annotated_label, a_start_end, assign, d_start_end]
    activities: dict with activities from context_model
    objects: dict with objects from context_model
    sensors: dict with sensors from context_model
Output:
    summary_dict
"""
def buildSummaryDict(resulting_df, activities, objects, sensors):
    
    # store indexes from activities ('start' and 'end' indexes for 'a_start_end' labels)    
    #activity_index = resulting_df[np.logical_or(resulting_df['d_start_end'] == 'start', resulting_df['d_start_end'] == 'end')].index
    # Init empty dict for summary
    summary = {}
    
    # Iterate through activities
    for key in activities.keys():
        key_index = resulting_df[np.logical_and(resulting_df['assign'] == key, np.logical_or(resulting_df['d_start_end'] == 'start', resulting_df['d_start_end'] == 'end'))].index
        if len(key_index) > 0:
            # For debugging purposes
            #print 'Activity:', key
            #print resulting_df.loc[key_index, 'assign']
            activity_info = {}
            # key_index is a list of indexes where start and end times for activity 
            # 'key' are stored
            
            # Calculate and store occurrences
            activity_info['occurrences'] = len(key_index) / 2
            print 'Activity:', key 
            print '   occurrences:', activity_info['occurrences']
            
            # Find patterns and store in pattern_list
            pattern_list = []
            # Use the same loop to find used objects and actions and store their frequencies
            object_list = []
            action_list = []
            duration_list = []
            locations = []
            for i in xrange(len(key_index)):
                if resulting_df.loc[key_index[i], 'd_start_end'] == 'end':
                    continue
                
                pattern = resulting_df[resulting_df['assign'] == key].loc[key_index[i]:key_index[i+1], 'action'].tolist()
                
                # The following loop is to fill pattern_list
                end_loop = False
                j = 0
                while not end_loop:
                    if len(pattern_list) == 0:
                        # Special case                        
                        pattern_list.append([1, pattern])
                        end_loop = True
                    else:
                        if j >= len(pattern_list):
                            end_loop = True
                        else:
                            pos = isPatternInList(pattern, pattern_list)
                            if pos != -1:
                                #print '   Repeated pattern!'
                                # Remember first element of a pattern is frequency
                                pattern_list[pos][0] = pattern_list[pos][0] + 1
                                end_loop = True
                            else:
                                # Add new pattern to pattern_list
                                #print '   New pattern!'
                                pattern_list.append([1, pattern])
                                end_loop = True
                    j = j + 1
                
                # store sensor activations for current activity in 'sensor_list'
                sensor_list = resulting_df[resulting_df['assign'] == key].loc[key_index[i]:key_index[i+1], 'sensor'].tolist()
                # Fill actions and objects in the following part
                for j in xrange(len(pattern)):
                    action = pattern[j]
                    sensor = sensor_list[j]
                    object_name = sensors[sensor]['attached-to']
                    # Fill actions
                    pos = findItemInFrequencyList(action, action_list)
                    if pos == -1:
                        action_list.append([1, action])
                    else:
                        action_list[pos][0] = action_list[pos][0] + 1
                    # Fill objects
                    pos = findItemInFrequencyList(object_name, object_list)
                    if pos == -1:
                        object_list.append([1, object_name])
                    else:
                        object_list[pos][0] = object_list[pos][0] + 1                    
                
                # Store duration
                d = key_index[i+1] - key_index[i]                
                duration_list.append(d.seconds)
                
                # Store location information
                # store sensor activations for current activity in 'sensor_list'
                location_list = resulting_df[resulting_df['assign'] == key].loc[key_index[i]:key_index[i+1], 'location'].tolist()
                for j in xrange(len(location_list)):
                    if location_list[j] != 'None':
                        pos = findItemInFrequencyList(location_list[j], locations)
                        if pos == -1:
                            locations.append([1, location_list[j]])
                            break
                        else:
                            locations[pos][0] = locations[pos][0] + 1
                            break
            
            activity_info['patterns'] = pattern_list
            activity_info['objects'] = object_list
            activity_info['actions'] = action_list
            activity_info['duration'] = [np.mean(duration_list), np.std(duration_list)]
            activity_info['locations'] = locations
            # for debugging purposes
            print '   patterns:'
            for i in xrange(len(pattern_list)):
                print '    ', pattern_list[i]            
            print '   objects:', activity_info['objects']
            print '   actions:', activity_info['actions']
            print '   duration:', activity_info['duration']
            
                             
        else:
            continue
        # Add activity_info to summary
        summary[key] = activity_info
    
    return summary
    

"""
function to find an item (a string), in a so-called frequency list
[[freq, item0], [freq, item1],..., [freq, itemN]]
Input:
    item: name of the item to be found (string)
    freq_list: a frequency list as described above
Output:
    pos: position of the item if it is in the list, -1 otherwise
"""
def findItemInFrequencyList(item, freq_list):
    pos = -1
    i = 0
    while pos == -1 and i < len(freq_list):
        if freq_list[i][1] == item:
            pos = i
        else:
            i = i + 1
    
    return pos

"""
Function to find whether pattern is in pattern_list. If it is, return position
If it is not, return -1
Input:
    pattern: [action0,..., actionN]
    pattern_list: [[freq, [action0,...,actionN]], [freq, [action0,..., actionN]]]
Output:
    pos: -1 if pattern is not in pattern_list, else position of the pattern in the list
"""
def isPatternInList(pattern, pattern_list):
    i = 0
    pos = -1
    while i < len(pattern_list) and pos == -1:
        if pattern == pattern_list[i][1]:
            pos = i
        else:
            i = i + 1
    return pos    
    
"""
Main function
"""

def main(argv):
   # call the argument parser 
   [annotated_file, context_file, time_approach, raw_data_file, summary_file] = parseArgs(argv[1:])
   print 'Parsed arguments:'
   print '   ', annotated_file
   print '   ', context_file
   print '   ', time_approach
   print '   ', raw_data_file
   print '   ', summary_file
   
   # Read the annotated_file and build a DataFrame 
   annotated_df = pd.read_csv(annotated_file, parse_dates=0, index_col=0)
   
   #print 'Annotated actions:'
   #print annotated_df.head(50)
   
   # Parse context_file to obtain activities and actions       
   [activities, objects, sensors] = parseDescription(context_file)
   
   # To test location inference from activity execution
   location_df = locationInferenceFromActivity(annotated_df, activities, objects, sensors)
   annotated_df['location'] = location_df
   #print 'After location inference'
   #print annotated_df.head(50)
      
   # Decide whether sensor-actions inside annotated activities (a_start_end)
   # are really from that activity
   filtered_df = filterInsiders(annotated_df, activities, objects, sensors)
     
   # Decide whether outsider sensor-actions pertain to an activity
   resulting_df = computeOutsiders(filtered_df, activities, objects, sensors, time_approach)
   
   # T!! comment only for some tests!
   resulting_df.to_csv(raw_data_file)
   
   # Build the summary dict
   summary_dict = buildSummaryDict(resulting_df, activities, objects, sensors)   
   
   # Write the json file sumarry_file
   with open(summary_file, 'w') as outfile:
       json.dump(summary_dict, outfile, indent=4)
   
if __name__ == "__main__":   
    main(sys.argv)