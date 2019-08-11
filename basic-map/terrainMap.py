#########################################################################################
# LightWorld
# terrainMap.py
# Author: Bastien Pesenti (bpesenti@yahoo.fr)
# Date: 8/10/2019

from panda3d.core import StackedPerlinNoise2, PNMImage
from panda3d.core import LVector3f, LVector3i, LVector2f, LVector2i
import math
from array import *

###############################################################################
# Generate the terrain image
class TerrainHeightMap:
    def __init__(self, imagSize):
        self.cellSize = 2.0
        self.heightStep = 0.5
        self.center = LVector2f(0.0, 0.0)
        self.size = imagSize
        self.__heightMap = [[0 for i in range(self.size)] for j in range(self.size)]
        self.__waterMap = [[False for i in range(self.size)] for j in range(self.size)]
    
    def generateTerrain(self):
        #Perlin Noise Base
        scale = 0.5 * 64 / self.size
        stackedNoise = StackedPerlinNoise2(scale, scale, 8, 2, 0.5, self.size, 0)
        terrainImage = PNMImage(self.size, self.size, 1)
        terrainImage.perlinNoiseFill(stackedNoise)

        #Make it look a bit more natural
        for i in range(self.size):
            for j in range(self.size):
                g = terrainImage.getGray(i,j)
                # make between -0.5 and 1, more land than water
                g = (g-0.25)/0.75
                # make mountain more spiky and plains more flat
                if g>0:
                    g = g ** 2
                # return to 0.25 to 1 range
                g = (g+1)/2
                terrainImage.setGray(i,j,g)
        
        #Make it an island
        border = 2 * self.size / 8
        for i in range(self.size):
            for j in range(self.size):
                distToEdge = min(i, self.size-1-i, j, self.size-1-j)
                if(distToEdge < border):
                    g = terrainImage.getGray(i,j)
                    g = g * math.sqrt(distToEdge / border)
                    g = max(g, 0.25)
                    terrainImage.setGray(i,j,g)

        # Convert to kHeight
        # Height in integer increments between -10 and 10
        for i in range(self.size):
            for j in range(self.size):
                self.__heightMap[i][j] = round((terrainImage.getGray(i,j)-0.5)*30)
                if(self.__heightMap[i][j] < 0):
                    self.__waterMap[i][j] = True

    def isValid(self, i,j):
        return i >= 0 and i < self.size and j >= 0 and j < self.size
    
    def hasWater(self, i, j):
        return self.__waterMap[i][j] == True
    
    def getKHeightFromZ(self, z):
        return round(z/self.heightStep)

    def getZHeightFromK(self, k):
        return k * self.heightStep
    
    def getKHeightFromIJ(self, i, j):
        return self.__heightMap[i][j]

    def getZHeightFromIJ(self, i, j):
        return self.getZHeightFromK(self.getKHeightFromIJ(i,j)) 

    def getZHeightFromXY(self, x, y):
        ijLocation = self.getIJLocationFromXY(LVector2f(x,y))
        return self.getZHeightFromIJ(ijLocation.getX(), ijLocation.getY())

    def getIJLocationFromXY(self, XYLocation):
        return LVector2i(
            round((XYLocation.getX()+self.size)/2),
            round((XYLocation.getY()+self.size)/2))

    def getXYLocationFromIJ(self, IJLocation):
        return LVector2f(
            2*IJLocation.getX()-self.size, 
            2*IJLocation.getY()-self.size)