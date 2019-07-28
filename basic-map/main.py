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
from panda3d.core import Light, DirectionalLight, AmbientLight
from panda3d.core import TextNode
from panda3d.core import LVector3
import sys
import os

from terrain import generateTerrainImage, generateTerrainGeom

base = ShowBase()
base.disableMouse()

terrainSize = 128

base.camera.setPos(terrainSize/2, -1.7*terrainSize, terrainSize/4)
base.camera.lookAt(0, 0, 0)

title = OnscreenText(text="Create a Basic Map",
                     style=1, fg=(1, 1, 1, 1), pos=(-0.1, 0.1), scale=.07,
                     parent=base.a2dBottomRight, align=TextNode.ARight)

terrainCube = generateTerrainGeom(terrainSize)
snode = GeomNode('terrainPatch')
snode.addGeom(terrainCube)
cube = render.attachNewNode(snode)
cube.setTwoSided(True)
testTexture = loader.loadTexture("terrainTex.png")
cube.setTexture(testTexture)

alight = AmbientLight('alight')
alight.setColor((0.4, 0.4, 0.4, 1))
alnp = render.attachNewNode(alight)
render.setLight(alnp)

dlight = DirectionalLight('dlight')
dlight.setColor((0.8, 0.7, 0.6, 1))
dlnp = render.attachNewNode(dlight)
render.setLight(dlnp)
dlnp.setHpr(0,-60,0)

base.run()
