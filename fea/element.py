import numpy as np 
from fea.solver import get_dofs

class Element:
    def __init__(self,E,A,leftnode = None, rightnode = None):
        self.leftnode = leftnode
        self.rightnode = rightnode
        self.E = E
        self.A = A

    def get_nodes(self):
        return[self.leftnode, self.rightnode]

    def get_length(self):
        delta_y=self.rightnode.posy-self.leftnode.posy
        delta_x=self.rightnode.posx-self.leftnode.posx
        length=np.sqrt(delta_y*delta_y+delta_x*delta_x)
        return length
        
    def get_angle(self):
        delta_y=self.rightnode.posy-self.leftnode.posy
        delta_x=self.rightnode.posx-self.leftnode.posx
        angle = np.arctan2(delta_y, delta_x)
        return angle

    def get_stiffness(self):
        stiffness = (self.E * self.A)/self.get_length()
        return stiffness
    
    def create_stiffness_matrix(self):
        theta = self.get_angle()
        c = np.cos(theta)
        s = np.sin(theta)
        c2 = c**2
        s2 = s**2
        cs = c*s
        k = self.get_stiffness()
        K = k * np.array([
            [ c2,  cs, -c2, -cs],
            [ cs,  s2, -cs, -s2],
            [-c2, -cs,  c2,  cs],
            [-cs, -s2,  cs,  s2]
        ])
        return K
    
    def get_stress(self,u):
        theta = self.get_angle()
        length = self.get_length()
        c = np.cos(theta)
        s = np.sin(theta)
        left_dx = u[self.leftnode.identifier*2]
        right_dx = u[self.rightnode.identifier*2]
        left_dy = u[self.leftnode.identifier*2+1]
        right_dy = u[self.rightnode.identifier*2+1]
        delta_dx = right_dx - left_dx
        delta_dy = right_dy - left_dy
        stretch = delta_dx * c + delta_dy * s
        strain = stretch/length
        stress = self.E*strain
        return stress
    
class TriangleElement:
    def __init__(self, E, nu, thickness, node_a, node_b, node_c):
        self.E = E
        self.nu = nu
        self.thickness = thickness
        self.node_a = node_a
        self.node_b = node_b
        self.node_c = node_c

    def get_nodes(self):
        return[self.node_a, self.node_b, self.node_c]
    def get_area(self):
        area = abs(0.5*(self.node_a.posx*(self.node_b.posy-self.node_c.posy)+self.node_b.posx*(self.node_c.posy-self.node_a.posy)+self.node_c.posx*(self.node_a.posy-self.node_b.posy)))
        return area
    
    def get_bc_terms(self):
        b1 = self.node_b.posy-self.node_c.posy
        b2 = self.node_c.posy-self.node_a.posy
        b3 = self.node_a.posy-self.node_b.posy
        c1 = self.node_c.posx-self.node_b.posx
        c2 = self.node_a.posx-self.node_c.posx
        c3 = self.node_b.posx-self.node_a.posx
        return b1, b2, b3, c1, c2, c3
    
    def get_B_matrix(self):
        A = self.get_area()
        b1, b2, b3, c1, c2, c3 = self.get_bc_terms()
        B = 1/(2*A)*np.array([[b1, 0, b2, 0, b3, 0],
                      [0, c1, 0, c2, 0, c3],
                      [c1, b1, c2, b2, c3, b3]])
        return B
    
    def get_D_matrix(self):
        e = self.E
        nu = self.nu
        D = e/(1-nu*nu)*np.array([[1, nu, 0],
                                  [nu, 1 , 0],
                                  [0, 0, (1-nu)/2]])
        return D
    
    def create_stiffness_matrix(self):
        a = self.get_area()
        t = self.thickness
        b = self.get_B_matrix()
        d = self.get_D_matrix()
        K = a*t*(b.T @ d @ b)
        return K
    
    def get_stress(self,u):
        node_list = self.get_nodes()
        dofs = get_dofs(node_list)
        u_local = u[dofs]
        strain = self.get_B_matrix() @ u_local
        stress = self.get_D_matrix() @ strain
        return stress





        


    
    
        
    

