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
    f = open(resultsdir+"/jf_"+detector_name+".json","r")
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


def multi_plot(data, std, y_label, legend, title=None):
    fig, ax = plt.subplots()
    x_pos = np.arange(len(experiment_names))

    fig.set_size_inches(10, 7)
    width = 1.0 / (len(data)+1)
    rects = []
    for i in range(len(data)):
        rects.append(ax.bar(x_pos+width*i, data[i], width, yerr=std[i], alpha=0.5, ecolor='black', capsize=10))
    ax.set_ylim([0,150])
    ax.set_ylabel(y_label)
    ax.set_xlabel('Experiment')
    ax.set_xticks(x_pos + width / 2)
    ax.set_xticklabels(experiment_names)
    ax.legend(rects, legend)

    if title!=None:
        ax.set_title(title)

    plt.tight_layout()

dets = []
dets.append(det_names[3])
dets.append(det_names[0])
dets.append(det_names[7])
dets.append(det_names[6])

print("Dets:",dets)

leads = einth
if len(sys.argv) > 1:
    leads = cs
else:
    print("You can switch to chest strap by adding anything as an argument for example: '{} cs'.".format(sys.argv[0]))

print("Leads:",leads)

avg = []
std = []
for d in dets:
    a,s = get_result(d, leads)
    avg.append(a)
    std.append(s)

multi_plot(avg,std,
        'JA (%)', dets, leads)


for d in dets:
    calc_stats(d, leads)

plt.show()
