#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
from ecgdetectors import Detectors
import json
import sys

experiment_names = ['sitting','maths','walking','hand_bike','jogging']

einth = 'einthoven_ii'
cs = 'chest_strap_V2_V1'

detectors = Detectors()
det_names = [i[1].__name__ for i in detectors.get_detector_list()]

resultsdir = "results"

alpha = 0.05

minja = 90 # %

def get_ja(detector_name, leads, experiment):
    f = open(resultsdir+"/ja_"+detector_name+".json","r")
    js = f.read()
    data = json.loads(js)
    s = []
    for i in data[leads][experiment]:
        if i["ja"]:
            s.append(i["ja"]*100)
    return np.array(s)


def get_result(det, leads):
    
    m = []
    s = []
    for e in experiment_names:
        m.append(np.mean(get_ja(det, leads, e)))
        s.append(np.std(get_ja(det, leads, e)))

    return m,s


def print_stat(p):
    if p == None:
        print('--- & ',end='')
        return
    s = ""
    if p < alpha:
        s = "*"
    print('{:03.2f}{} & '.format(p,s),end='')

    
def calc_stats(det,leads):
    print("Stats:",det, leads)
    print("      & ",end='')
    for e in experiment_names:
        print(e," & ",end='')
    print("\\\\")
    for e in experiment_names:
        r1 = get_ja(det, leads, e)
        t,p = stats.ttest_1samp(r1,minja,alternative='greater')
        print_stat(p)
    print()


def triple_plot(data1, std1, data2, std2, data3, std3, y_label, legend1, legend2, legend3, title=None):
    fig, ax = plt.subplots()
    x_pos = np.arange(len(experiment_names))

    fig.set_size_inches(10, 7)
    width = 0.25
    rects1 = ax.bar(x_pos, data1, width, yerr=std1, alpha=0.5, ecolor='black', capsize=10)
    rects2 = ax.bar(x_pos+width, data2, width, yerr=std2, alpha=0.5, ecolor='black', capsize=10)
    rects3 = ax.bar(x_pos+width*2, data3, width, yerr=std3, alpha=0.5, ecolor='black', capsize=10)
    ax.set_ylim([0,150])
    ax.set_ylabel(y_label)
    ax.set_xlabel('Detector')
    ax.set_xticks(x_pos + width / 2)
    ax.set_xticklabels(experiment_names)
    ax.legend((rects1[0], rects2[0], rects3[0]), (legend1, legend2, legend3))

    if title!=None:
        ax.set_title(title)

    plt.tight_layout()

    return rects1, rects2


det1 = det_names[0]
det2 = det_names[3]
det3 = det_names[7]

print("Det:",det1,det2,det3)

det1_avg,det1_std = get_result(det1, einth)
det2_avg,det2_std = get_result(det2, einth)
det3_avg,det3_std = get_result(det3, einth)

triple_plot(det1_avg,det1_std,
            det2_avg,det2_std,
            det3_avg,det3_std,
            'JA (%)', det1, det2, det3, "Einthoven")


calc_stats(det1, einth)
calc_stats(det2, einth)
calc_stats(det3, einth)

plt.show()
