from fea.node import Node
from fea.element import Element
from fea.solver import create_global_matrix,build_force_vector,apply_boundary_conditions,solve_system
import numpy as np

def test_three_node_spring_system():
    n0 = Node(identifier=0, posx=0.0, is_fixed=True)
    n1 = Node(identifier=1, posx=1.0)
    n2 = Node(identifier=2, posx=2.0, force=10)

    e0 = Element(stiffness=5, leftnode=n0, rightnode=n1)
    e1 = Element(stiffness=3, leftnode=n1, rightnode=n2)

    K = create_global_matrix([n0, n1, n2], [e0, e1])
    F = build_force_vector([n0, n1, n2])
    K_r, F_r = apply_boundary_conditions(K, F, [n0, n1, n2])
    u = solve_system(K_r, F_r)

    assert np.allclose(u, [2.0, 5.333333], atol=1e-4)
    
test_three_node_spring_system