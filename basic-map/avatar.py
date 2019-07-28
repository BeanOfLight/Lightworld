#!/usr/bin/env python

# Author: Bastien Pesenti (bpesenti@yahoo.fr)
# Date: 7/28/2019

from panda3d.core import LVector3

# Description
# Playable avatar

class LightworldAvatarControler:
    
    def __init__(self):
        # Current Position
        self.curPos = LVector3(0,0,0)
        self.curMoveDir = LVector3(0,1,0)
        self.curCamPos = self.curPos - self.curMoveDir * 1.9

        # Target position for next move
        self.targetPos = self.curPos
        self.targetMoveDir = self.curMoveDir
        self.targetCamPos = self.curCamPos

        #State
        self.canReceiveCommand = True
        self.moving = False
        self.turning = False
    
    def triggerMoveForward(self, target):
        if(self.canReceiveCommand):
            self.moving = True
            self.canReceiveCommand = False
            self.targetPos = target
    
    def moveByDistance(self, distanceToMove):
        if(self.moving):
            distanceToTarget = (self.targetPos-self.curPos).length()
            if(distanceToTarget<distanceToMove):
                self.curPos = self.targetPos
                self.moving = False
                self.canReceiveCommand = True
            else:
                dir = (self.targetPos-self.curPos) * (1/distanceToTarget)
                newPos = self.curPos + dir * distanceToMove
                self.curPos = newPos
            self.curCamPos = self.curPos - self.curMoveDir * 1.9

    def triggerTurnLeft(self):
        if(self.canReceiveCommand):
            self.turning = True
            self.canReceiveCommand = False
            self.targetMoveDir = LVector3(
                -self.curMoveDir.getY(), self.curMoveDir.getX(), self.curMoveDir.getZ())
            self.targetCamPos = self.curPos - self.targetMoveDir * 1.9

    def triggerTurnRight(self):
        if(self.canReceiveCommand):
            self.turning = True
            self.canReceiveCommand = False
            self.targetMoveDir = LVector3(
                self.curMoveDir.getY(), -self.curMoveDir.getX(), self.curMoveDir.getZ())
            self.targetCamPos = self.curPos - self.targetMoveDir * 1.9

    def turnByDistance(self, distanceToMove):
        if(self.turning):
            distanceToTarget = (self.targetCamPos-self.curCamPos).length()
            if(distanceToTarget<distanceToMove):
                self.curCamPos = self.targetCamPos
                self.curMoveDir = self.targetMoveDir
                self.turning = False
                self.canReceiveCommand = True
            else:
                dir = (self.targetCamPos-self.curCamPos) * (1/distanceToTarget)
                newPos = self.curCamPos + dir * distanceToMove
                self.curCamPos = newPos

    