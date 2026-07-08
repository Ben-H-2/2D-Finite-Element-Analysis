from typing import Optional

import numpy as np 
from fea.solver import get_dofs
from abc import ABC, abstractmethod
from fea.material import Material
from fea.node import Node

class ElementBase(ABC):
    @abstractmethod
    def get_nodes(self) -> list:
        raise NotImplementedError

    @abstractmethod
    def create_stiffness_matrix(self):
        raise NotImplementedError

    @abstractmethod
    def get_stress(self, u, node_index):
        raise NotImplementedError

    @abstractmethod
    def get_von_mises_stress(self, u, node_index):
        raise NotImplementedError

    @abstractmethod
    def get_edge_nodes(self, edge=None):
        raise NotImplementedError

    @abstractmethod
    def get_strain(self, u, node_index):
        raise NotImplementedError

class Element(ElementBase):
    def __init__(self, material: Material, A: float, leftnode: Optional[Node] = None, rightnode: Optional[Node] = None):
        self.leftnode: Optional[Node] = leftnode
        self.rightnode: Optional[Node] = rightnode
        self.material: Material = material
        self.A: float = A

    def get_nodes(self):
        return[self.leftnode, self.rightnode]
    
    def get_edge_nodes(self, edge=None):
        return (self.leftnode, self.rightnode)

    def get_length(self):
        if self.leftnode is None or self.rightnode is None:
            raise ValueError("Element nodes are not assigned.")
        left = self.leftnode
        right = self.rightnode
        delta_y = right.posy - left.posy
        delta_x = right.posx - left.posx
        length = np.sqrt(delta_y * delta_y + delta_x * delta_x)
        return length
        
    def get_angle(self):
        if self.leftnode is None or self.rightnode is None:
            raise ValueError("Element nodes are not assigned.")
        left = self.leftnode
        right = self.rightnode
        delta_y = right.posy - left.posy
        delta_x = right.posx - left.posx
        angle = np.arctan2(delta_y, delta_x)
        return angle

    def get_stiffness(self):
        stiffness = (self.material.E * self.A)/self.get_length()
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
    
    def get_strain(self, u, node_index):
        theta = self.get_angle()
        length = self.get_length()
        c = np.cos(theta)
        s = np.sin(theta)
        left_idx = node_index[self.leftnode]
        right_idx = node_index[self.rightnode]
        left_dx = u[left_idx*2]
        right_dx = u[right_idx*2]
        left_dy = u[left_idx*2+1]
        right_dy = u[right_idx*2+1]
        delta_dx = right_dx - left_dx
        delta_dy = right_dy - left_dy
        stretch = delta_dx * c + delta_dy * s
        strain = stretch/length
        return strain
    
    def get_stress(self, u, node_index):
        strain = self.get_strain(u, node_index)
        stress = self.material.E * strain
        return stress
    
    def get_von_mises_stress(self, full_u, node_index):
        von_mises_stress = self.get_stress(full_u, node_index)
        return von_mises_stress
    
class TriangleElement(ElementBase):
    def __init__(self, material: Material, thickness: float, node_a: Optional[Node], node_b: Optional[Node], node_c: Optional[Node]):
        self.material: Material = material
        self.thickness: float = thickness
        self.node_a: Optional[Node] = node_a
        self.node_b: Optional[Node] = node_b
        self.node_c: Optional[Node] = node_c

    def get_nodes(self):
        return[self.node_a, self.node_b, self.node_c]
    
    def get_edge_nodes(self, edge):
        edges = {
            "ab": (self.node_a, self.node_b),
            "bc": (self.node_b, self.node_c),
            "ca": (self.node_c, self.node_a),
        }
        if edge not in edges:
            raise ValueError("Triangle edge must be 'ab', 'bc', or 'ca'.")
        return edges[edge]

    def get_area(self):
        if self.node_a is None or self.node_b is None or self.node_c is None:
            raise ValueError("Triangle element nodes are not assigned.")
        area = abs(0.5*(self.node_a.posx*(self.node_b.posy-self.node_c.posy)+self.node_b.posx*(self.node_c.posy-self.node_a.posy)+self.node_c.posx*(self.node_a.posy-self.node_b.posy)))
        return area
    
    def get_bc_terms(self):
        if self.node_a is None or self.node_b is None or self.node_c is None:
            raise ValueError("Triangle element nodes are not assigned.")
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
        e = self.material.E
        nu = self.material.nu
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
    
    def get_strain(self, u, node_index):
        dofs = get_dofs(self.get_nodes(), node_index)
        u_local = u[dofs]
        strain = self.get_B_matrix() @ u_local
        return strain
    
    def get_stress(self, u, node_index):
        strain = self.get_strain(u, node_index)
        stress = self.get_D_matrix() @ strain
        return stress
    
    def get_von_mises_stress(self, u, node_index):
        stress = self.get_stress(u, node_index)
        sigma_x, sigma_y, tau_xy = stress
        von_mises = np.sqrt(sigma_x**2-sigma_x*sigma_y+sigma_y**2+3*tau_xy**2)
        return von_mises
