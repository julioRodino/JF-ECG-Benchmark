#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Calculates the individual jitters, accuracy and JA values.
Outputs the averages and stores the individual ones in a file.
plot with gnuplot with:
gnuplot> plot "norm_calc.tsv" using 1 with lines, "norm_calc.tsv" using 3 with lines 
to plot the momentary ja values and the current average at that point.
gnuplot> plot "norm_calc.tsv" using 2 with lines, "norm_calc.tsv" using 4 with lines 
To plot the accuracy and the average.
"""

import sys
import os
import numpy as np
import json
from ecg_gudb_database import GUDb
from ecgdetectors import Detectors
from hrv import HRV
import pathlib # For local file use
from multiprocessing import Process

# The JA analysis for a detector
import ja_analysis

# directory where the results are stored
resultsdir = "results"

try:
    os.mkdir(resultsdir)
except OSError as error:
    pass

# Get the sampling rate
fs = GUDb.fs

detectors = Detectors(fs) # Initialise detectors
hrvcalc = HRV(fs)

current_dir = pathlib.Path(__file__).resolve()

recording_leads = "einthoven_ii"
experiment = "sitting"

ja_results = np.empty((0,2))

f = open("norm_calc.tsv","w")

for detector in detectors.detector_list:

    detectorname = detector[1].__name__
    detectorfunc = detector[1]
    
    rmssd_results = np.array([])

    print("Processing:",detector[0])

    for subject_number in range(0, 25): # loop for all subjects

        print("Analysing subject {}, {}, {}, {}".format(subject_number, experiment, recording_leads, detector[0]))

        # creating class which loads the experiment

        # For online GUDB access
        ecg_class = GUDb(subject_number, experiment) 

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

        data = einthoven_ii

        if ecg_class.anno_cables_exists:
            data_anno = ecg_class.anno_cables
            exist=True

        #%% Detection

        ### Applying detector to each subject ECG data set then correct for mean detector
        # delay as referenced to annotated R peak position
        # Note: the correction factor for each detector doesn't need to be exact,
        # but centres the detection point for finding the nearest annotated match
        # It may/will be different for different subjects and experiments

        if exist==True: # only proceed if an annotation exists
            detected_peaks = detectorfunc(data) # call detector class for current detector
            interval_results = ja_analysis.evaluate(detected_peaks, data_anno, fs, len(data)) # perform interval based analysis
            ja = np.array([interval_results[ja_analysis.key_jitter],
                            interval_results[ja_analysis.key_accuracy],
                            
            ])
            ja_results = np.vstack( (ja_results,ja) )
            ja_avg = np.average(ja_results,axis=0)
            s = ja_analysis.score(ja_avg[0],ja_avg[1])
            rmssd = hrvcalc.RMSSD(data_anno)
            rmssd_results = np.append( rmssd_results, rmssd )
            rmssd_avg = np.average(rmssd_results)
            rmssd_std = np.std(rmssd_results)
            print("Current avg: J = {:1.6f} sec, A = {:1.6f}, JA = {:1.4f}, RMSSD = {:1.4f}+/-{:1.4f}".format(ja_avg[0],ja_avg[1],s,rmssd_avg,rmssd_std))
            f.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(ja[0],ja[1],rmssd,ja_avg[0],ja_avg[1],rmssd_avg))
            f.flush()
print("FINAL Avg: J = {:1.6f} sec, A = {:1.6f}".format(ja_avg[0],ja_avg[1]))
f.close()
