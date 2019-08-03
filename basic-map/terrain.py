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
    def __getUVFromXY(self, material, x, y):
        offset = self.materialOffset[material]
        uv = LVector2f(x,y) * self.scale
        return offset + uv

    def getUVFromXY(self, kHeight, normal, x, y):
        #if(normal.getZ() < 0.2):
        #    return self.__getUVFromXY("rock", x, y)
        if(kHeight<0):
            return self.__getUVFromXY("water", x, y)
        elif(kHeight<1):
            return self.__getUVFromXY("sand", x, y)
        elif(kHeight<7):
            return self.__getUVFromXY("grass", x, y)
        else:
            return self.__getUVFromXY("rock", x, y)

###############################################################################
# Cell shape class
class CellShape:

    class CellFace:
        def __init__(self):
            self.verts = []
            self.texCoords = []
            self.normal = []
            self.triangles = []

    #  (7) xnyp   (6) yp   (5) xpyp
    #           +--------+
    #           |        |
    #    (0) xn |        | (4) xp
    #           |        |
    #           +--------+
    #  (1) xnyn   (2) yn   (3) xpyn

    def __init__(self):
        pass

    def getBasicFloorFace(XYZCellCenter, radius):
        face = CellShape.CellFace()
        cx = XYZCellCenter.getX()
        cy = XYZCellCenter.getY()
        cz = XYZCellCenter.getZ()
        r = radius
        face.verts = [ LVector3f(cx-r, cy-r, cz), LVector3f(cx+r, cy-r, cz), LVector3f(cx+r, cy+r, cz), LVector3f(cx-r, cy+r, cz)]
        face.texCoords = [ LVector2f(0.0, 0.0), LVector2f(1.0, 0.0), LVector2f(1.0, 1.0), LVector2f(0.0, 1.0)]
        face.normal = LVector3f(0.0, 0.0, 1.0)
        face.triangles = [ LVector3i(0, 1, 2), LVector3i(0, 2, 3) ]
        return face

    def getDirectSideTapereFloorFace(XYZCellCenter, fullRadius, offsetRadius, taperedSides, taperedCorner):
        face = CellShape.CellFace()

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

    def getBasicSideFace(XYZCellCenter, radius, ZOffset, ZHeight, orientation):
        face = CellShape.CellFace()
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
        #for side in self.directSides:
        #    needOffset = (self.sideCell[side].valid and self.sideCell[side].heightDrop > 0)
        #    self.sideRadius[side] = self.cellInRadius if needOffset else self.cellOutRadius

    def __fillFace(self, mesh, i, j, face):
        n = face.normal
        for v in face.verts:
            mesh.vertex.add_data3(v.getX(), v.getY(), v.getZ())
            mesh.normal.addData3(n.getX(), n.getY(), n.getZ())
            mesh.color.addData4f(1.0, 1.0, 1.0, 1.0)
        kh = self.heightMap.getKHeightFromIJ(i, j)
        for tc in face.texCoords:
            schemeTC = self.textureScheme.getUVFromXY(kh, n, tc.getX(), tc.getY())
            mesh.texcoord.addData2f(schemeTC.getX(), schemeTC.getY())       
        mv = mesh.numVerts
        for t in face.triangles:
            mesh.tris.addVertices(mv+t.getX(), mv+t.getY(), mv+t.getZ())
        mesh.numVerts += len(face.verts)
    
    def __meshCellFloorTaperedStyle(self, mesh, i, j):
        # Construct geometry
        center = LVector3f(self.cellCenter.getX(), self.cellCenter.getY(), self.heightMap.getZHeightFromIJ(i, j))
        radius = self.cellOutRadius
        offsetRadius = self.cellInRadius
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

        # taperedCorner = [ "xnyn", "xpyn", "xpyp", "xnyp" ]
                
        face = CellShape.getDirectSideTapereFloorFace(center, radius, offsetRadius, taperedSide, taperedCorner)
        # Fill Mesh Structure
        self.__fillFace(mesh, i, j, face)
    
    def __meshCellFloorBlockStyle(self, mesh, i, j):
        # Construct geometry
        center = LVector3f(self.cellCenter.getX(), self.cellCenter.getY(), self.heightMap.getZHeightFromIJ(i, j))
        radius = self.cellOutRadius
        face = CellShape.getBasicFloorFace(center, radius)
        # Fill Mesh Structure
        self.__fillFace(mesh, i, j, face)

    def __meshCellSidesBlockStyle(self, mesh, i, j):
        # Construct geometry
        center = LVector3f(self.cellCenter.getX(), self.cellCenter.getY(), self.heightMap.getZHeightFromIJ(i, j))
        radius = self.cellOutRadius
        for side in self.directSides:
            neighb = self.sideCell[side]
            for drop in range(0, neighb.heightDrop):
                face = CellShape.getBasicSideFace(center, radius, drop * self.mapHeightStep, self.mapHeightStep, side)
                self.__fillFace(mesh, i, j, face)    
         
    def meshCell(self, mesh, i, j):
        self.__updateCellInfo(i, j)
        if(self.style == "blockStyle"):
            self.__meshCellFloorBlockStyle(mesh, i, j)
            self.__meshCellSidesBlockStyle(mesh, i, j)
        else:
            self.__meshCellFloorTaperedStyle(mesh, i, j)
            self.__meshCellSidesBlockStyle(mesh, i, j)

###############################################################################
# Worker class generating the terrain mesh
class TerrainMesher:

    def __init__(self, size):
        self.size = size
        self.style = "taperedStyle" # "blockStyle"

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
"""  
##############################################################################################################
class LightworldTerrain:
    
    def __init__(self, size):
        self.size = size
        self.__terrainImage = self.__generateTerrainImage()

    def __getHeight(self,i,j):
        h = round((self.__terrainImage.getGray(i,j)-0.5)*20)/2
        return h

    def __generateTerrainImage(self):
        #Perlin Noise Base
        terrainImage = PNMImage(self.size, self.size, 1)
        scale = 0.5 * 64 / self.size
        stackedNoise = StackedPerlinNoise2(scale, scale, 8, 2, 0.5, self.size, 0)
        terrainImage.perlinNoiseFill(stackedNoise)

        #Make it look a bit more natural
        for i in range(self.size):
            for j in range(self.size):
                g = terrainImage.getGray(i,j)
                # make between -1 and 1, more land than water
                g = (g-0.25)/0.75
                # make mountain more spiky and plains more flat
                if g>0:
                    g = g ** 2
                terrainImage.setGray(i,j,(g+1)/2)

        return terrainImage

    def getHeightAtPos(self,x,y):
        h = self.__getHeight(round((x+self.size)/2), round((y+self.size)/2))
        return h
    
    def generateTerrainGeom(self):

        #Define format
        format = GeomVertexFormat.getV3n3cpt2()
        vdata = GeomVertexData('square', format, Geom.UHDynamic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        tris = GeomTriangles(Geom.UHDynamic)

        vIndex = 0

        def addTexRock():
            texcoord.addData2f(0.0, 0.0)
            texcoord.addData2f(0.5, 0.0)
            texcoord.addData2f(0.5, 0.5)
            texcoord.addData2f(0.0, 0.5)
        def addTexWater():
            texcoord.addData2f(0.5, 0.0)
            texcoord.addData2f(1.0, 0.0)
            texcoord.addData2f(1.0, 0.5)
            texcoord.addData2f(0.5, 0.5)
        def addTexGrass():
            texcoord.addData2f(0.0, 0.5)
            texcoord.addData2f(0.5, 0.5)
            texcoord.addData2f(0.5, 1.0)
            texcoord.addData2f(0.0, 1.0)
        def addTexSand():
            texcoord.addData2f(0.5, 0.5)
            texcoord.addData2f(1.0, 0.5)
            texcoord.addData2f(1.0, 1.0)
            texcoord.addData2f(0.5, 1.0)

        def addTexFloor(altitude):
            if(altitude<0):
                addTexWater()
            elif(altitude<0.5):
                addTexSand()
            elif(altitude<4):
                addTexGrass()
            else:
                addTexRock()

        def addTexSkirt(altitude, wallHeight):
            if(altitude<=0):
                addTexWater()
            elif(altitude<0.5):
                addTexSand()
            elif(altitude<4) and (wallHeight<1):
                addTexGrass()
            else:
                addTexRock()

        def addTriangleFan(vStart, numVerts):
            for i in range (1, numVerts-1):
                tris.addVertices(vStart, vStart+i, vStart+i+1)
            return vStart + numVerts

        def addSquareVerts(vStart):
            vNext = addTriangleFan(vStart, 4)
            return vNext

        def addFloorSquare(
            x, y, z, xnOffset, xpOffset, ynOffset, ypOffset, vStart):
            vertex.add_data3(x-xnOffset,y-ynOffset, z)
            vertex.add_data3(x+xpOffset,y-ynOffset, z)
            vertex.add_data3(x+xpOffset,y+ypOffset, z)
            vertex.add_data3(x-xnOffset,y+ypOffset, z)
            for x in range(4):
                normal.addData3(0,0,1)
            return addSquareVerts(vStart)

        def addFloorTile(
            x, y, z, 
            cellRadius, offsetRadius,
            xnIndent, xpIndent, ynIndent, ypIndent, 
            xnynIndent, xnypIndent, xpynIndent, xpypIndent, 
            vStart):
            
            # Compute side offsets
            xnOffset = offsetRadius if xnIndent else cellRadius
            xpOffset = offsetRadius if xpIndent else cellRadius
            ynOffset = offsetRadius if ynIndent else cellRadius
            ypOffset = offsetRadius if ypIndent else cellRadius

            numVerts = 0

            # xn yn corner
            if(xnynIndent):
                vertex.add_data3(x-cellRadius, y-offsetRadius, z)
                vertex.add_data3(x-offsetRadius, y-cellRadius, z)
                numVerts += 2
            else:
                vertex.add_data3(x-xnOffset,y-ynOffset, z)
                numVerts += 1

            # xp yn corner
            if(xpynIndent):
                vertex.add_data3(x+offsetRadius, y-cellRadius, z)
                vertex.add_data3(x+cellRadius, y-offsetRadius, z)
                numVerts += 2
            else:
                vertex.add_data3(x+xpOffset,y-ynOffset, z)
                numVerts += 1

            # xp yp corner
            numVerts = 0
            if(xpypIndent):
                vertex.add_data3(x+cellRadius, y+offsetRadius, z)
                vertex.add_data3(x+offsetRadius, y+cellRadius, z)
                numVerts += 2
            else:
                vertex.add_data3(x+xpOffset,y+ynOffset, z)
                numVerts += 1

            # xn yp corner
            numVerts = 0
            if(xnypIndent):
                vertex.add_data3(x-offsetRadius, y+cellRadius, z)
                vertex.add_data3(x-cellRadius, y+offsetRadius, z)
                numVerts += 2
            else:
                vertex.add_data3(x-xnOffset,y+ynOffset, z)
                numVerts += 1

            for x in range(numVerts):
                normal.addData3(0,0,1)
            return addTriangleFan(vStart, numVerts)


        def addSkirtSquareXN(x, y, z, xnOffset, xpOffset, ynOffset, ypOffset, vStart):
            vertex.add_data3(x-1,y+1,z-0.5)
            vertex.add_data3(x-1,y-1,z-0.5)
            vertex.add_data3(x-xnOffset,y-ynOffset,z)
            vertex.add_data3(x-xnOffset,y+ypOffset,z)
            for x in range(4):
                normal.addData3(-1,0,0)
            return addSquareVerts(vStart)

        def addSkirtSquareXP(x, y, z, xnOffset, xpOffset, ynOffset, ypOffset, vStart):
            vertex.add_data3(x+1,y-1,z-0.5)
            vertex.add_data3(x+1,y+1,z-0.5)
            vertex.add_data3(x+xpOffset,y+ypOffset,z)
            vertex.add_data3(x+xpOffset,y-ynOffset,z)
            for x in range(4):
                normal.addData3(1,0,0)
            return addSquareVerts(vStart)

        def addSkirtSquareYP(x, y, z, xnOffset, xpOffset, ynOffset, ypOffset, vStart):
            vertex.add_data3(x+1,y+1,z-0.5)
            vertex.add_data3(x-1,y+1,z-0.5)
            vertex.add_data3(x-xnOffset,y+ypOffset,z)
            vertex.add_data3(x+xpOffset,y+ypOffset,z)
            for x in range(4):
                normal.addData3(0,1,0)
            return addSquareVerts(vStart)
        
        def addSkirtSquareYN(x, y, z, xnOffset, xpOffset, ynOffset, ypOffset, vStart):
            vertex.add_data3(x-1,y-1,z-0.5)
            vertex.add_data3(x+1,y-1,z-0.5)
            vertex.add_data3(x+xpOffset,y-ynOffset,z)
            vertex.add_data3(x-xnOffset,y-ynOffset,z)
            for x in range(4):
                normal.addData3(0,-1,0)
            return addSquareVerts(vStart)

        for i in range(self.size):
            for j in range(self.size):
                # add floor
                x = 2*i-self.size
                y = 2*j-self.size
                z = self.__getHeight(i,j)

                # Compute attributes of the cell for 4 straight directions
                if(i==0):
                    xnBorder = True 
                    xnBottom = -5
                else: 
                    xnBorder = False
                    xnBottom = self.__getHeight(i-1,j)

                if(i==self.size-1):
                    xpBorder = True 
                    xpBottom = -5
                else: 
                    xpBorder = False
                    xpBottom = self.__getHeight(i+1,j)

                if(j==0):
                    ynBorder = True 
                    ynBottom = -5
                else: 
                    ynBorder = False
                    ynBottom = self.__getHeight(i,j-1) 

                if(j==self.size-1):
                    ypBorder = True 
                    ypBottom = -5
                else: 
                    ypBorder = False
                    ypBottom = self.__getHeight(i,j+1)                

                # Compute attributes of the cell for 4 diagonal directions
                if(i==0 or j==0):
                    xnynBorder = True 
                    xnynBottom = -5
                else: 
                    xnynBorder = False
                    xnynBottom = self.__getHeight(i-1,j-1)
                              
                if(i==0 or j==self.size-1):
                    xnypBorder = True 
                    xnypBottom = -5
                else: 
                    xnypBorder = False
                    xnypBottom = self.__getHeight(i-1,j+1)

                if(i==self.size-1 or j==0):
                    xpynBorder = True 
                    xpynBottom = -5
                else: 
                    xpynBorder = False
                    xpynBottom = self.__getHeight(i+1,j-1)
                              
                if(i==self.size-1 or j==self.size-1):
                    xpypBorder = True 
                    xpypBottom = -5
                else: 
                    xpypBorder = False
                    xpypBottom = self.__getHeight(i+1,j+1)

                xnIndent = (xnBorder == False and xnBottom < z)
                xpIndent = (xpBorder == False and xpBottom < z)
                ynIndent = (ynBorder == False and ynBottom < z)
                ypIndent = (ypBorder == False and ypBottom < z)

                xnynIndent = (xnBorder == False and ynBorder == False and xnBottom == z and ynBottom == z and xnynBottom < z)
                xnypIndent = (xnBorder == False and ypBorder == False and xnBottom == z and ypBottom == z and xnypBottom < z)
                xpynIndent = (xpBorder == False and ynBorder == False and xpBottom == z and ynBottom == z and xpynBottom < z)
                xpypIndent = (xpBorder == False and ypBorder == False and xpBottom == z and ypBottom == z and xpypBottom < z)

                
                vIndex = addFloorTile(x, y, z, 1, 0.5,
                        xnIndent, xpIndent, ynIndent, ypIndent, 
                        xnynIndent, xnypIndent, xpynIndent, xpypIndent, 
                        vIndex)

                addTexFloor(z)

                #xn side
                zSide = z
                while zSide > xnBottom:
                    vIndex = addSkirtSquareXN(x, y, zSide, xnOffset, xpOffset, ynOffset, ypOffset, vIndex)
                    if i == 0:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, z-xnBottom)
                    zSide = zSide - 0.5

                #xp side
                zSide = z
                while zSide > xpBottom:
                    vIndex = addSkirtSquareXP(x, y, zSide, xnOffset, xpOffset, ynOffset, ypOffset, vIndex) 
                    if i == self.size-1:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, z-xpBottom)
                    zSide = zSide - 0.5

                #yn side
                zSide = z
                while zSide > ynBottom:
                    vIndex = addSkirtSquareYN(x, y, zSide, xnOffset, xpOffset, ynOffset, ypOffset, vIndex)  
                    if ynBorder:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, z-ynBottom)
                    zSide = zSide - 0.5

                #yp side
                zSide = z
                while zSide > ypBottom:
                    vIndex = addSkirtSquareYP(x, y, zSide, xnOffset, xpOffset, ynOffset, ypOffset, vIndex)  
                    if ypBorder == True:
                        addTexSand()
                    else:
                        addTexSkirt(zSide, z-ypBottom)
                    zSide = zSide - 0.5

        terrainCube = Geom(vdata)
        terrainCube.addPrimitive(tris)
        return terrainCube
"""


