import pygame
from random import random as rnd
from random import choice
import numpy as np
from copy import deepcopy
import time

import os

from islands import get_points

from quantumgraph import QuantumGraph


####################
num_civs = 5
# 'simulator', 'cambridge', 'rochester'
device = 'simulator'     
# None or 'static'
opponent_type = None           
years = 20
runs = 1
####################


L = 256
w,h = 3,3
radius = 5

pygame.init()
clock = pygame.time.Clock()

players = []

def random_colour():
    # return a random (r,g,b)
    def random_channel():
        return int( (0.2 + 0.6*rnd()) * 256 )
    return (random_channel(),random_channel(),random_channel())

def draw_height():
    # update screen with `height`
    for x in range(L):
        for y in range(L):
            h = height[x,y]
            rgb = ( 186*h+245*(1-h), 143*h+215*(1-h), 69*h+161*(1-h))
            pygame.draw.rect(screen, rgb, box[x,y])

def draw_cities():
    # update screen with `cities`
    for civ in range(num_civs):
        for city in cities[civ]:
            pygame.draw.rect(screen, (64,64,64), box[city])
            
def draw_territory():
    # update screen with `owner` info
    for x in range(L):
        for y in range(L):
            if owner[x,y]!=None:
                pygame.draw.rect(screen, colour[owner[x,y]], box[x,y])
    draw_border()
    
def draw_border():
    # update screen with `border` info
    for civ in range(num_civs):
        for neighbour in border[civ]:
            for pos in border[civ][neighbour]:
                pygame.draw.rect(screen, (26,26,26), box[pos]) # (144,129,86)

def get_influence(d):
    # return influence at distance `d` from a city
    return (d<2*radius)*( (d<radius) + 1/max(1,d)**2 )
                
def add_city(city, civ, remove=False):
    # update the following when a `city` is added to `civ` (or removed for `remove=True`):
    # `cities`, `city_owners`, `ruins`, `influence`
    (x,y) = city
    if remove:
        cities[civ].remove(city)
        city_owners.pop(city)
        ruins.append(city)
    else:
        cities[civ].append(city)
        city_owners[city] = civ
    for dx in range(-2*radius,2*radius+1):
        for dy in range(-2*radius,2*radius+1):
            (xx,yy) = (x+dx,y+dy)
            d = np.sqrt(dx**2+dy**2)
            inf = get_influence(d)
            if d<2*radius:
                if (xx,yy) in influence:
                    if civ in influence[xx,yy]:
                        if remove:
                            influence[xx,yy][civ] -= inf
                        else:
                            influence[xx,yy][civ] += inf
                    else:
                        influence[xx,yy][civ] = inf

def remove_city(city,civ):
    # runs `add_city` for `remove=True`
    add_city(city, civ, remove=True)
    
def update():
    
    for civ in range(num_civs):
        area[civ] = 0
        border[civ] = {}
        loss[civ] = 0
        gain[civ] = 0
            
    for x in range(L):
        for y in range(L):
            infs = {civ:influence[x,y][civ] for civ in influence[x,y]}
            if infs:
                civ = max(infs, key=infs.get)
                if owner[x,y]!=civ and owner[x,y]!=None:
                    loss[owner[x,y]] += 1
                    gain[civ] += 1
                owner[x,y] = civ
                if (x,y) in city_owners:
                    if city_owners[x,y]!=civ:
                        # city is protected from changing hands
                        if (x,y)==cities[city_owners[x,y]][0]:
                            owner[x,y] = city_owners[x,y]
                        else: # city changes hands
                            transfers[city_owners[x,y]] = civ
                            remove_city((x,y),city_owners[x,y])
                            add_city((x,y),civ)
    
    for civ in range(num_civs):
        area[civ] = 0
        border[civ] = {}

    for x in range(L):
        for y in range(L):
            civ = owner[x,y]
            if civ != None:
                area[civ] += 1
                for (dx,dy) in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    if (x+dx, y+dy) in owner:
                        neighbour = owner[x+dx, y+dy]
                        if neighbour!=civ:
                            if neighbour in border[civ]:
                                if (x,y) not in border[civ][neighbour]:
                                    border[civ][neighbour].append((x,y))
                            else:
                                border[civ][neighbour] = [(x,y)]
                                
    for civ in range(num_civs):
        # not on static or random opponent civs
        if (civ not in opponent) or (opponent_type not in ['static', 'random']):
            if civ in transfers:
                # set losing civ to max defense
                ai.set_bloch({'X':1,'Y':0,'Z':0}, civ, update=False)
                pair = [civ,transfers[civ]]
                if pair in ai.coupling_map or pair[::-1] in ai.coupling_map:
                    # as much as possible, set up a <XZ>=<ZX>=1 state between loser and winner
                    
                    ai.set_bloch({'X':1,'Y':0,'Z':0}, transfers[civ], update=False)
                    ai.qc.cz(transfers[civ],civ)
                    
                    
            else:
                if None in border[civ]:
                    frontier = len(border[civ][None])
                else:
                    frontier = 0
                if frontier>(loss[civ]+gain[civ]): # when frontiers are dominant, increase exploration
                    ai.set_bloch({'X':0,'Y':1,'Z':0}, civ, fraction=1/4, update=False)
                else:
                    if loss[civ]>gain[civ]:  # when losses are dominant, increase defense
                        ai.set_bloch({'X':1,'Y':0,'Z':0}, civ, fraction=min(1, loss[civ]/(np.pi*radius**2)), update=False)
                    else: # when gains are dominant, increase aggression
                        ai.set_bloch({'X':0,'Y':0,'Z':1}, civ, fraction=min(1, loss[civ]/(np.pi*radius**2)), update=False)           
    ai.update_tomography()
    
def get_surplus(civ):
    # for a `civ`, return the number of cities that can be added
    if len(cities[civ])==1:
        return 1
    else:
        return int( area[civ]/(np.pi*radius**2) - len(cities[civ]) )
    
                                
def choose_city(civ,tactic,neighbour=None):
    
    if tactic in ['Y','X']: # defend ('X') or explore ('Y')

        minf = np.inf
        min_city = []
        if neighbour in border[civ]:
            for pos in border[civ][neighbour]:
                if (height[pos]!=0) and (pos not in city_owners) and (pos not in ruins):
                    inf = influence[pos][civ]
                    if inf<minf:
                        minf = inf
                        min_city = [pos]
                    elif inf==minf:
                        min_city.append(pos)
            if min_city:
                city = choice(min_city)
            else:
                city = None
        else:
            city = None

    elif tactic=='Z': # attack ('Z')

        maxf = 0
        max_city = []
        if neighbour in border[civ]:
            for pos in border[civ][neighbour]:
                if (height[pos]!=0) and (pos not in city_owners) and (pos not in ruins):
                    if neighbour in influence[pos]:
                        inf = influence[pos][neighbour]
                        if inf>maxf and inf<=get_influence(radius/2):
                            maxf = inf
                            max_city = [pos]
                        elif inf==maxf:
                            max_city.append(pos)
        if max_city:
            city = choice(max_city)
        else:
            city = None
    
    elif tactic=='remove':
        
        maxf = 0
        city = None
        for pos in cities[civ][1:]:
            inf = influence[pos][civ]
            if inf>maxf:
                maxf = inf
                city = pos
    
    return city
   
def get_tactic(civ):
    
    # We need to look at the single qubit pauli expectation values
    # for the civ itself, as well as all the two qubit ones with
    # its neighbours.
    # For this we calculate expect[neighbour][`pauli`], the sum
    # of the single qubit expectation value for each `pauli` with
    # the two qubit expectation values with the given neighbour
    # for which the support on civ is `pauli`.
    
    if (civ in opponent) and (opponent=='random'):
        
        best_tactic = choice(['X','Y','Z'])
        target_neighbour = choice(list(border[civ].keys()))
        
    else:
    
        rho_civ = ai.get_bloch(civ)

        expect = {}
        for neighbour in border[civ]: 
            if neighbour!=None:  
                rho_both = ai.get_relationship(civ,neighbour)
                expect[neighbour] = {}
                for pauli_civ in ['X','Y','Z']:
                    expect[neighbour][pauli_civ] = rho_civ[pauli_civ]
                    for pauli_ngbhr in ['X','Y','Z']:
                        expect[neighbour][pauli_civ] += rho_both[pauli_civ+pauli_ngbhr]

        # Of all these, the maximum is value is determined, as well as the
        # corresponding tactic and neighbour.
        best_tactic,target_neighbour = 'Y',None
        max_expect = -1
        for neighbour in expect: 
            for tactic in expect[neighbour]:
                if expect[neighbour][tactic]>max_expect:
                    max_expect = expect[neighbour][tactic]
                    best_tactic,target_neighbour = tactic, neighbour
                
    if best_tactic=='Y':
        target_neighbour = None

    return best_tactic,target_neighbour
    
def make_move(civ):
    
    # determine a tactic and a target neighbour, based on civ state
    tactic,neighbour = get_tactic(civ)
    city = choose_city(civ,tactic,neighbour)
    
    # see if the civ has capacity for a new city
    surplus = get_surplus(civ)
    
    # if there is no capacity, remove a city
    if (surplus<1) and (tactic in ['X','Y','Z']):
        old_city = choose_city(civ,'remove')
        if old_city:
            remove_city(old_city,civ)
            surplus += 1
      
    # if there is now capacity...
    if surplus>0:
        # and the proposed city is valid, add it
        if (city!=None):
            add_city(city,civ)
        # otherwise, attempt to explore
        else:
            tactic = 'Y'
            neighbour = None
            city = choose_city(civ,tactic,neighbour)
            if city:
                add_city(city,civ)
       
    return tactic,neighbour,city

########################################################################################
                                
# initialize screen
screen = pygame.display.set_mode((L*w,L*h))

# set up the objects used for the cells
box = {}
for x in range(L):
    for y in range(L):
        box[x,y] = pygame.Rect(x*w,y*w,w,h)

# make the height map
height = {}
for x in range(L):
    for y in range(L):
        height[x,y] = 1

colour = [ random_colour() for _ in range(num_civs) ]

h = 0
for _ in range(runs):
    
    folder = str(num_civs) +'_'+ device +'_'
    if opponent_type:
        folder += opponent_type + '_'
    else:
        folder += 'None_'
    folder += str(int(time.time()))
    os.mkdir('maps/'+folder)
    
    points, coupling_map, half = get_points(L)
    
    if opponent_type:
        h = (h+1)%2
        opponent = half[h]
    else:
        opponent = []        

    ai = QuantumGraph(num_civs,device=device)
    for civ in range(num_civs):
        ai.set_bloch({'X':1,'Y':1,'Z':1}, civ, update=False)

    owner = {}
    influence = {}
    for x in range(L):
        for y in range(L):
            owner[x,y] = None
            influence[x,y] = {}

    cities = [[] for _ in range(num_civs)]
    city_owners = {}
    for civ in range(num_civs):
        add_city(points[civ],civ)

    ruins = []

    loss = [0 for _ in range(num_civs)]
    gain = [0 for _ in range(num_civs)]

    done = False
    
    transfers = {}

    for year in range(years):

        print(year)

        last_transfers = {civ:transfers[civ] for civ in transfers}
        transfers = {}
        
        area = {civ:0 for civ in range(num_civs)}
        border = [{} for _ in range(num_civs)] 
        update()

        moves = {}
        for civ in range(num_civs):
            moves[civ] = make_move(civ)

        draw_height()
        draw_territory()
        draw_cities()
        pygame.display.flip()

        pygame.image.save(screen, 'maps/'+folder+'/year_'+str(year)+'.png')

        dump = {'moves':moves, 'transfers':transfers, 'area':area, 'opponent':opponent}
        with open('maps/'+folder+'/data.txt', 'a') as file:
            file.write(str(dump)+'\n')


        # give player the option to quit
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    done = True