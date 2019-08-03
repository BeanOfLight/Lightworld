#!/usr/bin/env python

# Author: Bastien Pesenti (bpesenti@yahoo.fr)
# Date: 7/26/2019

from panda3d.core import StackedPerlinNoise2, PNMImage
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles, GeomVertexWriter
from panda3d.core import LVector3f, LVector3i, LVector2f, LVector2i
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
        self.__terrainImage = PNMImage(self.size, self.size, 1)
    
    def generateTerrain(self):
        #Perlin Noise Base
        scale = 0.5 * 64 / self.size
        stackedNoise = StackedPerlinNoise2(scale, scale, 8, 2, 0.5, self.size, 0)
        self.__terrainImage.perlinNoiseFill(stackedNoise)

        #Make it look a bit more natural
        for i in range(self.size):
            for j in range(self.size):
                g = self.__terrainImage.getGray(i,j)
                # make between -0.5 and 1, more land than water
                g = (g-0.25)/0.75
                # make mountain more spiky and plains more flat
                if g>0:
                    g = g ** 2
                # return to 0.25 to 1 range
                g = (g+1)/2
                self.__terrainImage.setGray(i,j,g)
        
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
        return round((self.__terrainImage.getGray(i,j)-0.5)*20)

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
# Cell shape class
class CellShape:

    #  (7) xnyp   (6) yp   (5) xpyp
    #           +--------+
    #           |        |
    #    (0) xn |        | (4) xp
    #           |        |
    #           +--------+
    #  (1) xnyn   (2) yn   (3) xpyn

    def __init__(self):
        pass

    def getBlockFloorFace(XYZCellCenter, radius):
        face = CellFace()
        cx = XYZCellCenter.getX()
        cy = XYZCellCenter.getY()
        cz = XYZCellCenter.getZ()
        r = radius
        face.verts = [ LVector3f(cx-r, cy-r, cz), LVector3f(cx+r, cy-r, cz), LVector3f(cx+r, cy+r, cz), LVector3f(cx-r, cy+r, cz)]
        face.texCoords = [ LVector2f(0.0, 0.0), LVector2f(1.0, 0.0), LVector2f(1.0, 1.0), LVector2f(0.0, 1.0)]
        face.normal = LVector3f(0.0, 0.0, 1.0)
        face.triangles = [ LVector3i(0, 1, 2), LVector3i(0, 2, 3) ]
        return face

    def getBlockSideFace(XYZCellCenter, radius, ZOffset, ZHeight, orientation):
        face = CellFace()
        cx = XYZCellCenter.getX()
        cy = XYZCellCenter.getY()
        cz = XYZCellCenter.getZ()
        r = radius
        zo = ZOffset
        zh = ZHeight
        if(orientation == "xn"):
            x = cx-r
            y = cy
            z = cz-zo
            face.verts = [ LVector3f(x, y+r, z-zh), LVector3f(x, y-r, z-zh), LVector3f(x, y-r, z), LVector3f(x, y+r, z)]
            face.normal = LVector3f(-1.0, 0.0, 0.0)
        elif(orientation == "yn"):
            x = cx
            y = cy-r
            z = cz-zo
            face.verts = [ LVector3f(x-r, y, z-zh), LVector3f(x+r, y, z-zh), LVector3f(x+r, y, z), LVector3f(x-r, y, z)]
            face.normal = LVector3f(0.0, -1.0, 0.0)
        elif(orientation == "xp"):
            x = cx+r
            y = cy
            z = cz-zo
            face.verts = [ LVector3f(x, y-r, z-zh), LVector3f(x, y+r, z-zh), LVector3f(x, y+r, z), LVector3f(x, y-r, z)]
            face.normal = LVector3f(-1.0, 0.0, 0.0)
        elif(orientation == "yp"):
            x = cx
            y = cy+r
            z = cz-zo
            face.verts = [ LVector3f(x+r, y, z-zh), LVector3f(x-r, y, z-zh), LVector3f(x-r, y, z), LVector3f(x+r, y, z)]
            face.normal = LVector3f(0.0, -1.0, 0.0)
        face.texCoords = [ LVector2f(0.0, 0.0), LVector2f(1.0, 0.0), LVector2f(1.0, 1.0), LVector2f(0.0, 1.0)]
        face.triangles = [ LVector3i(0, 1, 2), LVector3i(0, 2, 3) ]
        return face 

    def getTapereFloorFace(XYZCellCenter, fullRadius, offsetRadius, taperedSides, taperedCorner):
        face = CellFace()

        cx = XYZCellCenter.getX()
        cy = XYZCellCenter.getY()
        cz = XYZCellCenter.getZ()
        frd = fullRadius
        ord = offsetRadius
        r = {"xn" : frd, "yn" : frd, "xp": frd, "yp" : frd }
        tcx = 0.5
        tcy = 0.5
        tfrd = 0.5
        tord = 0.5 * offsetRadius / fullRadius
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

        face.normal = LVector3f(0.0, 0.0, 1.0)
        nv = len(face.verts)
        for v in range(1,nv-1):
            face.triangles.append(LVector3i(0, v, v+1))
        return face

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
    
    def __meshCellTaperedStyle(self, mesh, i, j):
        # Cell properties
        center = LVector3f(self.cellCenter.getX(), self.cellCenter.getY(), self.heightMap.getZHeightFromIJ(i, j))
        radius = self.cellOutRadius
        offsetRadius = self.cellInRadius
        
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
        face = CellShape.getTapereFloorFace(center, radius, offsetRadius, taperedSide, taperedCorner)
        face.texMat = self.textureScheme.getMaterial(self.heightMap.getKHeightFromIJ(i, j), face.normal)
        mesh.addFace(self.textureScheme, face)
    
    def __meshCellBlockStyle(self, mesh, i, j):
        # Construct geometry
        center = LVector3f(self.cellCenter.getX(), self.cellCenter.getY(), self.heightMap.getZHeightFromIJ(i, j))
        radius = self.cellOutRadius
        # Fill floor cell
        face = CellShape.getBlockFloorFace(center, radius)
        face.texMat = self.textureScheme.getMaterial(self.heightMap.getKHeightFromIJ(i, j), face.normal)
        mesh.addFace(self.textureScheme, face)
        # Fill sides cell
        for side in self.directSides:
            neighb = self.sideCell[side]
            for drop in range(0, neighb.heightDrop):
                face = CellShape.getBlockSideFace(center, radius, drop * self.mapHeightStep, self.mapHeightStep, side)
                face.texMat = self.textureScheme.getMaterial(self.heightMap.getKHeightFromIJ(i, j), face.normal)
                mesh.addFace(self.textureScheme, face)

    def meshCell(self, mesh, i, j):
        self.__updateCellInfo(i, j)
        if(self.style == "blockStyle"):
            self.__meshCellBlockStyle(mesh, i, j)
        else:
            self.__meshCellTaperedStyle(mesh, i, j)

###############################################################################
# Worker class generating the terrain mesh
class TerrainMesher:

    def __init__(self, size):
        self.size = size
        self.style = "blockStyle" # "blockStyle"

    def meshTerrain(self):
        self.heightMap = TerrainHeightMap(self.size)
        self.heightMap.generateTerrain()
        self.textureScheme = TextureScheme()
        cellMesher = TerrainCellMesher(self.heightMap, self.textureScheme, self.style)

        terrainMesh = TerrainMesh()
        for i in range(self.size):
            for j in range(self.size):
                cellMesher.meshCell(terrainMesh, i, j)

        return terrainMesh.makeGeom()


