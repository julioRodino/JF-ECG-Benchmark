#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt

# Plots the map which maps jitter in seconds to %

import ja_analysis

jitter = np.linspace(0,100E-3,100)

ja = []

for j in jitter:
    ja.append(ja_analysis.mapping_jitter(j / ja_analysis.norm_jitter))

plt.plot(jitter,ja)
plt.xlabel("jitter / s")
plt.ylabel("score")
plt.show()
