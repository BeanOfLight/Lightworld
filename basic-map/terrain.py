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

def generateTerrainImage(size):
    #Perlin Noise Base
    terrainImage = PNMImage(size, size, 1)
    stackedNoise = StackedPerlinNoise2(0.5, 0.5, 8, 2, 0.5, size, 0)
    terrainImage.perlinNoiseFill(stackedNoise)

    #Make it look a bit more natural
    #for i in range(size):
    #    for j in range(size):
    #        g = terrainImage.getGray(i,j)
    #        # g = (abs(g-0.5)*2)**2
    #        # g = ((g-0.5)*2)
    #        terrainImage.setGray(i,j,(g+1)/2)

    return terrainImage

def generateTerrainGeom(size):

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
        elif(altitude<5):
            addTexGrass()
        else:
            addTexRock()

    def addTexSkirt(altitude, wallHeight):
        if(altitude<=0):
            addTexWater()
        elif(altitude<0.5):
            addTexSand()
        elif(altitude<5) and (wallHeight<1):
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

    def getHeight(i,j, terrainHeigh):
        h = round((terrainHeight.getGray(i,j)-0.3)*20)/2
        #if h<0:
        #    h = 0
        return h

    terrainHeight = generateTerrainImage(size)

    for i in range(size):
        for j in range(size):
            # add floor
            x = 2*i-size
            y = 2*j-size
            z = getHeight(i,j, terrainHeight)
            vIndex = addFloorSquare(x, y, z, vIndex)
            addTexFloor(z)

            #yp side
            bottom = -5
            if j != size-1:
                bottom = getHeight(i,j+1, terrainHeight)
            zSide = z
            wallHeight = zSide-bottom
            while zSide > bottom:
                vIndex = addSkirtSquareYP(x, y, zSide, vIndex)  
                if j == size-1:
                    addTexSand()
                else:
                    addTexSkirt(zSide, wallHeight)
                zSide = zSide - 0.5

            #yn side
            bottom = -5
            if j != 0:
                bottom = getHeight(i,j-1, terrainHeight)               
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
            if i != size-1:
                bottom = getHeight(i+1,j, terrainHeight)               
            zSide = z
            wallHeight = zSide-bottom
            while zSide > bottom:
                vIndex = addSkirtSquareXP(x, y, zSide, vIndex) 
                if i == size-1:
                    addTexSand()
                else:
                    addTexSkirt(zSide, wallHeight)
                zSide = zSide - 0.5

            #xn side
            bottom = -5
            wallHeight = zSide-bottom
            if i != 0:
                bottom = getHeight(i-1,j, terrainHeight)               
            zSide = z
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



