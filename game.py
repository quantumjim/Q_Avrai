import random
import pickle
import time
import os

from qavrai import World
from quantumgraph import QuantumGraph
from ai import Governments

from islands import get_points

# tools for the player interface
    
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
    def __init__(self,folder,player,static,years):
        self.folder = folder
        self.player = player
        self.static = static
        self.years = years
        self.year = 0

def save_game(params,world,graph,govs,folder='current_save',file=''):
    pickle.dump(params, open(folder+'/params'+file+'.p','wb'))
    pickle.dump(world, open(folder+'/world'+file+'.p','wb'))
    pickle.dump(graph, open(folder+'/graph'+file+'.p','wb'))
    pickle.dump(govs, open(folder+'/govs'+file+'.p','wb'))
    
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

    
def run_game(num_civs=28, player=None, L=100, years=20, device='simulator', static=0, newgame=True, theta=0):
    
    # load game if one is ongoing
    if newgame:
        
        try:
            folder = 'data/'+str(num_civs)+'_'+device+'_'+str(static)+'_'+str(int(time.time()))
        except:
            folder = 'data/'+str(num_civs)+'_?_'+str(static)+'_'+str(int(time.time()))
        os.mkdir(folder)
        
        points, coupling_map, partition, height = get_points(L,num_civs,theta=theta)
        
        # set up the objects that run the simulation
        params = Parameters(folder,player,partition[static],years)
        world = World(num_civs,L,height=height)
        graph = QuantumGraph(num_civs,device=device)
        govs = Governments(world,graph,partition[static])

        # place initial cities
        
        for civ in range(num_civs):
            city = points[civ]
            world.add_city(city,civ)
            world.update()

        save_game(params,world,graph,govs)
    else:
        params,world,graph,govs = load_game()


    # run the game
    while params.year < params.years:

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
        world.make_map().save(params.folder+'/year_'+str(params.year)+'.png')
        # save details of what happened this year
        dump = {'moves':moves, 'transfers':transfers, 'area':world.area, 'static':params.static}
        with open(params.folder+'/data.txt', 'a') as file:
            file.write(str(dump)+'\n')
        save_game(params,world,graph,govs,folder=params.folder,file='_'+str(params.year))
        # iterate year
        params.year += 1
        # save game objects as they will be at the beginning of next year to current save folder
        save_game(params,world,graph,govs)

        

    # once the game is over, delete the save
    delete_save()