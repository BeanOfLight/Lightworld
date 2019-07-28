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
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import CollideMask
from panda3d.core import Texture, GeomNode
from panda3d.core import PerspectiveLens
from panda3d.core import CardMaker
from panda3d.core import Light, DirectionalLight, AmbientLight
from panda3d.core import TextNode
from panda3d.core import LVector3
import sys
import os

from terrain import LightworldTerrain
from avatar import LightworldAvatarControler

# Function to put instructions on the screen.
def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1), scale=.05,
                        shadow=(0, 0, 0, 1), parent=base.a2dTopLeft,
                        pos=(0.08, -pos - 0.04), align=TextNode.ALeft)

# Function to put title on the screen.
def addTitle(text):
    return OnscreenText(text=text, style=1, fg=(1, 1, 1, 1), scale=.07,
                        parent=base.a2dBottomRight, align=TextNode.ARight,
                        pos=(-0.1, 0.09), shadow=(0, 0, 0, 1))

# Game Class
class LightworldBasic(ShowBase):
    def __init__(self):
        # Set up the window, camera, etc.
        ShowBase.__init__(self)

        # Set the background color to blue
        self.win.setClearColor((0.4, 0.7, 1.0, 1))

        # Post the instructions
        self.title = addTitle(
            "Lightworld: Explore the map")
        self.inst1 = addInstructions(0.06, "[ESC]: Quit")
        self.inst2 = addInstructions(0.12, "[Left Arrow]: Rotate Left")
        self.inst3 = addInstructions(0.18, "[Right Arrow]: Rotate Right")
        self.inst4 = addInstructions(0.24, "[Up Arrow]: Move Forward")

        # Terrain Map
        terrainSize = 128
        terrain = LightworldTerrain(terrainSize) 
        terrainMap = terrain.generateTerrainGeom()
        snode = GeomNode('terrainPatch')
        snode.addGeom(terrainMap)
        map = render.attachNewNode(snode)
        map.setTwoSided(True)
        testTexture = loader.loadTexture("terrainTex.png")
        map.setTexture(testTexture)

        # Create the avatar
        self.avatarControler = LightworldAvatarControler()
        self.avatarControler.curPos = LVector3(0,0,terrain.getHeightAtPos(0,0)+1)
        self.avatarControler.curMoveDir = LVector3(0,1,0)
        self.avatarControler.curLookDir = LVector3(0,1,0)

        self.avatar = loader.loadModel("models/smiley")
        self.avatar.reparentTo(render)
        self.avatar.setScale(0.25)
        self.avatar.setPos(self.avatarControler.curPos)

        # Accept the control keys for movement and rotation
        self.accept("escape", sys.exit)
     #   self.accept("arrow_left", self.turnLeft)
     #   self.accept("arrow_right", self.turnRight)
        self.accept("arrow_up", self.moveForward)

        taskMgr.add(self.move, "moveTask")

        # Set up the camera
        self.disableMouse()
        self.camera.setPos(self.avatarControler.getCameraPos())
        self.camera.lookAt(self.avatarControler.getCameraLookAt())

        # We will detect the height of the terrain by creating a collision
        # ray and casting it downward toward the terrain.  One ray will
        # start above ralph's head, and the other will start above the camera.
        # A ray may hit the terrain, or it may hit a rock or a tree.  If it
        # hits the terrain, we can detect the height.  If it hits anything
        # else, we rule that the move is illegal.
        self.cTrav = CollisionTraverser()
        self.avatarGroundRay = CollisionRay()
        self.avatarGroundRay.setOrigin(0, 0, 9)
        self.avatarGroundRay.setDirection(0, 0, -1)
        self.avatarGroundCol = CollisionNode('avatarRay')
        self.avatarGroundCol.addSolid(self.avatarGroundRay)
        self.avatarGroundCol.setFromCollideMask(CollideMask.bit(0))
        self.avatarGroundCol.setIntoCollideMask(CollideMask.allOff())
        self.avatarGroundColNp = self.avatar.attachNewNode(self.avatarGroundCol)
        self.avatarGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.avatarGroundColNp, self.avatarGroundHandler)

        # Uncomment this line to see the collision rays
        self.avatarGroundColNp.show()

        # Uncomment this line to show a visual representation of the
        # collisions occuring
        self.cTrav.showCollisions(render)

        # Create some lighting
        alight = AmbientLight('alight')
        alight.setColor((0.4, 0.4, 0.4, 1))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)
        dlight = DirectionalLight('dlight')
        dlight.setColor((0.8, 0.7, 0.6, 1))
        dlnp = render.attachNewNode(dlight)
        render.setLight(dlnp)
        dlnp.setHpr(0,-60,0)

    
    def moveForward(self):
        self.avatarControler.triggerMoveForward()

    def move(self, task):       
        if(self.avatarControler.moving == True):
            self.avatarControler.moveByDistance(0.1)
            self.avatar.setPos(self.avatarControler.curPos)
            self.camera.setPos(self.avatarControler.getCameraPos())

        return task.cont

demo = LightworldBasic()
demo.run()
