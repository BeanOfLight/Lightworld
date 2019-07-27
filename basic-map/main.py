#!/usr/bin/env python

# Author: Kwasi Mensah (kmensah@andrew.cmu.edu)
# Date: 8/02/2005
#
# This is meant to be a simple example of how to draw a cube
# using Panda's new Geom Interface. Quads arent directly supported
# since they get broken down to trianlges anyway.
#

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from panda3d.core import lookAt
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles, GeomVertexWriter
from panda3d.core import Texture, GeomNode
from panda3d.core import PerspectiveLens
from panda3d.core import CardMaker
from panda3d.core import Light, Spotlight, AmbientLight
from panda3d.core import TextNode
from panda3d.core import LVector3
import sys
import os

base = ShowBase()
base.disableMouse()
base.camera.setPos(40, -100, 20)
base.camera.lookAt(0, 0, 0)
#base.camera.setPos(0, 0, 1.5)
#base.camera.lookAt(0, 1, 1.4)

title = OnscreenText(text="Create a Basic Map",
                     style=1, fg=(1, 1, 1, 1), pos=(-0.1, 0.1), scale=.07,
                     parent=base.a2dBottomRight, align=TextNode.ARight)

# You can't normalize inline so this is a helper function
def normalized(*args):
    myVec = LVector3(*args)
    myVec.normalize()
    return myVec


def makeTerrainCube():
    
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

testTexture = loader.loadTexture("grass.png")
terrainSize = 60
x0 = terrainSize / 2
y0 = terrainSize / 2
for i in range(terrainSize):
    for j in range(terrainSize):
        snode = GeomNode('terrainPatch')
        terrainCube = makeTerrainCube()
        snode.addGeom(terrainCube)
        cube = render.attachNewNode(snode)
        cube.setTwoSided(True)
        cube.setTexture(testTexture)
        x = 2*i-terrainSize
        y = 2*j-terrainSize
        z = round(max([4-((x-x0)**2+(y-y0)**2) / 50,0]))
        cube.setPos(x, y, z)

alight = AmbientLight('alight')
alight.setColor((0.4, 0.4, 0.4, 1))
alnp = render.attachNewNode(alight)
render.setLight(alnp)

slight = Spotlight('slight')
slight.setColor((1, 1, 1, 1))
lens = PerspectiveLens()
slight.setLens(lens)
slnp = render.attachNewNode(slight)
render.setLight(slnp)
slnp.setPos(cube, -20, -40, 80)
slnp.lookAt(0, 0, 0)

base.run()
