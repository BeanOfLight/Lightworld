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
# Cell shape class
class CellFace:
    def __init__(self):
        self.verts = []
        self.texCoords = []
        self.texMat = ""
        self.normal = []
        self.triangles = []


###############################################################################
# Cell shape class refactored
class CellShape2:
    
    def __init__(self, center, outRadius, inRadius, zStep):
        self.outRadius = outRadius
        self.inRadius = inRadius
        self.zStep = zStep
        self.center = center

    def getOuterTopFlatFace():
        pass

    def getSideFlatFace():
        pass

    def getInnerTopFlatFace():
        pass

    def getSideTopFlatFace(side):
        pass

    def getCornerTopFlatFace():
        pass

    


###############################################################################
# Cell shape class
class CellShape:

    #  (7) xnyp   (6) yp   (5) xpyp
    #           +--------+
    #           |        |
    #    (0) xn |        | (4) xp
    #           |        |
    #           +--------+
    #  (1) xnyn   (2) yn   (3) xpyn

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

    # Vertices of the tapered side cap faces (flat, tapered, or vertical)
    def __getCapSideTaperedVerts(self, orientation, slope, zOffset):
        c = self.cacheCapTopInnerCornerVerts
        refList = []
        refList.append(c["xnyp"])
        refList.append(c["xnyn"])
        refList.append(c["xpyn"])
        refList.append(c["xpyp"])
        refList.append(c["xnyp"])
        sides = ["xn", "yn", "xp", "yp"]
        d = sides.index(orientation)

        inr = self.inRadius
        our = self.outRadius
        delta = our-inr
        zPush = zOffset
        if(slope=="tapered" or slope=="vertical"):
            zPush = zPush+self.zStep
        pushToOuter = [
            LVector3f(-delta, 0.0, -zPush), 
            LVector3f(0.0, -delta, -zPush), 
            LVector3f(delta, 0.0, -zPush), 
            LVector3f(0.0, delta, -zPush)]
        delta2 = 0
        if(slope=="vertical"):
            delta2 = delta
        pushToOuter2 = [
            LVector3f(-delta2, 0.0, -zOffset), 
            LVector3f(0.0, -delta2, -zOffset), 
            LVector3f(delta2, 0.0, -zOffset), 
            LVector3f(0.0, delta2, -zOffset)]

        vList = []
        vList.append(refList[d]+pushToOuter[d])
        vList.append(refList[d+1]+pushToOuter[d])
        vList.append(refList[d+1]+pushToOuter2[d])
        vList.append(refList[d]+pushToOuter2[d])
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
        
    def __getNormal(listVerts):
        v1 = listVerts[1] - listVerts[0]
        v2 = listVerts[2] - listVerts[1]
        n = v1.cross(v2)
        return n.normalized()        
    
    def __getTriFan(listVerts):
        fan = []
        nv = len(listVerts)
        for v in range(1,nv-1):
            fan.append(LVector3i(0, v, v+1))
        return fan

    def __getBlockFloorFace(self):
        face = CellFace()
        face.verts = self.__getCapTopOuterCornerVerts()
        face.texCoords = CellShape.__getSquareTexCoords()
        face.normal = CellShape.__getNormal(face.verts)
        face.triangles = CellShape.__getTriFan(face.verts)
        return face

    def __getBlockSideFace(self, ZOffset, orientation):
        face = CellFace()
        face.verts = self.__getCapSideOuterCornerVerts(ZOffset, orientation)
        face.normal = CellShape.__getNormal(face.verts)
        texYnOffset = (2 * self.outRadius - self.zStep) / (2 * self.outRadius)
        face.texCoords = CellShape.__getCropSquareTexCoords(0.0, 0.0, 0.0, texYnOffset)
        face.triangles = CellShape.__getTriFan(face.verts)
        return face 

    def getBlockFacesNeeded(self, sidesNeeded):
        fList = []
        fList.append(self.__getBlockFloorFace())
        for side, zOffsetList in sidesNeeded.items():
            for zOffset in zOffsetList:
                fList.append(self.__getBlockSideFace(zOffset, side))
        return fList

    def __geTaperedCenterFloorFace(self):
        face = CellFace()
        face.verts = self.__getCapTopInnerCornerVerts()
        face.texCoords = CellShape.__getSquareTexCoords()
        face.normal = CellShape.__getNormal(face.verts)
        face.triangles = CellShape.__getTriFan(face.verts)
        return face

    def __getTaperedSideFloorFace(self, orientation, tapered, zOffset):
        face = CellFace()
        face.verts = self. __getCapSideTaperedVerts(orientation, tapered, zOffset)
        face.normal = CellShape.__getNormal(face.verts)
        texYnOffset = (2 * self.outRadius - self.zStep) / (2 * self.outRadius) / 1.41
        face.texCoords = CellShape.__getCropSquareTexCoords(0.0, 0.0, 0.0, texYnOffset)
        face.triangles = CellShape.__getTriFan(face.verts)
        return face 

    def getTaperedFacesNeeded(self, sidesNeeded):
        fList = []
        fList.append(self.__geTaperedCenterFloorFace()) 
        for side, zOffsetList in sidesNeeded.items():
            fList.append(self.__getTaperedSideFloorFace(side, "flat" if not zOffsetList else "tapered", 0.0))
            for izo in range(1,len(zOffsetList)):
                fList.append(self.__getTaperedSideFloorFace(side, "vertical", zOffsetList[izo]))
        return fList

    '''
    def getTapereFloorFace(self, taperedSides, taperedCorner):
        face = CellFace()

        cx = self.center.getX()
        cy = self.center.getY()
        cz = self.center.getZ()
        frd = self.outRadius
        ord = self.inRadius
        r = {"xn" : frd, "yn" : frd, "xp": frd, "yp" : frd }
        tcx = 0.5
        tcy = 0.5
        tfrd = 0.5
        tord = 0.5 * self.inRadius / self.outRadius
        tr = {"xn" : tfrd, "yn" : tfrd, "xp": tfrd, "yp" : tfrd }

        for side in taperedSides:
            r[side] = ord
            tr[side] = tord

        if "xnyn" in taperedCorner:
            face.verts.append(LVector3f(cx-frd, cy-ord, cz))
            face.texCoords.append(LVector2f(tcx-tfrd, tcy-tord))
            face.verts.append(LVector3f(cx-ord, cy-frd, cz))
            face.texCoords.append(LVector2f(tcx-tord, tcy-tfrd))
        else:
            face.verts.append(LVector3f(cx-r["xn"], cy-r["yn"], cz))
            face.texCoords.append(LVector2f(tcx-tr["xn"], tcy-tr["yn"]))  

        if "xpyn" in taperedCorner:
            face.verts.append(LVector3f(cx+ord, cy-frd, cz)) 
            face.texCoords.append(LVector2f(tcx+tord, tcy-tfrd))
            face.verts.append(LVector3f(cx+frd, cy-ord, cz)) 
            face.texCoords.append(LVector2f(tcx+tfrd, tcy-tord))
        else:
            face.verts.append(LVector3f(cx+r["xp"], cy-r["yn"], cz)) 
            face.texCoords.append(LVector2f(tcx+tr["xp"], tcy-tr["yn"]))

        if "xpyp" in taperedCorner:
            face.verts.append(LVector3f(cx+frd, cy+ord, cz))
            face.texCoords.append(LVector2f(tcx+tfrd, tcy+tord))
            face.verts.append(LVector3f(cx+ord, cy+frd, cz))
            face.texCoords.append(LVector2f(tcx+tord, tcy+tfrd))
        else:
            face.verts.append(LVector3f(cx+r["xp"], cy+r["yp"], cz))
            face.texCoords.append(LVector2f(tcx+tr["xp"], tcy+tr["yp"]))

        if "xnyp" in taperedCorner:
            face.verts.append(LVector3f(cx-ord, cy+frd, cz))
            face.texCoords.append(LVector2f(tcx-tord, tcy+tfrd))
            face.verts.append(LVector3f(cx-frd, cy+ord, cz))
            face.texCoords.append(LVector2f(tcx-tfrd, tcy+tord))
        else:
            face.verts.append(LVector3f(cx-r["xn"], cy+r["yp"], cz))
            face.texCoords.append(LVector2f(tcx-tr["xn"], tcy+tr["yp"]))

        face.normal = CellShape.__getNormal(face.verts)
        face.triangles = CellShape.__getTriFan(face.verts)
        return face
    '''
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

    #  (7) xnyp   (6) yp   (5) xpyp
    #           +--------+
    #           |        |
    #    (0) xn |        | (4) xp
    #           |        |
    #           +--------+
    #  (1) xnyn   (2) yn   (3) xpyn

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
        self.directSides = [ "xn", "yn", "xp", "yp" ]
        self.diagonalSides = [ "xnyn", "xpyn", "xpyp", "xnyp" ]
        self.sideCell = {
            "xn"   : self.NeighbCell( -1,  0),
            "xnyn" : self.NeighbCell( -1, -1),
            "yn"   : self.NeighbCell(  0, -1),
            "xpyn" : self.NeighbCell(  1, -1),
            "xp"   : self.NeighbCell(  1,  0),
            "xpyp" : self.NeighbCell(  1,  1),
            "yp"   : self.NeighbCell(  0,  1),
            "xnyp" : self.NeighbCell( -1,  1)
        }

    # Private
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
        for side in self.directSides:
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
        cellShape = CellShape(center, self.cellOutRadius, self.cellInRadius, self.mapHeightStep)
        
        sidesNeeded = { "xn" : [], "yn" : [], "xp" : [], "yp" : [] }
        for side in self.directSides:
            neighb = self.sideCell[side]
            for drop in range(0, neighb.heightDrop):
                sidesNeeded[side].append(drop * self.mapHeightStep)
        fList = cellShape.getTaperedFacesNeeded(sidesNeeded) 
        for f in fList:
            f.texMat = self.textureScheme.getMaterial(self.heightMap.getKHeightFromIJ(i, j), f.normal)
            mesh.addFace(self.textureScheme, f)    
    
    '''
    def __meshCellTaperedStyle(self, mesh, i, j):
        # Cell properties
        center = LVector3f(self.cellCenter.getX(), self.cellCenter.getY(), self.heightMap.getZHeightFromIJ(i, j))
        radius = self.cellOutRadius
        offsetRadius = self.cellInRadius
        cellShape = CellShape(center, self.cellOutRadius, self.cellInRadius, self.mapHeightStep)
        
        # Compute tapered sides
        taperedSide = []
        taperedCorner = []
        sc = self.sideCell
        for side in self.directSides:
            if sc[side].heightDrop > 0:
                taperedSide.append(side)
        if sc["xn"].heightDrop == 0 and sc["yn"].heightDrop == 0 and sc["xnyn"].heightDrop > 0:
            taperedCorner.append("xnyn")
        if sc["xp"].heightDrop == 0 and sc["yn"].heightDrop == 0 and sc["xpyn"].heightDrop > 0:
            taperedCorner.append("xpyn")
        if sc["xp"].heightDrop == 0 and sc["yp"].heightDrop == 0 and sc["xpyp"].heightDrop > 0:
            taperedCorner.append("xpyp")
        if sc["xn"].heightDrop == 0 and sc["yp"].heightDrop == 0 and sc["xnyp"].heightDrop > 0:
            taperedCorner.append("xnyp")

        # Fill floor cell                
        face = cellShape.getTapereFloorFace(taperedSide, taperedCorner)
        face.texMat = self.textureScheme.getMaterial(self.heightMap.getKHeightFromIJ(i, j), face.normal)
        mesh.addFace(self.textureScheme, face)

        # Fill sides cell
        #for side in self.directSides:
        #    neighb = self.sideCell[side]
        #    for drop in range(0, neighb.heightDrop):
        #        face = cellShape.getBlockSideFace(drop * self.mapHeightStep, side)
        #        face.texMat = self.textureScheme.getMaterial(self.heightMap.getKHeightFromIJ(i, j), face.normal)
        #        mesh.addFace(self.textureScheme, face)
    '''
    def meshCell(self, mesh, i, j):
        self.__updateCellInfo(i, j)
        if(self.style == "blockStyle"):
            self.__meshCellBlockStyle(mesh, i, j)
        else:
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


