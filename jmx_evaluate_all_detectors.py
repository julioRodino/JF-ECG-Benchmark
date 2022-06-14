#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""

This code will run all subjects, all experiments, all leads recordings through
all detectors or a single detector as required.
For each recording (for which there are annotations) passed through a detector
the detection locations will be saved, and then these passed for interval
analysis, where jitter, missed beats and extra/spurious detections are
identified. Jitter is taken as the difference (in samples) between the
annotated interval and the detected interval, and is not truly HRV as it is
calculated not just at rest.
For each recording (as above) passed through a detector, the jitter, missed
beat sample locations and extra/spurious detection locations are all saved as
seperate csv files. This means that all 'raw' interval analysis data is
available for subsequent benchmarking, plotting or analysis by lead type,
experiment, etc as desired and has not been combined in a way which results in
loss of information.
The matched filter detector can use a default template or user generated
averaged PQRST shapes for each subject.
The positional data for missed and extra beats can be used to plot markers
onto source recordings to indicate where and how a detector is behaving with
actual ECG recordings.
This code can be used to generate 'global' average standard deviatrion and
mean missed beat and extra detection values which are then saved as a csv file
and are used as reference values for the new overall benchmarking method

Create a folder named 'saved_csv' in the current directory to save csv files to.

"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ecg_gudb_database import GUDb
from ecgdetectors import Detectors
import pathlib # For local file use

# The JMX analysis for a detector
import jmx_analysis

# directory where the results are stored
resultsdir = "results"

try:
    os.mkdir(resultsdir)
except OSError as error:
    pass

fs = 250 #sampling rate
detectors = Detectors(fs) # Initialise detectors for 250Hz sample rate (GUDB)

current_dir = pathlib.Path(__file__).resolve()

#%% Initialise parameters for analysis

save_global_results = True # when 'True' saves global jitter, missed, extra values as csv and prints

trim=True # CHANGE TO FALSE IF YOU DONT WANT TO TRIM
# * Values chosen by observation of detector settling intervals required *

#initialise for plots (*if used*)
plt.rc('xtick',labelsize=10)
plt.rc('ytick',labelsize=10)

analysed=0 # overall count of analysed subjects

data_det_lead = {} # initialise for data to be saved by lead and detector
det_lead_stats = {} # initialise for data to be saved by lead and detector

# initialise for global average jitter standard deviation, and global mean missed and extra beats
jitter_std_dev_total = 0.0 # running total for standard deviations for jitter for each detector

global_jitter=[]
global_missed=[]
global_extra=[]

# Detectors, recording leads and experiments can be added/removed from lists as required
all_recording_leads=["einthoven_ii", "chest_strap_V2_V1"] # can be expanded if required
all_experiments = ["sitting","maths","walking","hand_bike","jogging"]

for detector in detectors.detector_list:

    print("Processing:",detector[0])

    detectorname = detector[1].__name__
    detectorfunc = detector[1]
    
    name_jitter_sub = 'jitter_accum_sub_' + detectorname
    exec(name_jitter_sub+' = []') # initialse for all detector names, jitter arrays
    name_missed_sub = 'missed_accum_sub_' + detectorname
    exec(name_missed_sub + ' = []') # initialse for all detector names, missed beat arrays
    name_extra_sub = 'extra_accum_sub_' + detectorname
    exec(name_extra_sub + ' = []') # initialse for all detector names, missed detection arrays

    for record_lead in all_recording_leads: # loop for all chosen leads
        
        name_jitter = 'jitter_accum_' + record_lead +'_' + detectorname
        exec(name_jitter+' = []') # initialse for all rec leads, det names (jitter arrays)
        name_missed = 'missed_accum_' + record_lead +'_' + detectorname
        exec(name_missed + ' = []') # initialse for all rec leads, det names (missed beat arrays)
        name_extra = 'extra_accum_' + record_lead +'_' + detectorname
        exec(name_extra + ' = []') # initialse for all rec leads, det names (missed detection arrays)
        
        jitter_all_exp=[]
        missed_all_exp=[]
        extra_all_exp=[]
        
        for experiment in all_experiments: # loop for all chosen experiments
            
            jitter=[]
            missed=[]
            extra=[]
            
            for subject_number in range(0, 25): # loop for all subjects
                
                # print('')
                print("Analysing subject %d, %s, %s" %(subject_number, experiment, record_lead))
    
                # creating class which loads the experiment
        
                # For online GUDB access
                ecg_class = GUDb(subject_number, experiment) 
            
                # For local GUDB file access:
                # from ecg_gla_database import Ecg # For local file use
                # data_path = str(pathlib.Path(__file__).resolve().parent.parent/'experiment_data')
                # ecg_class = Ecg(data_path, subject_number, experiment)
                
                # getting the raw ECG data numpy arrays from class
                chest_strap_V2_V1 = ecg_class.cs_V2_V1
                einthoven_i = ecg_class.einthoven_I
                einthoven_ii = ecg_class.einthoven_II
                einthoven_iii = ecg_class.einthoven_III
        
                # getting filtered ECG data numpy arrays from class
                ecg_class.filter_data()
                chest_strap_V2_V1_filt = ecg_class.cs_V2_V1_filt
                einthoven_i_filt = ecg_class.einthoven_I_filt
                einthoven_ii_filt = ecg_class.einthoven_II_filt
                einthoven_iii_filt = ecg_class.einthoven_III_filt
            
                data=eval(record_lead) # set data array (i.e. recording to be processed)
               
                if 'chest' in record_lead: 
                    if ecg_class.anno_cs_exists:
                        data_anno = ecg_class.anno_cs
                        exist=True
                        analysed=analysed+1
                    else:
                        exist=False
                        print("No chest strap annotations exist for subject %d, %s exercise" %(subject_number, experiment))
                else:
                    if ecg_class.anno_cables_exists:
                        data_anno = ecg_class.anno_cables
                        exist=True
                        analysed=analysed+1
                    else:
                        exist=False
                        print("No cables annotations exist for subject %d, %s exercise" %(subject_number, experiment))
                        
                #%% Detection
        
                ### Applying detector to each subject ECG data set then correct for mean detector
                # delay as referenced to annotated R peak position
                # Note: the correction factor for each detector doesn't need to be exact,
                # but centres the detection point for finding the nearest annotated match
                # It may/will be different for different subjects and experiments

                if exist==True: # only proceed if an annotation exists
                    detected_peaks = detectorfunc(data) # call detector class for current detector
                    interval_results = jmx_analysis.evaluate(detected_peaks, data_anno) # perform interval based analysis
                    
                    jitter=np.concatenate((jitter, interval_results[0])) # jitter results
                    missed.append(len(interval_results[1])) # missed beat results
                    extra.append(len(interval_results[2])) # extra detection results

                    
            # ^ LOOP AROUND FOR NEXT SUBJECT
                        
            # Save to csv files, all subjects concatenated/appended
            # https://stackoverflow.com/questions/27126511/add-columns-different-length-pandas/33404243
            jitter_list=jitter.tolist()
            missed_beats=missed
            extra_detections=extra
            jitter_df = pd.DataFrame({"jitter":jitter_list}) # since length different
            missed_extra_df = pd.DataFrame({"missed_beats":missed_beats, "extra_detections":extra_detections})
            categories_df = pd.concat([jitter_df, missed_extra_df], axis=1)
            file_name='results/'+detectorname+'_'+record_lead+'_'+experiment+'.csv'
            categories_df.to_csv(file_name, index=True)
            #print(new.head())
            
            # Concatenate all experiment results, for all subjects
            exec(name_jitter + ' = np.concatenate((' + name_jitter + ', jitter_list))') # jitter results
            exec(name_missed + ' = np.concatenate((' + name_missed + ', missed))') # jitter results
            exec(name_extra + ' = np.concatenate((' + name_extra + ', extra))') # jitter results
                        
        # ^ LOOP AROUND FOR NEXT EXPERIMENT
        
        
        # Add data for analysis by lead to (full array) 'data_det_lead' dictionary
        
        exec('data_det_lead["'+name_jitter+'"] = '+name_jitter)
        exec('data_det_lead["'+name_missed+'"] = '+name_missed)
        exec('data_det_lead["'+name_extra+'"] = '+name_extra)
        
        # Add stats for analysis by lead to dictionaries (SD, missed and extra mean values)
        # MAD is 'np.mean(abs(x - np.mean(x)))', but for a detected
        # interval=anno interval we can used: 'np.mean(abs(x))'
        # since matched interval difference=0
        exec(name_jitter+'_mad = np.mean(abs('+name_jitter+'))')
        exec(name_missed+'_mean = np.mean(np.asarray('+name_missed+'))')
        exec(name_extra+'_mean = np.mean('+name_extra+')')
        # Add stats for analysis to 'det_lead_stats' dictionary (SD, missed and extra mean dictionaries)
        exec('det_lead_stats["'+name_jitter+'_mad"] = '+name_jitter+'_mad')
        exec('det_lead_stats["'+name_missed+'_mean"] = '+name_missed+'_mean')
        exec('det_lead_stats["'+name_extra+'_mean"] = '+name_extra+'_mean')
        
        
        # det_lead_stats
        
        # for global calculations:
        exec(name_jitter_sub+ '= np.concatenate(('+name_jitter_sub+', ' + name_jitter +'))')
        exec(name_missed_sub+ '= np.concatenate(('+name_missed_sub+', ' + name_missed +'))')
        exec(name_extra_sub+ '= np.concatenate(('+name_extra_sub+', ' + name_extra +'))')        
        
    # ^ LOOP AROUND FOR NEXT LEAD
    
    exec('global_jitter=np.concatenate((global_jitter, ' + name_jitter_sub +'))')
    exec('global_missed=np.concatenate((global_missed, ' + name_missed_sub +'))')
    exec('global_extra=np.concatenate((global_extra, ' + name_extra_sub +'))')
    
# END DETECTOR LOOP

# Save data as csv files:
# https://www.edureka.co/community/65139/valueerror-arrays-same-length-valueerror-arrays-same-length
det_lead_df = pd.DataFrame.from_dict(data_det_lead, orient='index')
det_lead_df=det_lead_df.transpose() # transpose colums and rows
file_name=resultsdir+'/data_det_lead.csv'
det_lead_df.to_csv(file_name)

df_stats = pd.DataFrame(det_lead_stats, index=[0])
file_name=resultsdir+'/det_lead_stats.csv'
df_stats.to_csv(file_name)

if save_global_results==True:   
    # global_jitter_mad = np.mean(abs(global_jitter - np.mean(global_jitter))) (by definition)
    global_jitter_mad = np.mean(abs(global_jitter)) # since matched interval difference =0
    print('')
    print('global_jitter_mad = ', global_jitter_mad)
    
    global_missed_mean=np.mean(global_missed)
    print('')
    print('global_missed_mean = ', global_missed_mean)
    
    global_extra_mean=np.mean(global_extra)
    print('')
    print('global_extra_mean = ', global_extra_mean)
    
    # Save Global mean benchmark reference values 
    global_data={"Global_jitter_mad":global_jitter_mad, "Global_missed_mean":global_missed_mean, "Global_extra_mean":global_extra_mean}
    global_df = pd.DataFrame(global_data, index=[0])
    global_df.to_csv('saved_csv/global_results.csv')