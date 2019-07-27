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
    color = GeomVertexWriter(vdata, 'color')
    texcoord = GeomVertexWriter(vdata, 'texcoord')
    tris = GeomTriangles(Geom.UHDynamic)

    # Top Plane
    vertex.add_data3(-1,-1, 1)
    vertex.add_data3( 1,-1, 1)
    vertex.add_data3( 1, 1, 1)
    vertex.add_data3(-1, 1, 1)
    for x in range(4):
        color.addData4f(0.0, 0.8, 0.4, 1.0)
        normal.addData3(0,0,1)
    tris.addVertices(0, 1, 2)
    tris.addVertices(0, 2, 3)

    #Side Planes
    vertex.add_data3(1,-1,-1)
    vertex.add_data3(1, 1,-1)
    vertex.add_data3(1, 1, 1)
    vertex.add_data3(1,-1, 1)

    vertex.add_data3( 1, 1,-1)
    vertex.add_data3(-1, 1,-1)
    vertex.add_data3(-1, 1, 1)
    vertex.add_data3( 1, 1, 1)

    vertex.add_data3(-1, 1,-1)
    vertex.add_data3(-1,-1,-1)
    vertex.add_data3(-1,-1, 1)
    vertex.add_data3(-1, 1, 1)

    vertex.add_data3(-1,-1,-1)
    vertex.add_data3( 1,-1,-1)
    vertex.add_data3( 1,-1, 1)
    vertex.add_data3(-1,-1, 1)

    for x in range(4):
        normal.addData3(1,0,0)
    for x in range(4):
        normal.addData3(0,1,0)
    for x in range(4):
        normal.addData3(-1,0,0)
    for x in range(4):
        normal.addData3(0,-1,0)

    for x in range (4):
        tris.addVertices(4*(x+1), 4*(x+1)+1, 4*(x+1)+2)
        tris.addVertices(4*(x+1), 4*(x+1)+2, 4*(x+1)+3)

    for x in range(16):
        color.addData4f(0.6, 0.4, 0.2, 1.0)

    for x in range(1):
        texcoord.addData2f(0.0, 0.0)
        texcoord.addData2f(0.5, 0.0)
        texcoord.addData2f(0.5, 1.0)
        texcoord.addData2f(0.0, 1.0)
    for x in range(4):
        texcoord.addData2f(0.5, 0.0)
        texcoord.addData2f(1.0, 0.0)
        texcoord.addData2f(1.0, 1.0)
        texcoord.addData2f(0.5, 1.0)

    terrainCube = Geom(vdata)
    terrainCube.addPrimitive(tris)
    return terrainCube



