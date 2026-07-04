import numpy as np 

class Element:
    def __init__(self,stiffness,leftnode = None, rightnode = None):
        self.leftnode = leftnode
        self.rightnode = rightnode
        self.stiffness = stiffness
    def create_stiffness_matrix(self):
        stiffness_matrix = np.array([[self.stiffness, -self.stiffness], [-self.stiffness,self.stiffness]])
        return stiffness_matrix
    

