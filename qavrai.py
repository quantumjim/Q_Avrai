import numpy as np
import random
from PIL import Image
import colorsys

import matplotlib 
import matplotlib.pyplot as plt 
import matplotlib.image as img 


class World():
    
    def __init__(self,num_civs,L,r=5):
        
        self.L = L
        self.r = r
        self.num_civs = num_civs
        
        # for each point on the map:
        # * which civ owns it
        # * the influence each civ has over it
        self.owner = {}
        self.influence = {}
        for x in range(L):
            for y in range(L):
                self.owner[x,y] = None
                self.influence[x,y] = {}
                
                
        # for each civ, a list of its cities (as coordinates)
        self.cities = {civ:[] for civ in range(self.num_civs)}
        # for each city, the civ that owns it
        self.city_owners = {}

        # a list of ruins where cities once lay
        self.ruins = []
        
        self.area = {civ:0 for civ in range(self.num_civs)}
        self.border = {civ:{} for civ in range(self.num_civs)}
        
        self.colors = []
        self.city_colors = []
        for j in range(self.num_civs):
            hue = j/num_civs
            rgb = [round(255*j) for j in colorsys.hsv_to_rgb(hue,1/3,1)]
            self.colors.append(tuple(rgb))
            rgb = [round(255*j) for j in colorsys.hsv_to_rgb(hue,1,2/3)]
            self.city_colors.append(tuple(rgb))
            
        
    def _get_influence(self,d):
        # return influence at distance `d` from a city
        return (d<2*self.r)*( (d<self.r) + 1/max(1,d)**2 )
        
    def add_city(self, city, civ, remove=False):
        # when adding or removing a city, this updates the attributes
        # `cities`, `city_owners`, `ruins` and `influence`
        (x,y) = city
        if remove:
            while city in self.cities[civ]:
                self.cities[civ].remove(city)
            while city in self.city_owners:
                self.city_owners.pop(city)
            self.ruins.append(city)
        else:
            self.cities[civ].append(city)
            self.city_owners[city] = civ
        # loop over all points within twice the radius
        for dx in range(-2*self.r,2*self.r+1):
            for dy in range(-2*self.r,2*self.r+1):
                (xx,yy) = (x+dx,y+dy)
                d = np.sqrt(dx**2+dy**2)
                if d<2*self.r:
                    # determine the influence
                    inf = self._get_influence(d)
                    if (xx,yy) in self.influence:
                        # add (or remove) the influence for the new city
                        if civ in self.influence[xx,yy]:
                            if remove:
                                self.influence[xx,yy][civ] -= inf
                                if self.influence[xx,yy][civ]<=0:
                                    while civ in self.influence[xx,yy]:
                                        self.influence[xx,yy].pop(civ)
                            else:
                                self.influence[xx,yy][civ] += inf
                        else:
                            self.influence[xx,yy][civ] = inf
                            
    def remove_city(self,city):
        # runs `add_city` for `remove=True`
        civ = self.city_owners[city]
        self.add_city(city, civ, remove=True)
        
    def get_surplus(self,civ):
        # for a `civ`, return the number of cities that can be added
        if len(self.cities[civ])==1 or None in self.border[civ]:
            return 1
        else:
            return int( self.area[civ]/(np.pi*self.r**2) - len(self.cities[civ]) )
        
    def update(self):
        # updates everything after the addition or removal of cities
        # also returns how the losses, gains and transfers for each civ due to this upate
        
        loss = {civ:0 for civ in range(self.num_civs)}
        gain = {civ:0 for civ in range(self.num_civs)}
        transfers = {}

        for x in range(self.L):
            for y in range(self.L):
                infs = {civ:self.influence[x,y][civ] for civ in self.influence[x,y]}
                if infs:
                    civ = max(infs, key=infs.get)
                    if self.owner[x,y]!=civ and self.owner[x,y]!=None:
                        loss[self.owner[x,y]] += 1
                        gain[civ] += 1
                    self.owner[x,y] = civ
                    if (x,y) in self.city_owners:
                        if self.city_owners[x,y]!=civ:
                            # city is protected from changing hands
                            if (x,y)==self.cities[self.city_owners[x,y]][0]:
                                self.owner[x,y] = self.city_owners[x,y]
                            else: # city changes hands
                                loser = self.city_owners[x,y]
                                if loser in transfers:
                                    transfers[loser].append(civ)
                                else:
                                    transfers[loser] = [civ]
                                self.remove_city((x,y))
                                self.add_city((x,y),civ)

        self.area = {civ:0 for civ in range(self.num_civs)}
        self.border = {civ:{} for civ in range(self.num_civs)}
        for x in range(self.L):
            for y in range(self.L):
                civ = self.owner[x,y]
                if civ != None:
                    self.area[civ] += 1
                    for (dx,dy) in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        if (x+dx, y+dy) in self.owner:
                            neighbour = self.owner[x+dx, y+dy]
                            if neighbour!=civ:
                                if neighbour in self.border[civ]:
                                    if (x,y) not in self.border[civ][neighbour]:
                                        self.border[civ][neighbour].append((x,y))
                                else:
                                    self.border[civ][neighbour] = [(x,y)]
                                    
        return loss, gain, transfers
    
    def make_map(self,filename=None,civ=None,width=512):

        if civ!=None:
            X = [self.L,0]
            Y = [self.L,0]
            for x in range(self.L):
                for y in range(self.L):
                    if self.owner[x,y]==civ:
                        X[0] = min(X[0],x)
                        X[1] = max(X[1],x)
                        Y[0] = min(Y[0],y)
                        Y[1] = max(Y[1],y)
            b = self.r
        else:
            X = [0,self.L]
            Y = [0,self.L]
            b = 0

        worldmap = Image.new('RGB',(self.L,self.L))

        for x in range(self.L):
            for y in range(self.L):
                if (x,y) in self.owner:
                    if self.owner[x,y]!=None:
                        if (x,y) in self.cities[self.owner[x,y]]:
                            worldmap.putpixel((x,y),self.city_colors[self.owner[x,y]])
                        else:
                            worldmap.putpixel((x,y),self.colors[self.owner[x,y]])
                    else:
                        worldmap.putpixel((x,y),(192,192,192))
                else:
                    worldmap.putpixel((x,y),(255,255,255))
                    
        if civ!=None:

            worldmap.save('temp.png')
            image = img.imread('temp.png') 
            
            matplotlib.rc('xtick', labelsize=16) 
            matplotlib.rc('ytick', labelsize=16)
            
            fig, ax = plt.subplots()
            ax.set(xlim=(X[0]-b, X[1]+b), ylim=(Y[0]-b, Y[1]+b))
            

            imageplot = plt.imshow(image)
            plt.minorticks_on()
            fig.savefig('temp.png',bbox_inches='tight')
            plt.close()
            
            worldmap = Image.open('temp.png')
            
        else:
            worldmap = worldmap.transpose(Image.FLIP_TOP_BOTTOM)
            
        worldmap = worldmap.resize((width,int(width*worldmap.size[1]/worldmap.size[0])),1+3*(civ==None))

        if filename:
            worldmap.save(filename)

        return worldmap
            
            