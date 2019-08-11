#########################################################################################
# LightWorld
# meshing.py
# Author: Bastien Pesenti (bpesenti@yahoo.fr)
# Date: 8/10/2019


###############################################################################
# Container for the Environment Mesh Data (terrain, water, etc...)
class EnvironmentMesh:
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
            self.color.addData4f(1.0, 1.0, 1.0, 0.75)
        for tc in face.texCoords:
            schemeTC = textureScheme.getUVFromXY(face.texMat, tc.getX(), tc.getY())
            self.texcoord.addData2f(schemeTC.getX(), schemeTC.getY())               
        mv = self.numVerts
        for t in face.triangles:
            self.tris.addVertices(mv+t.getX(), mv+t.getY(), mv+t.getZ())
        self.numVerts += len(face.verts)

    def makeGeom(self):
        geom = Geom(self.vdata)
        geom.addPrimitive(self.tris)
        return geom