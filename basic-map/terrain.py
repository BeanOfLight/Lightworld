#!/usr/bin/env python

# Author: Bastien Pesenti (bpesenti@yahoo.fr)
# Date: 7/26/2019

from panda3d.core import StackedPerlinNoise2, PNMImage
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles, GeomVertexWriter
from panda3d.core import LVector3f, LVector3i, LVector2f, LVector2i
from array import *
import random
import math

# Description
# Tiled terrain map in 2x2m tiles
# Height in discrete increments of 0.5m 

###############################################################################
# Container for the Terrain Mesh Data
class TerrainMesh:
    def __init__(self):
        self.format = GeomVertexFormat.getV3n3cpt2()
        self.vdata = GeomVertexData('terrain', self.format, Geom.UHDynamic)
        self.vertex = GeomVertexWriter(self.vdata, 'vertex')
        self.texcoord = GeomVertexWriter(self.vdata, 'texcoord')
        self.color = GeomVertexWriter(self.vdata, 'color')
        self.tris = GeomTriangles(Geom.UHDynamic)  
        self.normal = GeomVertexWriter(self.vdata, 'normal')
        self.numVerts = 0

    def addFace(self, textureScheme, face):
        n = face.normal
        for v in face.verts:
            self.vertex.add_data3(v.getX(), v.getY(), v.getZ())
            self.normal.addData3(n.getX(), n.getY(), n.getZ())
            self.color.addData4f(1.0, 1.0, 1.0, 1.0)
        for tc in face.texCoords:
            schemeTC = textureScheme.getUVFromXY(face.texMat, tc.getX(), tc.getY())
            self.texcoord.addData2f(schemeTC.getX(), schemeTC.getY())               
        mv = self.numVerts
        for t in face.triangles:
            self.tris.addVertices(mv+t.getX(), mv+t.getY(), mv+t.getZ())
        self.numVerts += len(face.verts)

    def makeGeom(self):
        terrainGeom = Geom(self.vdata)
        terrainGeom.addPrimitive(self.tris)
        return terrainGeom

###############################################################################
# Generate the terrain image
class TerrainHeightMap:
    def __init__(self, imagSize):
        self.cellSize = 2.0
        self.heightStep = 0.5
        self.center = LVector2f(0.0, 0.0)
        self.size = imagSize
        self.__heightMap = [[0 for i in range(self.size)] for j in range(self.size)]
    
    def generateTerrain(self):
        #Perlin Noise Base
        scale = 0.5 * 64 / self.size
        stackedNoise = StackedPerlinNoise2(scale, scale, 8, 2, 0.5, self.size, 0)
        terrainImage = PNMImage(self.size, self.size, 1)
        terrainImage.perlinNoiseFill(stackedNoise)

        #Make it look a bit more natural
        for i in range(self.size):
            for j in range(self.size):
                g = terrainImage.getGray(i,j)
                # make between -0.5 and 1, more land than water
                g = (g-0.25)/0.75
                # make mountain more spiky and plains more flat
                if g>0:
                    g = g ** 2
                # return to 0.25 to 1 range
                g = (g+1)/2
                self.__heightMap[i][j] = g
        
        #Make it an island
        #border = self.size / 8
        #for i in range(self.size):
        #    for j in range(self.size):
        #        distToEdge = min(i, self.size-1-i, j, self.size-1-j)
        #        if(distToEdge < border):
        #            g = self.__terrainImage.getGray(i,j)
        #            g = g * distToEdge / border
        #            g = max(g, 0.25)
        #            self.__terrainImage.setGray(i,j,g)

    def isValid(self, i,j):
        return i >= 0 and i < self.size and j >= 0 and j < self.size
    
    # Height in integer increments between -10 and 10
    def getKHeightFromIJ(self, i, j):
        return round((self.__heightMap[i][j]-0.5)*20)

    def getZHeightFromIJ(self, i, j):
        return self.getKHeightFromIJ(i,j) * self.heightStep 

    def getZHeightFromXY(self, x, y):
        ijLocation = self.getIJLocationFromXY(LVector2f(x,y))
        return self.getZHeightFromIJ(ijLocation.getX(), ijLocation.getY())

    def getIJLocationFromXY(self, XYLocation):
        return LVector2i(
            round((XYLocation.getX()+self.size)/2),
            round((XYLocation.getY()+self.size)/2))

    def getXYLocationFromIJ(self, IJLocation):
        return LVector2f(
            2*IJLocation.getX()-self.size, 
            2*IJLocation.getY()-self.size)

###############################################################################
# Class managing texture computation
class TextureScheme:

    def __init__(self):
        self.scale = 0.4
        self.materialOffset = {
            "rock"  : LVector2f(0.05, 0.05),
            "sand"  : LVector2f(0.55, 0.55),
            "grass" : LVector2f(0.05, 0.55),
            "water" : LVector2f(0.55, 0.05)
            }
    
    # Get UV coordinates from the right material, from xy in [0.0,1.0] range
    def getUVFromXY(self, material, x, y):
        offset = self.materialOffset[material]
        uv = LVector2f(x,y) * self.scale
        return offset + uv

    def getMaterial(self, kHeight, normal):
        #if(normal.getZ() < 0.2):
        #    return "rock"
        if(kHeight<0):
            return "water"
        elif(kHeight<1):
            return "sand"
        elif(kHeight<7):
            return "grass"
        else:
            return "rock"
###############################################################################
# Heading utilities

class Heading:

    #  (7) xnyp   (6) yp   (5) xpyp
    #           +--------+
    #           |        |
    #    (0) xn |        | (4) xp
    #           |        |
    #           +--------+
    #  (1) xnyn   (2) yn   (3) xpyn

    AllSides = [ "xn", "xnyn", "yn", "xpyn", "xp", "xpyp", "yp", "xnyp" ]
    DirectSides = [ "xn", "yn", "xp", "yp" ]
    CornerSides = [ "xnyn", "xpyn", "xpyp", "xnyp" ]

    def getAxis(heading):
        if(heading=="xn" or heading=="xp"):
            return "x"
        elif(heading=="yn" or heading=="yp"):
            return "y"
    
    def getAdjascentHeadings(heading):
        if(heading=="xnyn"):
            return ["xn","yn"]
        elif(heading=="xpyn"):
            return ["xp","yn"]
        elif(heading=="xpyp"):
            return ["xp","yp"]
        elif(heading=="xnyp"):
            return ["xn","yp"]

    def getAdjascentXHeading(heading):
        if(heading=="xnyn"):
            return "xn"
        elif(heading=="xpyn"):
            return "xp"
        elif(heading=="xpyp"):
            return "xp"
        elif(heading=="xnyp"):
            return "xn"

    def getAdjascentYHeading(heading):
        if(heading=="xnyn"):
            return "yn"
        elif(heading=="xpyn"):
            return "yn"
        elif(heading=="xpyp"):
            return "yp"
        elif(heading=="xnyp"):
            return "yp"

    def getDirection2i(heading):
        if(heading=="xn"):
            return LVector2i(-1, 0)
        elif(heading=="xnyn"):
            return LVector2i(-1, -1)
        elif(heading=="yn"):
            return LVector2i(0, -1)
        elif(heading=="xpyn"):
            return LVector2i(1, -1)
        elif(heading=="xp"):
            return LVector2i(1, 0)
        elif(heading=="xpyp"):
            return LVector2i(1, 1)
        elif(heading=="yp"):
            return LVector2i(0, 1)
        elif(heading=="xnyp"):
            return LVector2i(-1, 1)

    def getDirection3f(heading):
        if(heading=="xn"):
            return LVector3f(-1.0, 0.0, 0.0)
        elif(heading=="xnyn"):
            return LVector3f(-1.0, -1.0, 0.0)
        elif(heading=="yn"):
            return LVector3f(0.0, -1.0, 0.0)
        elif(heading=="xpyn"):
            return LVector3f(1.0,-1.0, 0.0)
        elif(heading=="xp"):
            return LVector3f(1.0, 0.0, 0.0)
        elif(heading=="xpyp"):
            return LVector3f(1.0, 1.0, 0.0)
        elif(heading=="yp"):
            return LVector3f(0.0, 1.0, 0.0)
        elif(heading=="xnyp"):
            return LVector3f(-1.0, 1.0, 0.0)

###############################################################################
# Cell face class
class CellFace:
    def __init__(self):
        self.verts = []
        self.texCoords = []
        self.texMat = ""
        self.normal = []
        self.triangles = []

    def getNormal(listVerts):
        v1 = listVerts[1] - listVerts[0]
        v2 = listVerts[2] - listVerts[1]
        n = v1.cross(v2)
        return n.normalized()        
    
    def getTriFan(listVerts):
        fan = []
        nv = len(listVerts)
        for v in range(1,nv-1):
            fan.append(LVector3i(0, v, v+1))
        return fan
    
    def getSquareFace(center, normal, up, sideRadius, upRadius, refTexRadius):
        cx = center.getX()
        cy = center.getY()
        cz = center.getZ()
        sr = sideRadius
        ur = upRadius

        side = up.cross(normal)
        face = CellFace()       
        face.verts = [ 
            center - side * sideRadius - up * upRadius,
            center + side * sideRadius - up * upRadius,
            center + side * sideRadius + up * upRadius, 
            center - side * sideRadius + up * upRadius] 
        ratioSide = sideRadius / refTexRadius
        ratioUp  = upRadius / refTexRadius
        face.texCoords = [
            LVector2f(0.0, 0.0), 
            LVector2f(ratioSide, 0.0), 
            LVector2f(ratioSide, ratioUp), 
            LVector2f(0.0, ratioUp)]
        face.normal = CellFace.getNormal(face.verts)
        face.triangles = CellFace.getTriFan(face.verts)
        return face

###############################################################################
# Cell parameters
#
#   xnyp            yp           xpyp
#       +-----+-----------+-----+
#       | cor |           | cor |
#       | ner |    side   | ner |
#       +-----+-----------+-----+
#       |     |           |     |
#       |     |           |     |
#    xn | side|  center   | side| xp
#       |     |           |     |
#       |     |           |     |
#       +-----+-----------+-----+
#       | cor |   side    | cor |
#       | ner |           | ner |
#       +-----+-----------+-----+
#   xnyn            yn           xpyn
#
class CenterComponent:
    def __init__(self, center):
        self.center = center
        self.radius = 0.5

class SideComponent:
    def __init__(self, center, heading):
        self.center = center
        self.inRadius = 0.5
        self.outRadius = 1.0
        self.heading = heading # in "xn", "yn", "xp", "yp"
        self.stepHeight = 0.5
        self.drop = 0 # drop of direct neighbor
        self.slope = "" # in "flat", "block", "tapered"

class CornerComponent:
    def __init__(self, center, heading):
        self.center = center
        self.inRadius = 0.5
        self.outRadius = 1.0
        self.heading = heading # in "xnyn", "xpyn", "xpyp", "xnyp"
        self.stepHeight = 0.5
        self.cdrop = 0 # drop of corner neighbor
        self.xdrop = 0 # drop of direct neighbor in closest x direction
        self.ydrop = 0 # drop of direct neighbor in closest y direction
        self.slope = "" # in "flat", "block", "taperedX", "taperedY", "foldednormal", "foldedtangential"

class CellInfo:
    def __init__(self, center):
        self.center = center
        self.centerComp = CenterComponent(center)
        self.sideCompList = [
            SideComponent(center, "xn"),
            SideComponent(center, "yn"),
            SideComponent(center, "yp"),
            SideComponent(center, "xp")
        ]
        self.cornerCompList = [
            CornerComponent(center, "xnyn"),
            CornerComponent(center, "xpyn"),
            CornerComponent(center, "xpyp"),
            CornerComponent(center, "xnyp")
        ]   
###############################################################################
# Cell shape class refactored
class CellShape2:

    def __init__(self):
        pass

    def getFaces(self, cellInfo):
        fList = []
        fList.append(CellFace.getSquareFace(
            cellInfo.center, 
            LVector3f(0.0, 0.0, 1.0), 
            LVector3f(0.0, 1.0, 0.0), 
            cellInfo.centerComp.radius, cellInfo.centerComp.radius, 
            1.0))

        for sc in cellInfo.sideCompList:
            headingDir = Heading.getDirection3f(sc.heading)
            center = cellInfo.center + headingDir * (sc.outRadius+sc.inRadius) / 2.0
            if(sc.slope == "flat"):
                fList.append(CellFace.getSquareFace(
                    center, 
                    LVector3f(0.0, 0.0, 1.0), 
                    headingDir,
                    sc.inRadius,
                    (sc.outRadius-sc.inRadius) / 2.0,
                    1.0))                
            elif(sc.slope == "tapered"):
                tcenter = center - LVector3f(0.0, 0.0, 1.0) * sc.stepHeight / 2.0
                tnormal = (LVector3f(0.0, 0.0, 1.0) + headingDir)
                tnormal.normalize()
                tup = (- headingDir + LVector3f(0.0, 0.0, 1.0))
                tup.normalize()
                fList.append(CellFace.getSquareFace(
                    tcenter, 
                    tnormal, 
                    tup,
                    sc.inRadius,
                    (sc.outRadius-sc.inRadius) / 2.0 * math.sqrt(2.0),
                    1.0)) 
                # Vertical for further drop
                for lvl in range(1,sc.drop):
                    vcenter = cellInfo.center + headingDir * sc.outRadius - LVector3f(0.0, 0.0, 1.0) * sc.stepHeight * lvl * 3.0 / 2.0
                    vnormal = headingDir
                    vup = LVector3f(0.0, 0.0, 1.0)
                    fList.append(CellFace.getSquareFace(
                        vcenter, 
                        vnormal, 
                        vup,
                        sc.inRadius,
                        (sc.outRadius-sc.inRadius) / 2.0,
                        1.0))

        for cc in cellInfo.cornerCompList:
            headingDir = Heading.getDirection3f(cc.heading)
            center = cellInfo.center + headingDir * (cc.outRadius+cc.inRadius) / 2.0
            if(cc.slope == "flat"):
                fList.append(CellFace.getSquareFace(
                    center, 
                    LVector3f(0.0, 0.0, 1.0), 
                    LVector3f(0.0, 1.0, 0.0),
                    (cc.outRadius-sc.inRadius) / 2.0,
                    (cc.outRadius-sc.inRadius) / 2.0,
                    1.0))
            elif(cc.slope == "taperedxn" or cc.slope == "taperedyn" or cc.slope == "taperedxp" or cc.slope == "taperedyp"):
                taperHeadingDir = Heading.getDirection3f(cc.slope[-2:])
                center = center - LVector3f(0.0, 0.0, 1.0) * sc.stepHeight / 2.0
                normal = (LVector3f(0.0, 0.0, 1.0) + taperHeadingDir)
                normal.normalize()
                up = (- taperHeadingDir + LVector3f(0.0, 0.0, 1.0))
                up.normalize()
                fList.append(CellFace.getSquareFace(
                    center, 
                    normal, 
                    up,
                    (cc.outRadius-sc.inRadius) / 2.0,
                    (cc.outRadius-sc.inRadius) / 2.0 * math.sqrt(2.0),
                    1.0))
                # Need to add vertical for futrher drop
                axis = Heading.getAxis(cc.slope[-2:])
                drop = cc.xdrop if axis == "x" else cc.ydrop
                for lvl in range(1,drop):
                    vcenter = cellInfo.center + headingDir * (cc.outRadius+cc.inRadius) / 2.0 + taperHeadingDir * (cc.outRadius-cc.inRadius) / 2.0 - LVector3f(0.0, 0.0, 1.0) * sc.stepHeight * 3.0 / 2.0
                    vnormal = taperHeadingDir
                    vup = LVector3f(0.0, 0.0, 1.0)
                    fList.append(CellFace.getSquareFace(
                        vcenter, 
                        vnormal, 
                        vup,
                        (cc.outRadius-sc.inRadius) / 2.0,
                        (sc.outRadius-sc.inRadius) / 2.0,
                        1.0))
            elif(cc.slope == "foldednormal"):
                pass          
            # TODO: CONTINUE HERE
        return fList

###############################################################################
# Cell shape class
class CellShape:

    def __init__(self, center, outRadius, inRadius, zStep):
        self.outRadius = outRadius
        self.inRadius = inRadius
        self.zStep = zStep
        self.center = center
        self.__cacheShape()

    def __cacheShape(self):
        cx = self.center.getX()
        cy = self.center.getY()
        cz = self.center.getZ()
        bz = cz-self.zStep
        ord = self.outRadius
        self.cacheCapTopOuterCornerVerts = {
            "xnyn" : LVector3f(cx-ord, cy-ord, cz),
            "xpyn" : LVector3f(cx+ord, cy-ord, cz), 
            "xpyp" : LVector3f(cx+ord, cy+ord, cz),
            "xnyp" : LVector3f(cx-ord, cy+ord, cz)}
        ird = self.inRadius
        self.cacheCapTopInnerCornerVerts = {
            "xnyn" : LVector3f(cx-ird, cy-ird, cz),
            "xpyn" : LVector3f(cx+ird, cy-ird, cz), 
            "xpyp" : LVector3f(cx+ird, cy+ird, cz),
            "xnyp" : LVector3f(cx-ird, cy+ird, cz)}

    # Vertices of the top block face
    def __getCapTopOuterCornerVerts(self):
        c = self.cacheCapTopOuterCornerVerts
        vList = []
        for dir, vec in c.items():
            vList.append(vec)
        return vList

    # Vertices of the side block face
    def __getCapSideOuterCornerVerts(self, zOffset, orientation):
        c = self.cacheCapTopOuterCornerVerts
        refList = []
        refList.append(c["xnyp"])
        refList.append(c["xnyn"])
        refList.append(c["xpyn"])
        refList.append(c["xpyp"])
        refList.append(c["xnyp"])
        sides = ["xn", "yn", "xp", "yp"]
        d = sides.index(orientation)

        zb = LVector3f(0.0, 0.0, zOffset+self.zStep)
        zt = LVector3f(0.0, 0.0, zOffset)

        vList = []
        vList.append(refList[d]-zb)
        vList.append(refList[d+1]-zb)
        vList.append(refList[d+1]-zt)
        vList.append(refList[d]-zt)
        return vList

    # Vertices of tapered inner top face
    def __getCapTopInnerCornerVerts(self):
        c = self.cacheCapTopInnerCornerVerts
        vList = []
        for dir, vec in c.items():
            vList.append(vec)
        return vList
  
    def __getSquareTexCoords():
        tc = [ 
            LVector2f(0.0, 0.0), 
            LVector2f(1.0, 0.0), 
            LVector2f(1.0, 1.0), 
            LVector2f(0.0, 1.0)]
        return tc

    def __getCropSquareTexCoords(xnCrop, ynCrop, xpCrop, ypCrop):
        tc = [ 
            LVector2f(xnCrop, ynCrop), 
            LVector2f(1.0-xpCrop, ynCrop), 
            LVector2f(1.0-xpCrop, 1.0-ypCrop), 
            LVector2f(xnCrop, 1.0-ypCrop) ]
        return tc

    def __getBlockFloorFace(self):
        face = CellFace()
        face.verts = self.__getCapTopOuterCornerVerts()
        face.texCoords = CellShape.__getSquareTexCoords()
        face.normal = CellFace.getNormal(face.verts)
        face.triangles = CellFace.getTriFan(face.verts)
        return face

    def __getBlockSideFace(self, ZOffset, orientation):
        face = CellFace()
        face.verts = self.__getCapSideOuterCornerVerts(ZOffset, orientation)
        face.normal = CellFace.getNormal(face.verts)
        texYnOffset = (2 * self.outRadius - self.zStep) / (2 * self.outRadius)
        face.texCoords = CellShape.__getCropSquareTexCoords(0.0, 0.0, 0.0, texYnOffset)
        face.triangles = CellFace.getTriFan(face.verts)
        return face 

    def getBlockFacesNeeded(self, sidesNeeded):
        fList = []
        fList.append(self.__getBlockFloorFace())
        for side, zOffsetList in sidesNeeded.items():
            for zOffset in zOffsetList:
                fList.append(self.__getBlockSideFace(zOffset, side))
        return fList

###############################################################################
# Worker class meshing one cell of the terrain
class TerrainCellMesher:

    class NeighbCell:
        def __init__(self, di, dj):
            # Is it inside the terrain
            self.valid = False

            # Location
            self.di = di
            self.dj = dj

            # Properties
            self.heightDrop = 0 #difference in height increments (positive = lower)

    def __init__(self, terrainHeightMap, textureScheme, style):
        # Parameters      
        self.cellOutRadius = 1.0
        self.cellInRadius = 0.5
        self.mapHeightStep = 0.5
        
        # Source Data
        self.heightMap = terrainHeightMap
        self.textureScheme = textureScheme
        self.style = style

        # Cell Information
        self.height = 0 #height in map increments
        self.sideCell = {}
        for side in Heading.AllSides:
            self.sideCell[side] = self.NeighbCell(
                Heading.getDirection2i(side).getX(), 
                Heading.getDirection2i(side).getY())

        self.cellInfo = CellInfo(LVector3f(0.0, 0.0, 0.0))

    # Private
    def __updateCellTapered(self, i, j):
        self.__updateCellInfo(i, j)
        center = LVector3f(self.cellCenter.getX(), self.cellCenter.getY(), self.heightMap.getZHeightFromIJ(i, j))
        self.cellInfo = CellInfo(center)
        self.cellInfo.centerComp.radius = self.cellInRadius
        for sc in self.cellInfo.sideCompList:
            sc.inRadius = self.cellInRadius
            sc.outRadius = self.cellOutRadius
            sc.stepHeight = self.mapHeightStep
            sc.drop = self.sideCell[sc.heading].heightDrop
            sc.slope = "flat" if sc.drop <= 0 else "tapered"
        for cc in self.cellInfo.cornerCompList:
            cc.inRadius = self.cellInRadius
            cc.outRadius = self.cellOutRadius
            cc.stepHeight = self.mapHeightStep
            cc.cdrop = self.sideCell[cc.heading].heightDrop
            adjXHeading = Heading.getAdjascentXHeading(cc.heading)
            cc.xdrop = self.sideCell[adjXHeading].heightDrop
            adjYHeading = Heading.getAdjascentYHeading(cc.heading)
            cc.ydrop = self.sideCell[adjYHeading].heightDrop
            if(cc.xdrop > 0 and cc.ydrop <= 0):
                cc.slope = "tapered" + adjXHeading
            elif(cc.xdrop <= 0 and cc.ydrop > 0):
                cc.slope = "tapered" + adjYHeading
            elif(cc.xdrop == 0 and cc.ydrop == 0 and cc.cdrop > 0):
                cc.slope = "foldedtangential"
            elif(cc.xdrop > 0 and cc.ydrop > 0 and cc.cdrop > 0):
                cc.slope = "foldednormal"
            elif(cc.xdrop > 0 and cc.ydrop > 0 and cc.cdrop == 0):
                # this could be either tangential or normal, choosing tangential since scheme favors valleys over hills
                cc.slope = "foldedtangential"
            else: #if cc.drop <= 0:
                cc.slope = "flat"


    def __updateCellInfo(self, i, j):
        self.cellCenter = self.heightMap.getXYLocationFromIJ(LVector2i(i,j))
        self.k = self.heightMap.getKHeightFromIJ(i, j)
        for dir,cell in self.sideCell.items():
            if(self.heightMap.isValid(i + cell.di, j + cell.dj)):
                cell.valid = True
                cell.heightDrop = self.k - self.heightMap.getKHeightFromIJ(i+cell.di, j+cell.dj)
            else:
                cell.valid = False
                cell.heightDrop = 0     

    def __meshCellBlockStyle(self, mesh, i, j):
        # Initialize shape
        center = LVector3f(self.cellCenter.getX(), self.cellCenter.getY(), self.heightMap.getZHeightFromIJ(i, j))
        cellShape = CellShape(center, self.cellOutRadius, self.cellInRadius, self.mapHeightStep)
        
        # Fill cell
        sidesNeeded = { "xn" : [], "yn" : [], "xp" : [], "yp" : [] }
        for side in Heading.DirectSides:
            neighb = self.sideCell[side]
            for drop in range(0, neighb.heightDrop):
                sidesNeeded[side].append(drop * self.mapHeightStep)
        fList = cellShape.getBlockFacesNeeded(sidesNeeded) 
        for f in fList:
            f.texMat = self.textureScheme.getMaterial(self.heightMap.getKHeightFromIJ(i, j), f.normal)
            mesh.addFace(self.textureScheme, f)

    def __meshCellTaperedStyle(self, mesh, i, j):
        # Initialize shape
        center = LVector3f(self.cellCenter.getX(), self.cellCenter.getY(), self.heightMap.getZHeightFromIJ(i, j))
        cellShape = CellShape2()
        fList = cellShape.getFaces(self.cellInfo) 
        for f in fList:
            f.texMat = self.textureScheme.getMaterial(self.heightMap.getKHeightFromIJ(i, j), f.normal)
            mesh.addFace(self.textureScheme, f)    
    
    def meshCell(self, mesh, i, j):
        self.__updateCellInfo(i, j)
        if(self.style == "blockStyle"):
            self.__meshCellBlockStyle(mesh, i, j)
        else:
            self.__updateCellTapered(i, j)
            self.__meshCellTaperedStyle(mesh, i, j)

###############################################################################
# Worker class generating the terrain mesh
class TerrainMesher:

    def __init__(self):
        pass

    def generateTerrain(self, size):
        self.size = size
        self.heightMap = TerrainHeightMap(self.size)
        self.heightMap.generateTerrain()
        self.textureScheme = TextureScheme()
    
    def meshTerrain(self, style):
        cellMesher = TerrainCellMesher(self.heightMap, self.textureScheme, style)
        terrainMesh = TerrainMesh()
        for i in range(self.size):
            for j in range(self.size):
                cellMesher.meshCell(terrainMesh, i, j)

        return terrainMesh.makeGeom()


