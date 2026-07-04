import numpy as np 

class Element:
    def __init__(self,E,A,leftnode = None, rightnode = None):
        self.leftnode = leftnode
        self.rightnode = rightnode
        self.E = E
        self.A = A


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
        


    
    
        
    

