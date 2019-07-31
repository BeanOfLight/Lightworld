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

        def addTriangleFan(vStart, numVerts):
            for i in range (1, numVerts-1):
                tris.addVertices(vStart, vStart+i, vStart+i+1)
            return vStart + numVerts

        def addSquareVerts(vStart):
            vNext = addTriangleFan(vStart, 4)
            return vNext

        def addFloorSquare(x, y, z, xnOffset, xpOffset, ynOffset, ypOffset, vStart):
            vertex.add_data3(x-xnOffset,y-ynOffset, z)
            vertex.add_data3(x+xpOffset,y-ynOffset, z)
            vertex.add_data3(x+xpOffset,y+ypOffset, z)
            vertex.add_data3(x-xnOffset,y+ypOffset, z)
            for x in range(4):
                normal.addData3(0,0,1)
            return addSquareVerts(vStart)

        def addSkirtSquareXN(x, y, z, xnOffset, xpOffset, ynOffset, ypOffset, vStart):
            vertex.add_data3(x-1,y+1,z-0.5)
            vertex.add_data3(x-1,y-1,z-0.5)
            vertex.add_data3(x-xnOffset,y-ynOffset,z)
            vertex.add_data3(x-xnOffset,y+ypOffset,z)
            for x in range(4):
                normal.addData3(-1,0,0)
            return addSquareVerts(vStart)

        def addSkirtSquareXP(x, y, z, xnOffset, xpOffset, ynOffset, ypOffset, vStart):
            vertex.add_data3(x+1,y-1,z-0.5)
            vertex.add_data3(x+1,y+1,z-0.5)
            vertex.add_data3(x+xpOffset,y+ypOffset,z)
            vertex.add_data3(x+xpOffset,y-ynOffset,z)
            for x in range(4):
                normal.addData3(1,0,0)
            return addSquareVerts(vStart)

        def addSkirtSquareYP(x, y, z, xnOffset, xpOffset, ynOffset, ypOffset, vStart):
            vertex.add_data3(x+1,y+1,z-0.5)
            vertex.add_data3(x-1,y+1,z-0.5)
            vertex.add_data3(x-xnOffset,y+ypOffset,z)
            vertex.add_data3(x+xpOffset,y+ypOffset,z)
            for x in range(4):
                normal.addData3(0,1,0)
            return addSquareVerts(vStart)
        
        def addSkirtSquareYN(x, y, z, xnOffset, xpOffset, ynOffset, ypOffset, vStart):
            vertex.add_data3(x-1,y-1,z-0.5)
            vertex.add_data3(x+1,y-1,z-0.5)
            vertex.add_data3(x+xpOffset,y-ynOffset,z)
            vertex.add_data3(x-xnOffset,y-ynOffset,z)
            for x in range(4):
                normal.addData3(0,-1,0)
            return addSquareVerts(vStart)

        for i in range(self.size):
            for j in range(self.size):
                # add floor
                x = 2*i-self.size
                y = 2*j-self.size
                z = self.__getHeight(i,j)

                # Compute attributes of the cell for 4 straight directions


                if(i==0):
                    xnBorder = True 
                    xnBottom = -5
                else: 
                    xnBorder = False
                    xnBottom = self.__getHeight(i-1,j)

                if(i==self.size-1):
                    xpBorder = True 
                    xpBottom = -5
                else: 
                    xpBorder = False
                    xpBottom = self.__getHeight(i+1,j)

                if(j==0):
                    ynBorder = True 
                    ynBottom = -5
                else: 
                    ynBorder = False
                    ynBottom = self.__getHeight(i,j-1) 

                if(j==self.size-1):
                    ypBorder = True 
                    ypBottom = -5
                else: 
                    ypBorder = False
                    ypBottom = self.__getHeight(i,j+1)                

                # Compute attributes of the cell for 4 diagonal directions
                if(i==0 or j==0):
                    xnynBorder = True 
                    xnynBottom = -5
                else: 
                    xnynBorder = False
                    xnynBottom = self.__getHeight(i-1,j-1)
                              
                if(i==0 or j==self.size-1):
                    xnypBorder = True 
                    xnypBottom = -5
                else: 
                    xnypBorder = False
                    xnypBottom = self.__getHeight(i-1,j+1)

                if(i==self.size-1 or j==0):
                    xpynBorder = True 
                    xpynBottom = -5
                else: 
                    xpynBorder = False
                    xpynBottom = self.__getHeight(i+1,j-1)
                              
                if(i==self.size-1 or j==self.size-1):
                    xpypBorder = True 
                    xpypBottom = -5
                else: 
                    xpypBorder = False
                    xpypBottom = self.__getHeight(i+1,j+1)

                xnOffset = 1
                xpOffset = 1
                ynOffset = 1
                ypOffset = 1

                if(xnBorder == False and xnBottom < z):
                    xnOffset = 0.5
                if(xpBorder == False and xpBottom < z):
                    xpOffset = 0.5
                if(ynBorder == False and ynBottom < z):
                    ynOffset = 0.5
                if(ypBorder == False and ypBottom < z):
                    ypOffset = 0.5

                vIndex = addFloorSquare(x, y, z, xnOffset, xpOffset, ynOffset, ypOffset, vIndex)
                addTexFloor(z)

                #yp side
                zSide = z
                while zSide > ypBottom:
                    vIndex = addSkirtSquareYP(x, y, zSide, xnOffset, xpOffset, ynOffset, ypOffset, vIndex)  
                    if ypBorder == True:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, z-ypBottom)
                    zSide = zSide - 0.5

                #yn side
                zSide = z
                while zSide > ynBottom:
                    vIndex = addSkirtSquareYN(x, y, zSide, xnOffset, xpOffset, ynOffset, ypOffset, vIndex)  
                    if ynBorder:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, z-ynBottom)
                    zSide = zSide - 0.5

                #xp side
                zSide = z
                while zSide > xpBottom:
                    vIndex = addSkirtSquareXP(x, y, zSide, xnOffset, xpOffset, ynOffset, ypOffset, vIndex) 
                    if i == self.size-1:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, z-xpBottom)
                    zSide = zSide - 0.5

                #xn side
                zSide = z
                while zSide > xnBottom:
                    vIndex = addSkirtSquareXN(x, y, zSide, xnOffset, xpOffset, ynOffset, ypOffset, vIndex)
                    if i == 0:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, z-xnBottom)
                    zSide = zSide - 0.5

        terrainCube = Geom(vdata)
        terrainCube.addPrimitive(tris)
        return terrainCube



