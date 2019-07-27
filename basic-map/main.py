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
from panda3d.core import Light, Spotlight
from panda3d.core import TextNode
from panda3d.core import LVector3
import sys
import os

base = ShowBase()
base.disableMouse()
base.camera.setPos(10, -20, 10)
base.camera.lookAt(0, 0, 0)

title = OnscreenText(text="Panda3D: Tutorial - Making a Cube Procedurally",
                     style=1, fg=(1, 1, 1, 1), pos=(-0.1, 0.1), scale=.07,
                     parent=base.a2dBottomRight, align=TextNode.ARight)
escapeEvent = OnscreenText(text="1: Set a Texture onto the Cube",
                           style=1, fg=(1, 1, 1, 1), pos=(0.06, -0.08),
                           align=TextNode.ALeft, scale=.05,
                           parent=base.a2dTopLeft)
spaceEvent = OnscreenText(text="2: Toggle Light from the front On/Off",
                          style=1, fg=(1, 1, 1, 1), pos=(0.06, -0.14),
                          align=TextNode.ALeft, scale=.05,
                          parent=base.a2dTopLeft)
upDownEvent = OnscreenText(text="3: Toggle Light from on top On/Off",
                           style=1, fg=(1, 1, 1, 1), pos=(0.06, -0.20),
                           align=TextNode.ALeft, scale=.05,
                           parent=base.a2dTopLeft)


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
        texcoord.addData2f(0.0, 1.0)
        texcoord.addData2f(0.5, 1.0)
    for x in range(4):
        texcoord.addData2f(0.5, 0.0)
        texcoord.addData2f(1.0, 0.0)
        texcoord.addData2f(0.5, 1.0)
        texcoord.addData2f(1.0, 1.0)

    terrainCube = Geom(vdata)
    terrainCube.addPrimitive(tris)
    return terrainCube

terrainCube0 = makeTerrainCube()
snode = GeomNode('terrainCube')
snode.addGeom(terrainCube0)
cube = render.attachNewNode(snode)
cube.setTwoSided(True)

testTexture = loader.loadTexture("grass.png")
cube.setTexture(testTexture)

slight = Spotlight('slight')
slight.setColor((1, 1, 1, 1))
lens = PerspectiveLens()
slight.setLens(lens)
slnp = render.attachNewNode(slight)
render.setLight(slnp)
slnp.setPos(cube, -5, -10, 20)
slnp.lookAt(0, 0, 0)

base.run()