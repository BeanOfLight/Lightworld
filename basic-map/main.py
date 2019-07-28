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

from terrain import generateTerrainImage, generateTerrainGeom

base = ShowBase()
base.disableMouse()
base.camera.setPos(40, -160, 40)
base.camera.lookAt(0, 0, 0)
#base.camera.setPos(0, 0, 1.5)
#base.camera.lookAt(0, 1, 1.4)

title = OnscreenText(text="Create a Basic Map",
                     style=1, fg=(1, 1, 1, 1), pos=(-0.1, 0.1), scale=.07,
                     parent=base.a2dBottomRight, align=TextNode.ARight)

terrainSize = 256
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

slight = Spotlight('slight')
slight.setColor((1, 1, 1, 1))
lens = PerspectiveLens()
slight.setLens(lens)
slnp = render.attachNewNode(slight)
render.setLight(slnp)
slnp.setPos(cube, -20, -40, 80)
slnp.lookAt(0, 0, 0)

base.run()
