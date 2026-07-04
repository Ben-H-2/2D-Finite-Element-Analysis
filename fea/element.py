import numpy as np 

class Element:
    def __init__(self,stiffness,leftnode = None, rightnode = None):
        self.leftnode = leftnode
        self.rightnode = rightnode
        self.stiffness = stiffness
    def get_angle(self):
        delta_y=self.rightnode.posy-self.leftnode.posy
        delta_x=self.rightnode.posx-self.leftnode.posx
        angle = np.arctan2(delta_y, delta_x)
        return angle
    
    def create_stiffness_matrix(self):
        theta = self.get_angle()
        c = np.cos(theta)
        s = np.sin(theta)
        c2 = c**2
        s2 = s**2
        cs = c*s
        k = self.stiffness
        K = k * np.array([
            [ c2,  cs, -c2, -cs],
            [ cs,  s2, -cs, -s2],
            [-c2, -cs,  c2,  cs],
            [-cs, -s2,  cs,  s2]
        ])
        return K
        
    

