#!/usr/bin/env python

# Author: Bastien Pesenti (bpesenti@yahoo.fr)
# Date: 7/26/2019

from panda3d.core import StackedPerlinNoise2, PNMImage
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles, GeomVertexWriter
import random
import math

# Description
# Tiled terrain map in 2x2m tiles
# Height in discrete increments of 0.5m 

class LightworldTerrain:
    
    def __init__(self, size):
        self.size = size
        self.__terrainImage = self.__generateTerrainImage()

    def __getHeight(self,i,j):
        h = round((self.__terrainImage.getGray(i,j)-0.5)*20)/2
        return h

    def __generateTerrainImage(self):
        #Perlin Noise Base
        terrainImage = PNMImage(self.size, self.size, 1)
        scale = 0.5 * 64 / self.size
        stackedNoise = StackedPerlinNoise2(scale, scale, 8, 2, 0.5, self.size, 0)
        terrainImage.perlinNoiseFill(stackedNoise)

        #Make it look a bit more natural
        for i in range(self.size):
            for j in range(self.size):
                g = terrainImage.getGray(i,j)
                # make between -1 and 1, more land than water
                g = (g-0.25)/0.75
                # make mountain more spiky and plains more flat
                if g>0:
                    g = g ** 2
                terrainImage.setGray(i,j,(g+1)/2)

        return terrainImage

    def getHeightAtPos(self,x,y):
        h = self.__getHeight(round((x+self.size)/2), round((y+self.size)/2))
        return h
    
    def generateTerrainGeom(self):

        #Define format
        format = GeomVertexFormat.getV3n3cpt2()
        vdata = GeomVertexData('square', format, Geom.UHDynamic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        tris = GeomTriangles(Geom.UHDynamic)

        vIndex = 0

        def addTexRock():
            texcoord.addData2f(0.0, 0.0)
            texcoord.addData2f(0.5, 0.0)
            texcoord.addData2f(0.5, 0.5)
            texcoord.addData2f(0.0, 0.5)
        def addTexWater():
            texcoord.addData2f(0.5, 0.0)
            texcoord.addData2f(1.0, 0.0)
            texcoord.addData2f(1.0, 0.5)
            texcoord.addData2f(0.5, 0.5)
        def addTexGrass():
            texcoord.addData2f(0.0, 0.5)
            texcoord.addData2f(0.5, 0.5)
            texcoord.addData2f(0.5, 1.0)
            texcoord.addData2f(0.0, 1.0)
        def addTexSand():
            texcoord.addData2f(0.5, 0.5)
            texcoord.addData2f(1.0, 0.5)
            texcoord.addData2f(1.0, 1.0)
            texcoord.addData2f(0.5, 1.0)

        def addTexFloor(altitude):
            if(altitude<0):
                addTexWater()
            elif(altitude<0.5):
                addTexSand()
            elif(altitude<4):
                addTexGrass()
            else:
                addTexRock()

        def addTexSkirt(altitude, wallHeight):
            if(altitude<=0):
                addTexWater()
            elif(altitude<0.5):
                addTexSand()
            elif(altitude<4) and (wallHeight<1):
                addTexGrass()
            else:
                addTexRock()

        def addSquareVerts(vStart):
            tris.addVertices(vStart, vStart+1, vStart+2)
            tris.addVertices(vStart, vStart+2, vStart+3)
            return vStart + 4

        def addFloorSquare(x, y, z, vStart):
            vertex.add_data3(x-1,y-1, z)
            vertex.add_data3(x+1,y-1, z)
            vertex.add_data3(x+1,y+1, z)
            vertex.add_data3(x-1,y+1, z)
            for x in range(4):
                normal.addData3(0,0,1)
            return addSquareVerts(vStart)

        def addSkirtSquareXP(x, y, z, vStart):
            vertex.add_data3(x+1,y-1,z-0.5)
            vertex.add_data3(x+1,y+1,z-0.5)
            vertex.add_data3(x+1,y+1,z)
            vertex.add_data3(x+1,y-1,z)
            for x in range(4):
                normal.addData3(1,0,0)
            return addSquareVerts(vStart)

        def addSkirtSquareYP(x, y, z, vStart):
            vertex.add_data3(x+1,y+1,z-0.5)
            vertex.add_data3(x-1,y+1,z-0.5)
            vertex.add_data3(x-1,y+1,z)
            vertex.add_data3(x+1,y+1,z)
            for x in range(4):
                normal.addData3(0,1,0)
            return addSquareVerts(vStart)
        
        def addSkirtSquareXN(x, y, z, vStart):
            vertex.add_data3(x-1,y+1,z-0.5)
            vertex.add_data3(x-1,y-1,z-0.5)
            vertex.add_data3(x-1,y-1,z)
            vertex.add_data3(x-1,y+1,z)
            for x in range(4):
                normal.addData3(-1,0,0)
            return addSquareVerts(vStart)
        
        def addSkirtSquareYN(x, y, z, vStart):
            vertex.add_data3(x-1,y-1,z-0.5)
            vertex.add_data3(x+1,y-1,z-0.5)
            vertex.add_data3(x+1,y-1,z)
            vertex.add_data3(x-1,y-1,z)
            for x in range(4):
                normal.addData3(0,-1,0)
            return addSquareVerts(vStart)

        for i in range(self.size):
            for j in range(self.size):
                # add floor
                x = 2*i-self.size
                y = 2*j-self.size
                z = self.__getHeight(i,j)
                vIndex = addFloorSquare(x, y, z, vIndex)
                addTexFloor(z)

                #yp side
                bottom = -5
                if j != self.size-1:
                    bottom = self.__getHeight(i,j+1)
                zSide = z
                wallHeight = zSide-bottom
                while zSide > bottom:
                    vIndex = addSkirtSquareYP(x, y, zSide, vIndex)  
                    if j == self.size-1:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, wallHeight)
                    zSide = zSide - 0.5

                #yn side
                bottom = -5
                if j != 0:
                    bottom = self.__getHeight(i,j-1)               
                zSide = z
                wallHeight = zSide-bottom
                while zSide > bottom:
                    vIndex = addSkirtSquareYN(x, y, zSide, vIndex)  
                    if j == 0:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, wallHeight)
                    zSide = zSide - 0.5

                #xp side
                bottom = -5
                if i != self.size-1:
                    bottom = self.__getHeight(i+1,j)               
                zSide = z
                wallHeight = zSide-bottom
                while zSide > bottom:
                    vIndex = addSkirtSquareXP(x, y, zSide, vIndex) 
                    if i == self.size-1:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, wallHeight)
                    zSide = zSide - 0.5

                #xn side
                bottom = -5
                if i != 0:
                    bottom = self.__getHeight(i-1,j)               
                zSide = z
                wallHeight = zSide-bottom
                while zSide > bottom:
                    vIndex = addSkirtSquareXN(x, y, zSide, vIndex)
                    if i == 0:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, wallHeight)
                    zSide = zSide - 0.5

        terrainCube = Geom(vdata)
        terrainCube.addPrimitive(tris)
        return terrainCube



