# -*- coding: utf-8 -*-
"""
Created on Mon Jan 20 09:34:59 2014

@author: gazkune
"""

"""
This tool is to generate synthetic data of ADLs
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
    inputfile -> file where synthetic data generation is defined (special format)
    outputfile -> file to write the generated data (csv format)   
"""

def parseArgs(argv):
   inputfile = ''
   outputfile = ''
   try:
      opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
   except getopt.GetoptError:
      print 'synthetic_data_generator.py -i <inputfile> -o <outputfile>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'synthetic_data_generator.py -i <inputfile> -o <outputfile>'
         sys.exit()
      elif opt in ("-i", "--ifile"):
         inputfile = arg
      elif opt in ("-o", "--ofile"):
         outputfile = arg
   
   return inputfile, outputfile

"""
Function to check whether a sensor activation is well formed. The first element,
which should be a probability, is checked outside this function
Input:
    pattern: a sensor activation pattern ['Prob', sensor@delay, sensor@delay, ...]
Comment:
    Executes sys.exit() if any format mistake
"""
def checkSensorActivationPattern(pattern):
    # Ignore first element, which is a probability
    pattern = pattern[1:]
    for i in xrange(len(pattern)):
        # Check that each element is of form 'string'@'int'
        try:
            [sensor, delay] = pattern[i].split('@')
        except ValueError:
            msg = 'adlScriptParser: Sensor activations should be of form sensor@delay; read:', pattern[i]
            sys.exit(msg)
        #Check that delay is actually an integer
        try:
            delay = int(delay)
        except ValueError:
            sys.exit('adlScriptParser: Value read after @ is not an integer')    

"""
Function to check time format in ADL scipts. Times should be written as hour:minute 
where hour and minute are integers
Input:
    time: a string to represent a time
Comment:
    Executes sys.exit() if the format is not correct
"""
def checkTimeFormat(time):
    # Expected form: 'int:int'
    try:
        [hour, minute] = time.split(':')
    except ValueError:
        msg = "adlScriptParser: times shoudl be of form 'int@int'; read", time
        sys.exit(msg)
    try:
        hour = int(hour)
        minute = int(minute)
    except ValueError:
        msg = "adlScriptParser: check hours and minutes to be integers"
        sys.exit(msg)
        
"""
Function to check the forma of activity patterns: there are two possibilities:
Sequences -> ['S', start_time-end_time, ADL_name@delay, ADL_name@delay, ...]
Alterations -> ['A', start_time-end_time, ADL_name probability(float)]
Input:
    pattern: an activity pattern
    adl_names: the names of the ADLs, to check activity patterns are formed by those ADLs and
        not others
Comment:
    Executes sys.exit() if there is any format mistake
"""

def checkActivityPattern(pattern, adl_names):
    # Check whether we have sequences or alterations
    
    
    if pattern[0] == 'S':
        # Sequence form
        # ['S', start_time-end_time, ADL_name@delay, ADL_name@delay, ...]
        # Check timeslot
        try:
            [start, end] = pattern[1].split('-')
        except ValueError:
            msg = "adlScriptparser: activity pattern's second element should be a time slot of form 7:00-8:00"
            sys.exit(msg)
        # Make sure start and end are properly formed times
        checkTimeFormat(start)
        checkTimeFormat(end)
        
        # Check ADL lists with respective delays
        aux_pattern = pattern[2:]
        for i in xrange(len(aux_pattern)):
            # Check that each element is of form 'string'@'int'
            try:
                [adl, delay] = aux_pattern[i].split('@')
            except ValueError:
                msg = 'adlScriptParser: Expected adl_name@delay; read:', aux_pattern[i]
                sys.exit(msg)
            #Check that delay is actually an integer
            try:
                delay = int(delay)
            except ValueError:
                sys.exit('adlScriptParser: Value read after @ is not an integer')    
            
            # Check that adl is actually a name from adl_names
            try:
                adl_names.index(adl)
            except ValueError:
                msg = "adlScriptParser: In activity pattern, an ADL has been read which has not been listed previously in ADL names; read:", adl
                sys.exit(msg)
                
    elif pattern[0] == 'A':
        # Alteration form
        # ['A', start_time-end_time, ADL_name probability(float)]
        # Check timeslot
        try:
            [start, end] = pattern[1].split('-')
        except ValueError:
            msg = "adlScriptparser: activity pattern's second element should be a time slot of form 7:00-8:00"
            sys.exit(msg)
        # Make sure start and end are properly formed times
        checkTimeFormat(start)
        checkTimeFormat(end)
        
        # Check ADL name
        try:
            adl_names.index(pattern[2])
        except ValueError:
            msg = "adlScriptParser: In activity pattern, an ADL has been read which has not been listed previously in ADL names; read:", adl
            sys.exit(msg)
            
        # Check final element is a probability (float)
        try:
            prob = float(pattern[3])
        except ValueError:
            sys.exit("adlScriptParser: Expected a float after ADL name in alteration")
            
        # Check prob is smaller or equal than 1
        if prob > 1 or prob <0:
            msg = 'adlScriptParser: The probability value read for alteration is not between [0, 1]; read:', prob
            sys.exit(msg)
    else:
        msg = "adlScriptParser: activity pattern's first element should be 'S' or 'A'; read:", pattern[0]
        sys.exit(msg)
    

   
"""   
Function to read ADL script
Input: 
    adl_file -> the script to define synthetic data generation
Output: 
    simulated_days -> number of days to be simulated (int)
    adl_names -> Names of the ADLs taken into account (list of strings)
    sensor_activation_patterns -> different sensor patterns for each ADL, 
        containing sensor activations and their probabilities (list of lists of strings)
    activity_patterns -> contain daily frequency and occurring time slots (list of lists of strings)
    noise_specs -> noise specifications for sensor activations or action properties (list of lists)
"""

def adlScriptParser(adl_file):
    # Make sure the first line is a comment
    line = adl_file.readline()
    if line[0] != '#':       
        sys.exit("First line has to be a comment")
        
    # Next line contains the day number to be simulated
    line = adl_file.readline().strip('\n') # Remove EOL character
    try:
        simulated_days = int(line)
    except ValueError:
        sys.exit('adlScriptParser: Expecting an integer in the second line of input file')
            
    
    # Next line contains a comment
    line = adl_file.readline()
    if line[0] != '#':       
        sys.exit("Third line has to be a comment")    
    
    # Next line contains ADL names
    adl_names = []
    line = adl_file.readline().strip('\n') # Remove EOL character
    adl_names = line.split(' ')            
    
    # Make sure the next line is a comment
    line = adl_file.readline()
    if line[0] != '#':       
        sys.exit("Expected a comment after ADL names")
        
    # Next lines should contain sensor activation patterns for each activity    
    not_comment = True
    i = 0
    sensor_act_patterns = []
    while not_comment:            
        line = adl_file.readline().strip('\n')        
        # Check whether it is a comment
        if line[0] != '#':            
            # First line contains ADL name and number of patterns
            [name, pattern_number] = line.split(' ')
            
            # Check whether the name is the same name as adl_names
            if adl_names[i] != name:
                sys.exit("ADL names do not match")
                
            # Check whether pattern_number is an integer
            try:
                pattern_number = int(pattern_number)
            except ValueError:
                sys.exit("adlScriptParser: an integer expected alongside ADL name in sensor activation patterns")
                
            # Next 'pattern_number' lines contain sensor activation patterns
            pattern = []
            patterns = []
            prob_sum = 0.0;
            for j in xrange(pattern_number):
                line = adl_file.readline().strip('\n')
                pattern = line.split(' ')
                # Check whether sensor activation inside pattern are well formed
                checkSensorActivationPattern(pattern)
                patterns.append(pattern)                
                # First element is a probability; check before suming it for further checking
                try:
                    prob = float(pattern[0])
                except ValueError:
                    sys.exit("First value of a sensor activation pattern has to be a float")
                        
                prob_sum = prob_sum + prob
            
            # Check whether probabilities sum to 1
            if prob_sum != 1.0:
                msg = 'Probabilities for ADL ' + adl_names[i] + ' do not sum to 1'
                sys.exit(msg)
            
            #print 'Sum for ADL', adl_names[i], '=', prob_sum
            i = i + 1
            sensor_act_patterns.append(patterns)    
        else:        
            not_comment = False
        
    # Next lines are for activity patterns
    activity_patterns = []
    not_comment = True    
    while not_comment:
        line = adl_file.readline().strip('\n')
        # Check whether it is a comment
        if line[0] == '#':                    
            not_comment = False
        else:
            # First line of the pattern contains the Probability and lines of sequences and alterations
            if line.split(' ')[0] != 'Prob':
                msg = 'adlScriptParser: Prob expected but', line.split(' ')[0], 'read in activity patterns'
                sys.exit(msg)
                
            day_pattern = []
            try:
                probability = float(line.split(' ')[1])
            except ValueError:
                sys.exit("adlScriptParser: a float expected after Prob for activity patterns")
                
            day_pattern.append(probability)
            try:
                lines = int(line.split(' ')[2])
            except ValueError:
                sys.exit("adlScriptParser: number of lines expected (int) after probability for activity patterns")
            # Read the following 'lines' lines to complete the pattern
            pattern = []
            for j in xrange(lines):
                line = adl_file.readline().strip('\n')
                try:
                    pattern = line.split(' ')
                except ValueError:
                    sys.exit("adlScriptParser: an activity pattern should be a list of blank separated strings")
                
                # Check whether activity patterns are well formed
                checkActivityPattern(pattern, adl_names)
                day_pattern.append(pattern)            
            activity_patterns.append(day_pattern)
    
    # Next lines should contain the noise specifications
    # Each line has a probability value followed by action properties or sensor activations
    # That probability specifies the probability of activation in one hour time slot
    noise_specs = []
    not_comment = True
    while not_comment:
        line = adl_file.readline().strip('\n')
        # Check whether it is a comment
        if line[0] == '#':                    
            not_comment = False
        else:
            aux_list = line.split(' ')
            try:
                aux_list[0] = float(aux_list[0])
            except ValueError:
                msg = 'Expected a float number for first elemen of noise specification; read:' + aux_list[0]
                sys.exit(msg)
            
            noise_specs.append(aux_list)
            
    
    return simulated_days, adl_names, sensor_act_patterns, activity_patterns, noise_specs
    
"""
Function to generate sensor activations following the indications of the ADL script
Input:
    days -> How many days have to be simulated
    adl_instances -> ADL instances to be generated (int)
    adl_names -> Names of the ADLs taken into account (list of strings)
    sensor_activation_patterns -> different sensor patterns for each ADL, 
        containing sensor activations and their probabilities (list of lists of strings)
    activity_patterns -> contain daily frequency and occurring time slots (list of lists of strings)
    noise_specs -> contains the specifications for generating noisy sensor activations (list of lists)
    outputfile -> file where generated sensor activations are written (file name)
"""    
def adlGenerator(days, adl_names, sensor_activation_patterns, activity_patterns, noise_specs, outputfile):
    
    print 'Days to be simulated:', days
    
    current_day = getCurrentDay()

    # Initialize an empty pd.DataFrame object
    timed_sensor_activations = pd.DataFrame()    
    
    # Iterate through days and generate data considering activity and sensor activation patterns
    for i in xrange(days):
        # Choose an activity pattern for day 1 considering pattern probabilities
        print 'Day', i, ':', current_day        
        selected_pattern = getMostProbPattern(activity_patterns)        
        print 'Selected pattern:'
        print selected_pattern
        
        # selected_pattern contains the activity pattern for the current day
        for j in xrange(len(selected_pattern)):
            # Check whether we have a sequence or an alteration
            pattern = selected_pattern[j]
            # Initialize empty auxilary DataFrame
            timed_activations = pd.DataFrame()
            if pattern[0] == 'S':
                # This is a sequence                
                timed_activations = generateTimedSensorActivationsForSequence(pattern, sensor_activation_patterns, adl_names, current_day)
                # Provisional concatenation to avoid repetitions
                timed_sensor_activations = pd.concat([timed_sensor_activations, timed_activations])                
            
            elif pattern[0] == 'A':
                # This is an alteration                
                print 'We have an alteration'
                
                [result, timed_activations] = generateTimedSensorActivationsForAlteration(pattern, sensor_activation_patterns, adl_names, current_day)
                # depending on result, concatenate the activations
                if result == 1:
                    timed_sensor_activations = pd.concat([timed_sensor_activations, timed_activations])
                        
        
        # Generate noisy sensor activations for current day using noise_specs
        # Initialize empty DataFrame
        noisy_activations = pd.DataFrame()
        noisy_activations = generateNoisyActivations(noise_specs, current_day)
        # Print for debugging purposes
        print 'Noisy activations for day:', current_day
        print noisy_activations
        # Concatenate noisy_activations to timed_sensor_activations        
        timed_sensor_activations = pd.concat([timed_sensor_activations, noisy_activations])        
        
        # Update current_day!!!
        current_day = current_day + datetime.timedelta(days=1)
    
    timed_sensor_activations = timed_sensor_activations.sort_index()    
    timed_sensor_activations = timed_sensor_activations.rename(columns={0: 'sensor', 1: 'activity', 2: 'start_end'})
    print 'Generated complete timed sensor activations (head only):'
    print timed_sensor_activations.head(n=50)
    timed_sensor_activations.to_csv(outputfile)

"""
Function to generate noisy activations for a whole day using noise_specs read from adl_script
Input:
    noise_specs: contains the probabilities of activations per hour (list of lists)
    current_day: current day as datetime.datetime object
Output:
    noisy_activations: sensor activations with timestamps (pd.DataFrame)
"""
def generateNoisyActivations(noise_specs, current_day):
    # Initialize empty dates and sensor_array, which will be used to form noisy_activations    
    dates = []
    sensor_array = []
    # Iterate through 24 hours in current_day
    for i in xrange(24):
        # Calculate if activations should occur in this hour
        for j in xrange(len(noise_specs)):
            activation_prob = float(noise_specs[j][0])
            activations = noise_specs[j][1:]
            for k in xrange(len(activations)):
                rand_num = np.random.random()                
                if rand_num <= activation_prob:
                    # we must generate noise
                    # calculate a time for this noisy activation
                    seconds_delay = 3600 * np.random.random()
                    timestamp = current_day + datetime.timedelta(hours=i, seconds=seconds_delay)
                    dates.append(timestamp)
                    sensor_array.append([activations[k], 'None', ''])
    
    # Put dates and sensor_array in noisy_activations
    noisy_activations = pd.DataFrame(sensor_array, index=dates)
    return noisy_activations
                    

"""
Function to generate sensor activations from an activity pattern and sensor activation patterns
Input:
    selected_pattern: an alteration [A timeslot ADL Prob]
    sensor_activation_patterns: sensor activation patterns for each ADL
    adl_names: names of ADLs
    current_day: current day as datetime.datetime object
Output:    
    0/1: 0 if alteration is not executed, 1 otherwise
    timed_sensor_activations: sensor activation with timestamps (pd.DataFrame), if alteration
        gets executed, and empty DataFrame otherwise
"""
def generateTimedSensorActivationsForAlteration(selected_pattern, sensor_activation_patterns, adl_names, current_day):
    # Calculate whether alteration will be executed
    prob = float(selected_pattern[len(selected_pattern) - 1])
    rand_num = np.random.random();
    
    # Initialize an empty DataFrame
    timed_sensor_activations = pd.DataFrame()
    if rand_num <= prob:
        # Execute alteration
        # Select randomly the starting time of the sequence
        timeslot = selected_pattern[1]
        ref_time = generateTimeFromSlot(timeslot, current_day)
        adl_patterns = sensor_activation_patterns[adl_names.index(selected_pattern[2])]
        
        adl_name = selected_pattern[2]
                
        # Select the most probable sensor activation pattern for ADL
        sensor_pattern = getMostProbPattern(adl_patterns)
        print 'Selected sensor pattern for ADL', adl_name, ':'
        print sensor_pattern
        
        # To generate sensor activation, initialize dates and sensor_array
        dates = []
        dates.append(ref_time)
        sensor_array = []
        [sensor_array, dates] = generateSensorActivations(sensor_pattern, dates, datetime.timedelta(seconds=0), adl_name)
        
        # Create pd.DataFrame object with sensor_array and dates
        timed_sensor_activations = pd.DataFrame(sensor_array, index=dates)
        print 'Timed activations for alteration:'
        print timed_sensor_activations
        return [1, timed_sensor_activations]
    else:
        print 'Alteration will not be executed'
        return [0, timed_sensor_activations]
    
    
"""
Function to generate a uniformly distributed datatime.datatime 
from a day and time slot (string, ej: 7:00-8:00)
Input:
    timeslot: a string representing a time slot in 24h format (ej: '7:00-8:00')
    day: a datatime.datatime object with Year, Month and Day information
Output:
    ref_time: a datatime.datatime object, with a uniformly generated time sample
        (YY, MM, DD, HH, MM, SS) format        
"""
def generateTimeFromSlot(timeslot, day):
    end_hour = int(timeslot.split('-')[1].split(':')[0])
    end_minute = int(timeslot.split('-')[1].split(':')[1])
    end_time = datetime.datetime(day.year, day.month, day.day, end_hour, end_minute)
    
    start_hour = int(timeslot.split('-')[0].split(':')[0])
    start_minute = int(timeslot.split('-')[0].split(':')[1])
    start_time = datetime.datetime(day.year, day.month, day.day, start_hour, start_minute)
    
    delta = end_time - start_time
    print 'Time delta btw end and start times:', delta.seconds
    
    starting_seconds = delta.seconds * np.random.random()    
    
    return start_time + datetime.timedelta(seconds=starting_seconds)
    
"""
Function to generate sensor activations from an activity pattern and sensor activation patterns
Input:
    selected_pattern: a sequence [S timeslot ADL@delay ADL@delay...]
    sensor_activation_patterns: sensor activation patterns for each ADL
    adl_names: names of ADLs
    current_day: current day as datetime.datetime object
Output:
    timed_sensor_activations: sensor activation with timestamps (pd.DataFrame)
Comments:
    Use pandas DataFrames to store timestamp indexed sensor activations
    Generate sensor activations following the patterns and numpy.random functionalities
    Sensor activations will form DataFrames that can be concatenated (pd.concat) and sorted (df.sort_index)
"""
def generateTimedSensorActivationsForSequence(selected_pattern, sensor_activation_patterns, adl_names, current_day):
    
    # Select randomly the starting time of the sequence
    timeslot = selected_pattern[1]
    print 'Timeslot:', timeslot
    time0 = generateTimeFromSlot(timeslot, current_day)    
    print 'Time 0:', time0
    
    # Initilize dates list, which will be the index for a pd.DataFrame
    dates = []
    dates.append(time0)
    
    # Initialize sensor_array, where sensor activation will be written
    sensor_array = []
    # Pick up all the ADLs from selected_pattern
    adls = selected_pattern[2:]
    for i in xrange(len(adls)):
        current_adl = adls[i].split('@')[0]
        time_lapse = datetime.timedelta(seconds=int(adls[i].split('@')[1]))
        print 'Current ADL:', current_adl, 'Time lapse:', time_lapse.seconds
        # We have the ADL, time0 and time_lapse; now produce sensor activation following ADL pattern
        # and Gaussian sample generators for time
        adl_index = adl_names.index(current_adl)
        sensor_patterns = sensor_activation_patterns[adl_index]
        selected_pattern = getMostProbPattern(sensor_patterns)
        print 'Selected pattern for ADL', current_adl, ':'
        print selected_pattern
        [sensors, dates] = generateSensorActivations(selected_pattern, dates, time_lapse, current_adl)
        
        for j in xrange(len(sensors)):
            sensor_array.append(sensors[j])
    
    timed_sensor_activations = pd.DataFrame(sensor_array, index=dates)
    
    print 'Timed sensor activation for selected sequence:'
    print timed_sensor_activations
    
    return timed_sensor_activations

    
"""
Function to create sensor activations and times using Gaussian sample generators
Input:
    sensor_pattern: the selected pattern for sensor activations
    dates: datetime.datetime list, where the first element is time0, already set and further elements
        could also be set from previous calls to this function with previous ADLs
    time_lapse: this is the time lapse for the complete ADL
    current_adl: the name of the current ADL
Output:
    sensor_array: the array of sensor activations with ADL labels
    dates: the generated list of dates (datetime.datetime) 
"""
def generateSensorActivations(sensor_pattern, dates, time_lapse, current_adl):
    sensor_array = []
    if time_lapse.seconds > 0:
        # Generate a new time for ADL start time
        std = time_lapse.seconds * 0.25
        new_delay = datetime.timedelta(seconds=np.random.normal(time_lapse.seconds, std))
        dates.append(dates[len(dates)-1] + new_delay)
        
    for i in xrange(len(sensor_pattern)):        
        sensor = sensor_pattern[i].split('@')[0]
        delay = int(sensor_pattern[i].split('@')[1])
        if i == 0:
            sensor_array.append([sensor, current_adl, 'start'])
        elif i == len(sensor_pattern) - 1:
            sensor_array.append([sensor, current_adl, 'end'])
        else:
            sensor_array.append([sensor, current_adl, ''])
        if delay != 0:
            # Generate a new date
            std = delay * 0.25
            new_delay = datetime.timedelta(seconds=np.random.normal(delay, std))
            dates.append(dates[len(dates)-1] + new_delay)
        
    return sensor_array, dates            


"""
Function to get most probable activity pattern
Input:
    activity_patterns: a list of activity patterns or ADL patterns
Output:
    selected_pattern: a concrete pattern which has been selected probabilistically
"""
def getMostProbPattern(activity_patterns):
    number = np.random.random()
    print 'Randomly generated number:', number        
    selected_pattern = []
    accumulated_prob = 0.0
    for j in xrange(len(activity_patterns)):            
        prob = float(activity_patterns[j][0])
        print 'Probability for activity pattern', j, ':', prob
        accumulated_prob = accumulated_prob + prob
        if number <= accumulated_prob:
            # This is the selected pattern
            selected_pattern = activity_patterns[j][1:] # ignore the probability
            break
        
    return selected_pattern

"""
Function to get current day as datetime.datetime object
Output:
    datetime.datetime: current day in Year-Month-Day HH:MM:SS format
"""         
def getCurrentDay():
    today = time.strftime("%Y-%m-%d")
    year = int(today.split('-')[0])
    month = int(today.split('-')[1])
    day = int(today.split('-')[2])
    
    return datetime.datetime(year, month, day)
    
"""
Main function
"""

def main(argv):
    # call the argument parser 
   [inputfile_name, outputfile_name] = parseArgs(argv[1:])
   print 'Input file is', inputfile_name
   print 'Output file is', outputfile_name   
   
   # open input and output files
   inputfile = open(inputfile_name, 'r')
   #outputfile = open(outputfile_name, 'w')
   
   # parse the ADL script
   [simulated_days, adl_names, sensor_act_patterns, activity_patterns, noise_specs] = adlScriptParser(inputfile)   
   
  
   # Print the contents of the script for debugging purposes
   """    
   print '\nNumber of days to be simulated:', simulated_days, '\n'
   for i in xrange(len(adl_names)):      
       print 'ADL', i, ':', adl_names[i]
       print 'Sensor activation patterns:', len(sensor_act_patterns[i])
       for j in xrange(len(sensor_act_patterns[i])):
           print sensor_act_patterns[i][j]
           
       print ' ' 
       
   print 'Activity patterns: \n'
   for i in xrange(len(activity_patterns)):
       pattern = activity_patterns[i]
       print 'Activity pattern', i, 'with probability', pattern[0]
       #pattern = pattern[1:]
       for j in xrange(1, len(pattern)):
           print pattern[j]
       
       print ' '
   """
   print 'Noise specifications:'
   for i in xrange(len(noise_specs)):
       print noise_specs[i]
       
   # Once the ADL generation script has been read, generate data
   adlGenerator(simulated_days, adl_names, sensor_act_patterns, activity_patterns, noise_specs, outputfile_name)
            
if __name__ == "__main__":
   main(sys.argv)