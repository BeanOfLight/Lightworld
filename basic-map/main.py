#!/usr/bin/env python

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
from panda3d.core import NodePath
import sys
import os

from terrain import TerrainMesher
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
        #Interactive or overview mode
        self.overview = True

        # Set up the window, camera, etc.
        ShowBase.__init__(self)

        # Set the background color to blue
        self.win.setClearColor((0.4, 0.7, 1.0, 1))

        # Post the instructions
        self.title = addTitle("Lightworld: Explore the map")       
        self.inst1 = addInstructions(0.06, "[ESC]: Quit")
        self.inst2 = addInstructions(0.12, "[v]: Toggle Overview")
        self.inst3 = addInstructions(0.18, "[s]: Toggle Terrain Style")
        self.inst3 = addInstructions(0.24, "[+/-]: Change Size and Recreate")
        self.inst4 = addInstructions(0.30, "[Space]: Update Terrain")
        self.inst5 = addInstructions(0.36, "[Left Arrow]: Rotate Left")
        self.inst6 = addInstructions(0.42, "[Right Arrow]: Rotate Right")
        self.inst7 = addInstructions(0.48, "[Up Arrow]: Move Forward")
        self.inst8 = addInstructions(0.54, "[Down Arrow]: Move Backward")

        # Create the avatar
        avatarHeight = 1
        cameraDistance = 1
        self.avatarControler = LightworldAvatarControler(avatarHeight, cameraDistance)

        # Initialize terrain and avatar
        self.texture = loader.loadTexture("terrainTex2.png") 
        self.terrainSize = 64
        self.terrainStyle = "taperedStyle"
        self.avatar = loader.loadModel("models/smiley")
        self.avatar.reparentTo(render)
        self.avatar.setScale(0.01)
        self.avatar.hide()
        self.map = NodePath()
        self.terrain = TerrainMesher() 

        # Generate terrain and positive avatar
        self.updateTerrain()

        # Accept the control keys for movement and rotation
        self.accept("escape", sys.exit)
        self.accept("v", self.toggleOverview)
        self.accept("s", self.toggleTerrainStyle)
        self.accept("+", self.increaseTerrainSize)
        self.accept("-", self.decreaseTerrainSize)
        self.accept("space", self.updateTerrain)
        self.accept("arrow_left", self.turnLeft)
        self.accept("arrow_right", self.turnRight)
        self.accept("arrow_up", self.moveForward)
        self.accept("arrow_down", self.moveBackward)
        taskMgr.add(self.move, "moveTask")

        self.disableMouse()
        self.toggleOverview()

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
    
    def updateAvatarPosition(self):
        self.avatarControler.setInitialPos(0,0,self.terrain.heightMap.getZHeightFromXY(0.0,0.0))
        self.avatar.setPos(self.avatarControler.curPos)
        self.avatar.lookAt(self.avatarControler.curPos-self.avatarControler.curMoveDir)
    
    def updateCameraPosition(self):
        if self.overview == False:
            self.camera.setPos(self.avatarControler.curCamPos)
            self.camera.lookAt(self.avatarControler.curPos)
        else:
            self.camera.setPos(LVector3(-2.2 * self.terrainSize, -1.7 * self.terrainSize, self.terrainSize) )
            self.camera.lookAt(LVector3(-0.1 * self.terrainSize, 0.0, -0.30 * self.terrainSize))

    def updateTerrain(self):
        self.terrain.generateTerrain(self.terrainSize)
        self.updateTerrainMesh()
        self.updateAvatarPosition()
        self.updateCameraPosition()

    def updateTerrainMesh(self):
        self.map.removeNode()
        terrainMesh = self.terrain.meshTerrain(self.terrainStyle)
        snode = GeomNode('terrainPatch')
        snode.addGeom(terrainMesh)
        self.map = render.attachNewNode(snode)
        self.map.setTexture(self.texture)
    
    def toggleTerrainStyle(self):
        if(self.terrainStyle == "taperedStyle"):
            self.terrainStyle = "blockStyle"
        else:
            self.terrainStyle = "taperedStyle"
        self.updateTerrainMesh()

    def increaseTerrainSize(self):
        self.terrainSize += self.terrainSize
        self.updateTerrain()

    def decreaseTerrainSize(self):
        if(self.terrainSize > 1):
            self.terrainSize -= round(self.terrainSize / 2.0)
            self.updateTerrain()

    def toggleOverview(self):
        self.overview = not self.overview
        if self.overview == False:
            self.camLens.setFocalLength(0.4)
            self.camLens.setNear(0.1)
            self.inst4.show()
            self.inst5.show()
            self.inst6.show()
            self.inst7.show()
            self.inst8.show()
        else:
            self.disableMouse()
            self.camLens.setFocalLength(1)
            self.inst4.hide()
            self.inst5.hide()
            self.inst6.hide()
            self.inst7.hide()
            self.inst8.hide()
        
        self.updateCameraPosition()

    def moveForward(self):
        if self.overview == False:
            target = self.avatarControler.curPos + self.avatarControler.curMoveDir * 2.0
            target.setZ(self.terrain.heightMap.getZHeightFromXY(target.getX(),target.getY()))
            self.avatarControler.triggerMove(target)

    def moveBackward(self):
        if self.overview == False:
            target = self.avatarControler.curPos - self.avatarControler.curMoveDir * 2.0
            target.setZ(self.terrain.heightMap.getZHeightFromXY(target.getX(),target.getY()))
            self.avatarControler.triggerMove(target)

    def turnLeft(self):
        if self.overview == False:
            self.avatarControler.triggerTurnLeft()
    
    def turnRight(self):
        if self.overview == False:
            self.avatarControler.triggerTurnRight()

    def move(self, task):       
        if(self.avatarControler.moving == True):
            self.avatarControler.moveByDistance(0.1)
            self.avatar.setPos(self.avatarControler.curPos)
            self.avatar.lookAt(self.avatarControler.curPos-self.avatarControler.curMoveDir)
            self.camera.setPos(self.avatarControler.curCamPos)
            self.camera.lookAt(self.avatarControler.curPos)
        elif(self.avatarControler.turning == True):
            self.avatarControler.turnByDistance(0.2)
            self.avatar.lookAt(self.avatarControler.curPos-self.avatarControler.curMoveDir)
            self.camera.setPos(self.avatarControler.curCamPos)
            self.camera.lookAt(self.avatarControler.curPos)

        return task.cont

demo = LightworldBasic()
demo.run()
