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
        self.curLookDir = LVector3(0,1,0)

        # Target position for next move
        self.targetPos = self.curPos
        self.targetMoveDir = self.curMoveDir
        self.targetLookDir = self.curLookDir

        #State
        self.canReceiveCommand = True
        self.moving = False
    
    def getCameraPos(self):
        return self.curPos - (self.curLookDir * 3.0)

    def getCameraLookAt(self):
        return self.curPos

    def triggerMoveForward(self):
        if(self.canReceiveCommand):
            self.moving = True
            self.canReceiveCommand = False
            self.targetPos = self.curPos + self.curMoveDir * 2.0
    
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
        
        return self.curPos