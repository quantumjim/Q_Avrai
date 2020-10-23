import numpy as np

def get_points (size):

    coupling_map = [[0, 1], [0, 5], [1, 0], [1, 2], [2, 1], [2, 3], [3, 2], [3, 4], [4, 3], [4, 6], [5, 0], [5, 9], [6, 4], [6, 13], [7, 8], [7, 16], [8, 7], [8, 9], [9, 5], [9, 8], [9, 10], [10, 9], [10, 11], [11, 10], [11, 12], [11, 17], [12, 11], [12, 13], [13, 6], [13, 12], [13, 14], [14, 13], [14, 15], [15, 14], [15, 18], [16, 7], [16, 19], [17, 11], [17, 23], [18, 15], [18, 27], [19, 16], [19, 20], [20, 19], [20, 21], [21, 20], [21, 22], [21, 28], [22, 21], [22, 23], [23, 17], [23, 22], [23, 24], [24, 23], [24, 25], [25, 24], [25, 26], [25, 29], [26, 25], [26, 27], [27, 18], [27, 26], [28, 21], [28, 32], [29, 25], [29, 36], [30, 31], [30, 39], [31, 30], [31, 32], [32, 28], [32, 31], [32, 33], [33, 32], [33, 34], [34, 33], [34, 35], [34, 40], [35, 34], [35, 36], [36, 29], [36, 35], [36, 37], [37, 36], [37, 38], [38, 37], [38, 41], [39, 30], [39, 42], [40, 34], [40, 46], [41, 38], [41, 50], [42, 39], [42, 43], [43, 42], [43, 44], [44, 43], [44, 45], [44, 51], [45, 44], [45, 46], [46, 40], [46, 45], [46, 47], [47, 46], [47, 48], [48, 47], [48, 49], [48, 52], [49, 48], [49, 50], [50, 41], [50, 49], [51, 44], [52, 48]]

    half = {}
    half[0] = [0,2,4,7,9,11,13,15,19,21,23,25,27,30,32,34,36,38,42,44,46,48,50]
    half[1] = []
    for j in range(53):
        if j not in half[0]:
            half[1].append(j)
    
    v = 0.5
    diag_x = 1
    diag_y = 0.37
    tail = 1
    
    border = size/np.sqrt(53)

    hexagons = {
        (0,0):                     [2, 1, 3, 0, 4, 5, 6, 9, 13,10,12,11],
        (-2*diag_x,-2*diag_y-2*v): [9, 8, 10,7, 11,16,17,19,23,20,22,21],
        (2*diag_x,-2*diag_y-2*v):  [13,12,14,11,15,17,18,23,27,24,26,25],
        (0,-4*diag_y-4*v):         [23,22,24,21,25,28,29,32,36,33,35,34],
        (-2*diag_x,-6*diag_y-6*v): [32,31,33,30,34,39,40,42,46,43,45,44,51],
        (+2*diag_x,-6*diag_y-6*v): [36,35,37,34,38,40,41,46,50,47,49,48,52],
    }

    points = [ (-0.1,-0.1) for j in range(53)]

    for (diag_yx,diag_yy) in hexagons:
        points[hexagons[diag_yx,diag_yy][0]] = (diag_yx,diag_yy)
        points[hexagons[diag_yx,diag_yy][1]] = (diag_yx-diag_x,diag_yy-diag_y)
        points[hexagons[diag_yx,diag_yy][2]] = (diag_yx+diag_x,diag_yy-diag_y)
        points[hexagons[diag_yx,diag_yy][3]] = (diag_yx-2*diag_x,diag_yy-2*diag_y)
        points[hexagons[diag_yx,diag_yy][4]] = (diag_yx+2*diag_x,diag_yy-2*diag_y)
        points[hexagons[diag_yx,diag_yy][5]] = (diag_yx-2*diag_x,diag_yy-2*diag_y-v)
        points[hexagons[diag_yx,diag_yy][6]] = (diag_yx+2*diag_x,diag_yy-2*diag_y-v)
        points[hexagons[diag_yx,diag_yy][7]] = (diag_yx-2*diag_x,diag_yy-2*diag_y-2*v)
        points[hexagons[diag_yx,diag_yy][8]] = (diag_yx+2*diag_x,diag_yy-2*diag_y-2*v)
        points[hexagons[diag_yx,diag_yy][9]] = (diag_yx-diag_x,diag_yy-3*diag_y-2*v)
        points[hexagons[diag_yx,diag_yy][10]] = (diag_yx+diag_x,diag_yy-3*diag_y-2*v)
        points[hexagons[diag_yx,diag_yy][11]] = (diag_yx,diag_yy-4*diag_y-2*v)
        try:
            points[hexagons[diag_yx,diag_yy][12]] = (diag_yx,diag_yy-4*diag_y-2*v-tail)
        except:
            pass
        
    min_x = size
    min_y = size
    for pos in points:
        min_x = min(min_x,pos[0])
        min_y = min(min_y,pos[1])
    points = [ (x-min_x, y-min_y) for (x,y) in points ]
       
    max_x = -size
    max_y = -size
    for pos in points:
        max_x = max(max_x,pos[0])
        max_y = max(max_y,pos[1])
    points = [ (x/max_x, y/max_y) for (x,y) in points ]
    
    points = [ (int(border+x*(size-2*border)), int(border+y*(size-2*border))) for (x,y) in points ]
    
    return points, coupling_map, half