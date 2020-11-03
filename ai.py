import numpy as np
from random import choice

class Governments():
    
    def __init__(self,world,graph,static=[]):
        
        self.world = world
        self.graph = graph
        self.static = static
        
        for civ in range(world.num_civs):
            graph.set_bloch({'X':1,'Y':1,'Z':1}, civ, update=False)
        graph.update_tomography()

    def choose_city(self,civ,tactic=None):

        world = self.world
        graph = self.graph
        
        '''
        Step 1: Decide on a tactic

        We need to look at the single qubit pauli expectation values
        for the civ itself, as well as all the two qubit ones with
        its neighbours.

        For this we calculate expect[neighbour][`pauli`], the sum
        of the single qubit expectation value for each `pauli` with
        the two qubit expectation values with the given neighbour
        for which the support on civ is `pauli`.

        This step is mostly skipped if tactic has already been chosen
        to be random or removal.
        '''

        if tactic in ['random', 'remove']:
            neighbour = None

        else:

            rho_civ = graph.get_bloch(civ)

            expect = {}
            for neighbour in world.border[civ]: 
                if neighbour!=None:  
                    rho_both = graph.get_relationship(civ,neighbour)
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
            tactic = best_tactic

        if tactic=='Y':
            neighbour = None


        '''
        Step 2: Decide on the city position

        We now have a tactic and a neighbour to apply it to.
        With this we determine the optimal city placement. 
        '''

        if tactic in ['Y','X']: # defend ('X') or explore ('Y')

            minf = np.inf
            min_city = []
            # if the neighbour shares a border
            if neighbour in world.border[civ]:
                # look at all points along the civ's border with neighbour
                for pos in world.border[civ][neighbour]:
                    # for valid places to put a city
                    if (self.world.height[pos]!=0) and (pos not in world.city_owners) and (pos not in world.ruins):
                        # find points of the civ's minimum influence and record them
                        if civ in world.influence[pos]:
                            inf = world.influence[pos][civ]
                        else:
                            # this is a pretty bad situation!
                            inf = 0
                        if inf<minf:
                            minf = inf
                            min_city = [pos]
                        elif inf==minf:
                            min_city.append(pos)

                # choose new city location from this list
                if min_city:
                    city = choice(min_city)
                # reset tactic to random if no valid positions exist
                else:
                    tactic = 'random'
            # reset tactic to random if the neighbour does not share a border
            else:
                tactic = 'random'

        elif tactic=='Z': # attack ('Z')

            maxf = 0
            max_city = []
            if neighbour in world.border[civ]:
                # look at all points along the civ's border with neighbour
                for pos in world.border[civ][neighbour]:
                    # for valid places to put a city
                    if (self.world.height[pos]!=0) and (pos not in world.city_owners) and (pos not in world.ruins):
                        # find points of the neighbour's maximum influence and record them
                        # points at which the civ's own influence is at least that of the
                        # neighbour are not included
                        if neighbour in world.influence[pos] and civ in world.influence[pos]:
                            inf = world.influence[pos][neighbour]
                            own_inf = world.influence[pos][civ]
                            if inf>maxf and inf<=own_inf:
                                maxf = inf
                                max_city = [pos]
                            elif inf==maxf:
                                max_city.append(pos)
            # choose new city location from this list
            if max_city:
                city = choice(max_city)
            # reset tactic to random if no valid positions exist
            else:
                tactic = 'random'

        elif tactic=='remove':

            # choose to remove the city at which the civ's influence is maximum
            maxf = 0
            city = None
            for pos in world.cities[civ][1:]:
                inf = world.influence[pos][civ]
                if inf>maxf:
                    maxf = inf
                    city = pos


        # if no city has yet been chosen, choose a random position
        if tactic=='random':

            # first try a random border position
            border = []
            for neighbour in world.border[civ]:
                for pos in world.border[civ][neighbour]:
                    if (self.world.height[pos]!=0) and (pos not in world.city_owners) and (pos not in world.ruins):
                        border.append(pos)
            if border:
                city = choice(border)
            else:
                # then try a random position from the whole nation
                nation = []
                for pos in world.owner:
                    if (self.world.height[pos]!=0) and (world.owner[pos]==civ) and (pos not in world.city_owners) and (pos not in world.ruins):
                        nation.append(pos)
                if nation:
                    city = choice(nation) 
                else:
                    # if all else fails, give up!
                    city = None

        '''
        Step 3: Return all the info
        '''

        return city,tactic,neighbour
    
    
    def update(self, loss, gain, transfers):
        
        world = self.world
        graph = self.graph
        
        for civ in range(world.num_civs):
            # if a civ has lost a city
            if civ in transfers:
                # unless it is a static civ, set it to max defense
                if civ not in self.static:
                    graph.set_bloch({'X':1,'Y':0,'Z':0}, civ, update=False)
                pair = [civ,transfers[civ]]
                # if either the loser or winner is not static
                if pair[0] not in self.static or pair[1] not in self.static:
                    # and if they are connected by the coupling map
                    if pair in graph.coupling_map or pair[::-1] in graph.coupling_map:
                        # as much as possible, set up a <XZ>=<ZX>=1 state between loser and winner
                        graph.set_relationship({'XZ':+1,'ZX':+1},civ,transfers[civ],fraction=1/2)
                    
            # otherwise change state based on territory transfers        
            else:
                # only do anything if the civ is not static
                if civ not in self.static:
                    if None in world.border[civ]:
                        frontier = len(world.border[civ][None])
                    else:
                        frontier = 0
                    # when frontiers are dominant, increase exploration
                    if frontier>(loss[civ]+gain[civ]):
                        state = {'X':0,'Y':1,'Z':0}
                        fraction = 1/2
                    else:
                        # when losses are dominant, increase defense
                        if loss[civ]>gain[civ]:
                            state = {'X':1,'Y':0,'Z':0}
                            fraction = loss[civ]/(np.pi*world.r**2)
                        # when gains are dominant, increase aggression
                        else:
                            state = {'X':0,'Y':0,'Z':1}
                            fraction = gain[civ]/(np.pi*world.r**2)
                    graph.set_bloch(state, civ, fraction=fraction, update=False)
    
        graph.update_tomography()