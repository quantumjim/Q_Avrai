import numpy as np
import quantumblur as qb
import random

def get_points (size, num_civs, r=1.2, theta=0.25, thresh=0.55):

    # coupling map for 27 qubit devices (Montreal, Paris, etc)
    coupling_map = [[0, 1], [1, 0], [1, 2], [1, 4], [2, 1], [2, 3], [3, 2], [3, 5], [4, 1], [4, 7], [5, 3], [5, 8], [6, 7], [7, 4], [7, 6], [7, 10], [8, 5], [8, 9], [8, 11], [9, 8], [10, 7], [10, 12], [11, 8], [11, 14], [12, 10], [12, 13], [12, 15], [13, 12], [13, 14], [14, 11], [14, 13], [14, 16], [15, 12], [15, 18], [16, 14], [16, 19], [17, 18], [18, 15], [18, 17], [18, 21], [19, 16], [19, 20], [19, 22], [20, 19], [21, 18], [21, 23], [22, 19], [22, 25], [23, 21], [23, 24], [24, 23], [24, 25], [25, 22], [25, 24], [25, 26], [26, 25]]

    # partitions for these devices ('a' and 'b' represent two bipartitions)
    half = [0,2,4,5,6,9,10,11,13,15,16,17,20,21,22,24,26]
    partition = {'none':[], 'a':[], 'b':[]}
    partition['all'] = list(range(num_civs))
    for j in range(num_civs):
        if j in half:
            partition['a'].append(j)
        else:
            partition['b'].append(j)
    
    # postions for qubits such that neighbours are equidistant and nicely placed in the map
    points = {0: (0, 2), 1: (1, 3), 2: (0, 4), 3: (1, 5), 4: (2, 2), 5: (2, 6), 6: (3, 0), 7: (3, 1), 8: (3, 7), 9: (3, 8), 10: (4, 2), 11: (4, 6), 12: (5, 3), 13: (5, 4), 14: (5, 5), 15: (6, 2), 16: (6, 6), 17: (7, 0), 18: (7, 1), 19: (7, 7), 20: (7, 8), 21: (8, 2), 22: (8, 6), 23: (9, 3), 24: (10, 4), 25: (9, 5), 26: (10, 6)}
    scale = size/(10+2*r)
    for civ in points:
        x,y = points[civ]
        points[civ] = (int(scale*(x+r)),int(scale*(y+r+1)))
        
    # height values for the terrain (0 or sea and 1 for land)
    # first with just a circle of radius r around each point
    height = {}
    for x in range(size):
        for y in range(size):
            height[x,y] = 0
            min_dist = np.Inf
            for (xx,yy) in points.values():
                min_dist = min(np.sqrt((x-xx)**2+(y-yy)**2),min_dist)
            if min_dist<r*scale:
                height[x,y] = 1
    # and then a quantum blur to spice things up
    if theta!=0:
        qc = qb.height2circuit(height)
        for qubit in range(qc.num_qubits):
            qc.rx(theta*(1+random.random())/2,qubit)
        height = qb.circuit2height(qc)
    for (x,y) in height:
        height[x,y] = int(height[x,y]>thresh)
    
    return points, coupling_map, partition, height