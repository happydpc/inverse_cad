from scene import Scene

import random
import math

class Feature():
    def __repr__(self): return str(self)
    def __eq__(self,o): return str(self) == str(o)
    def __ne__(self,o): return not (self == o)
    def __hash__(self): return hash(str(self))

class Vertex(Feature):
    def __init__(self,x,y=None,z=None):
        if y is None:
            x,y,z = x.x,x.y,x.z
        self.p = (x,y,z)
    def close(self,o,e=0.001):
        d = sum((u - v)**2
                for u,v in zip(self.p,o.p) )**0.5
        return d < e
    def __hash__(self): return hash(self.p)
    def __eq__(self,o):
        return isinstance(o,Vertex) and self.p == o.p
    def __ne__(self,o):
        return not (self == o)
    def __str__(self):
        return f"Vertex{self.p}"
    def __repr__(self): return str(self)
    def __gt__(self,o):
        return self.p > o.p
    def __lt__(self,o):
        return self.p < o.p

class Edge(Feature):
    def __init__(self,u,v):
        if u > v:
            self.e = (u,v)
        else:
            self.e = (v,u)
    
    def __hash__(self): return hash(self.e)
    def __eq__(self,o):
        return isinstance(o,Edge) and self.e == o.e
    def __ne__(self,o):
        return not (self == o)
    def __str__(self):
        return f"Edge{self.e}"
    def __repr__(self): return str(self)

class Face(Feature):
    def __init__(self, cycles):
        assert len(cycles) == 1
        self.cycles = tuple(cycles)
    def __str__(self):
        return f"Face{self.cycles}"
    def __hash__(self):
        return hash(self.cycles)
    def __eq__(self,o):
        return isinstance(o,Face) and self.cycles == o.cycles

class CAD():
    """Purely functional wrapper over Scene"""
    def __init__(self, child=None):
        self.child = child or Scene()

    def extrude(self, face, direction, union=True):
        s = self.child.Clone()
        command = []
        for cs in face + [direction]:
            for c in cs:
                command.append(str(c))
        if union:
            command.append('+')
        else:
            command.append('-')
        print(" ".join(command))
        s.ExtrudeFromString(" ".join(["extrude"] + command))
        return CAD(s)

    def export(self, fn):
        self.child.SaveScene(fn)

    def findClose(self, v):
        candidates = [vp for vp in self.getVertices()
                      if v.close(vp)]
        if candidates: return candidates[0]
        return None


    @staticmethod
    def sample():
        angle = 0
        N = random.choice(range(3,8))
        r = random.random() + 1
        face = [(r,r,0)]
        for _ in range(N - 1):            
            d_angle = 2*math.pi/N#6.28/N

            x,y,_ = face[-1]
            x = x + r*math.cos(angle + d_angle)
            y = y + r*math.sin(angle + d_angle)
            
            angle += d_angle

            face.append((x,y,0))

        c = CAD()
        c = c.extrude(face,(0,0,1))

        # f = 0.5 + 0.5*random.random()
        # face = [(x*f,y*f,1)
        #         for x,y,_ in face ]
        # d = 0.2 + 0.7*random.random()
        # c = c.extrude(face,(0,0,-d),False)
        return c

    def getVertices(self):
        N = self.child.GetSceneVertexNumber()
        return [Vertex(v.x,v.y,v.z)
                for n in range(N)
                for v in [self.child.GetSceneVertex(n)] ]

    def getEdges(self):
        return list({Edge(Vertex(self.child.GetSceneVertex(e.source)),
                          Vertex(self.child.GetSceneVertex(e.target)))
                     for n in range(self.child.GetSceneHalfEdgeNumber())
                     for e in [self.child.GetSceneHalfEdge(n)] })

    def getFaces(self):
        fs = set()
        for n in range(self.child.GetSceneHalfFacetNumber()):
            f = self.child.GetSceneHalfFacet(n)
            cycles = []
            for cycle in f.cycles:
                thisCycle = []
                for e in cycle:                
                    e = self.child.GetSceneHalfEdge(e)
                    e = Edge(Vertex(self.child.GetSceneVertex(e.source)),
                         Vertex(self.child.GetSceneVertex(e.target)))
                    thisCycle.append(e)
                    
                # print()
                cycles.append(frozenset(thisCycle))
            fs.add(Face(cycles))
        return fs
    
    def getFeatures(self):
        # mapping from vertex to index and vice versa
        v2n = {}
        n2v = []
        for n in range(self.child.GetSceneVertexNumber()):
            print(n)
            v = self.child.GetSceneVertex(n)
            v = Vertex(v.x,v.y,v.z)
            v2n[v] = n
            n2v.append(v)

        print(v2n)

        e2n = {}
        n2e = []
        for n in range(self.child.GetSceneHalfEdgeNumber()):
            e = self.child.GetSceneHalfEdge(n)
            source = n2v[e.source]
            target = n2v[e.target]

            e2n[e] = n
            n2e.append(e)

    def setTarget(self, c):
        self.child.SetTargetFromOtherScene(c.child)
        
            

class Extrusion():
    def __init__(self, displacement, union, vertices):
        self.vertices, self.displacement, self.union = vertices, displacement, union

    def __str__(self):
        return f"Extrusion({self.f}, D={self.displacement}, U={self.union})"

    def __repr__(self):
        return str(self)

    def compile(self, target):
        from state import NextVertex, Extrude
        vs = list(self.vertices)
        # want to pick a random rotation of the vertices
        if random.random() > 0.5:
            vs.reverse()
        N = random.choice(range(len(vs)))
        vs = vs[N:] + vs[:N]
        compilation = [ NextVertex(v) for v in vs ]
        base = vs[-1]
        connection = Vertex(base.p[0] + self.displacement[0],
                            base.p[1] + self.displacement[1],
                            base.p[2] + self.displacement[2])
        connection = target.findClose(connection)
        if connection is None: return None
        compilation.append(Extrude(connection, self.union))
        return compilation

    def execute(self,c):
        return c.extrude([v.p for v in self.vertices],
                         self.displacement,
                         self.union)

    @staticmethod
    def sample(c):
        angle = 0
        N = random.choice(range(3,8))
        r = random.random() + 1
        face = [Vertex(r,r,0)]
        for _ in range(N - 1):            
            d_angle = 2*math.pi/N#6.28/N

            x,y,_ = face[-1].p
            x = x + r*math.cos(angle + d_angle)
            y = y + r*math.sin(angle + d_angle)
            
            angle += d_angle

            face.append(Vertex(x,y,0))
        return Extrusion((0,0,1),True,face)

class Program():
    def __init__(self, commands):
        self.commands = commands

    def execute(self,c):
        for k in self.commands: c = k.execute(c)
        return c

    def compile(self, target):
        actions = []
        for k in self.commands:
            actions.extend(k.compile(target))
        return actions

    def __str__(self):
        return f"Program{self.commands}"

    def __repr__(self):
        return str(self)

    @staticmethod
    def sample(s):
        return Program([Extrusion.sample(s)])
            
        
        
if __name__ == "__main__":
    for i in range(1):
        
        c = CAD.sample()
        v = c.getVertices()
        e = c.getEdges()
        f = c.getFaces()
        print(len(f),"faces")
        print(f)
        #import pdb; pdb.set_trace()
        
        
        