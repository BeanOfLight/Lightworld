#!/usr/bin/env python

# Author: Bastien Pesenti (bpesenti@yahoo.fr)
# Date: 7/26/2019

from panda3d.core import StackedPerlinNoise2, PNMImage
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles, GeomVertexWriter
from panda3d.core import LVector3, LVector2f, LVector2i
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
                # make between -1 and 1, more land than water
                g = (g-0.25)/0.75
                # make mountain more spiky and plains more flat
                if g>0:
                    g = g ** 2
                self.__terrainImage.setGray(i,j,(g+1)/2)

    def isValid(self, i,j):
        return i >= 0 and i < self.size and j >= 0 and j < self.size
    
    def getKHeightFromIJ(self, i, j):
        return round((self.__terrainImage.getGray(i,j)-0.5)*20)/2

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

    def __init__(self, terrainHeightMap):
        # Parameters      
        self.cellOutRadius = 1.0
        self.cellInRadius = 0.5
        self.mapHeightStep = 0.5
        
        # Source Data
        self.heightMap = terrainHeightMap

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
        self.k = self.heightMap.getKHeightFromIJ(i, j)
        for dir,cell in self.sideCell.items():
            if(self.heightMap.isValid(i + cell.di, j + cell.dj)):
                cell.valid = True
                cell.heightDrop = self.k - self.heightMap.getKHeightFromIJ(i+cell.di, j+cell.dj)
            else:
                cell.valid = False

    def __meshCellFloor(self, mesh, i,j):
        # radius of each sides
        sideRadius = {}
        for dir in self.directSides:
            needOffset = (self.sideCell[dir].valid and self.sideCell[dir].heightDrop > 0)
            sideRadius[dir] = self.cellInRadius if needOffset else self.cellOutRadius

        # vertex pos coords
        numNewVerts = 0
        cellCenter = self.heightMap.getXYLocationFromIJ(LVector2i(i,j))
        for side in self.diagonalSides:
            x = cellCenter.getX() + self.cellOutRadius * self.sideCell[side].di
            y = cellCenter.getY() + self.cellOutRadius * self.sideCell[side].dj
            z = self.heightMap.getZHeightFromIJ(i, j)
            mesh.vertex.add_data3(x, y, z)
            numNewVerts += 1    

        # vertex tex coords
        for side in self.diagonalSides:
            x = 0.25 + self.sideCell[side].di * 0.25
            y = 0.25 + self.sideCell[side].dj * 0.25
            mesh.texcoord.addData2f(x, y)
        
        # triangles
        for index in range (1, numNewVerts-1):
            mesh.tris.addVertices(
                mesh.numVerts, 
                mesh.numVerts+index, 
                mesh.numVerts+index+1)
        mesh.numVerts += numNewVerts

        # normals
        for x in range(4):
            mesh.normal.addData3(0,0,1)

        # color
        for x in range(4):
            mesh.color.addData4f(1.0, 1.0, 1.0, 1.0)
    
    def meshCell(self, mesh, i,j):
        self.__updateCellInfo(i,j)
        self.__meshCellFloor(mesh, i,j)


###############################################################################
# Worker class generating the terrain mesh
class TerrainMesher:

    def __init__(self, size):
        self.size = size

    def meshTerrain(self):
        self.heightMap = TerrainHeightMap(self.size)
        self.heightMap.generateTerrain()
        cellMesher = TerrainCellMesher(self.heightMap)

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


