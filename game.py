import random
import pickle
import time
import os

from qavrai import World
from quantumgraph import QuantumGraph
from ai import Governments

from islands import get_points


# get the parameters to define this instance of the game
from params import *


# tools for the player interface

def setup():
    text = 'The Gods commanded all nations to found new cities and expand.\n\n'\
                +'By clever placement of our new cities, we can seek to gain an advantage over our neighbours. '\
                +'Parliament will make suggestions, but it is up to you to decide!'
    print(text)
    
def get_coord(image, advice, world):
    
    text = 'Where would you like to place a city, Your Grace? Just give us coordinates and it will be done!\n\n'\
        + 'Parliament suggests the location ' + str(advice) + '.'
    invalid = 'Forgive me, Your Grace. That does not appear to be a valid location.\n\nAllow me to try asking again.\n'
    
    chosen = False
    while chosen==False:
        image.show()
        print(text)
        
        try:
            coords = eval(input())
            print()
        except:
            print(invalid)
            
        if world.owner[coords]==world.owner[advice]:
            print('Thank you, Your Grace.\n')
            chosen = True
        else:
            print(invalid)

    return coords


# tools for saving and loading

class Parameters():
    def __init__(self,folder,player,opponent,years):
        self.folder = folder
        self.player = player
        self.opponent = opponent
        self.years = years
        self.year = 0

def save_game(params,world,graph,govs):
    pickle.dump(params, open('current_save/params.p','wb'))
    pickle.dump(world, open('current_save/world.p','wb'))
    pickle.dump(graph, open('current_save/graph.p','wb'))
    pickle.dump(govs, open('current_save/govs.p','wb'))
    
    
def load_game():
    params = pickle.load(open('current_save/params.p','rb'))
    world = pickle.load(open('current_save/world.p','rb'))
    graph = pickle.load(open('current_save/graph.p','rb'))
    govs = pickle.load(open('current_save/govs.p','rb'))
    return params, world, graph, govs

def delete_save():
    os.remove('current_save/params.p')
    os.remove('current_save/world.p')
    os.remove('current_save/graph.p')
    os.remove('current_save/govs.p')
    

# load game if one is ongoing, set up a new one if not

try:
    
    params,world,graph,govs = load_game()
    
except:
    
    folder = str(num_civs) +'_'+ device +'_'
    if opponent:
        folder += 'opponent_'
    else:
        folder += 'None_'
    folder += str(int(time.time()))
    os.mkdir('histories/'+folder)
    
    # set up the objects that run the simulation
    params = Parameters(folder,player,opponent,years)
    world = World(num_civs,L)
    graph = QuantumGraph(num_civs,device=device)
    govs = Governments(world,graph)

    # place initial cities
    points, coupling_map, half = get_points(L)
    for civ in range(num_civs):
        city = points[civ]
        world.add_city(city,civ)
        world.update()

    save_game(params,world,graph,govs)


# run the game
while params.year < params.years:
    
    params,world,graph,govs = load_game()
    
    moves = {}
    for civ in range(world.num_civs):
                
        # determine how many cities can be placed this turn
        surplus = world.get_surplus(civ)

        # work out which cities to place (or remove) and do it
        for _ in range(surplus):
                
            # ai choses city to place
            city,tactic,neighbour = govs.choose_city(civ)
            if civ==params.player:
                image = world.make_map(civ=civ)
                advice = city
                city = get_coord(image,advice,world)

            # add new city
            if city:
                world.add_city(city,civ)
                
        else:
            for _ in range(-surplus):
                
                # ai choses city to remove
                city,tactic,neighbour = govs.choose_city(civ,tactic='remove')
                
                # remove it
                if city:
                    world.remove_city(city)
        
        # record the move
        moves[civ] = tactic,neighbour,city
                    
    # update the simulation
    loss, gain, transfers = world.update()
    govs.update(loss,gain,transfers)
    
    # save map
    world.make_map().save('histories/'+params.folder+'/year_'+str(params.year)+'.png')
    # save details of what happened this year
    dump = {'moves':moves, 'transfers':transfers, 'area':world.area, 'opponent':params.opponent}
    with open('histories/'+params.folder+'/data.txt', 'a') as file:
        file.write(str(dump)+'\n')
    # iterate year
    params.year += 1
    # save game objects as they will be at the beginning of next year
    save_game(params,world,graph,govs)

# once it is over, delete the save
delete_save()