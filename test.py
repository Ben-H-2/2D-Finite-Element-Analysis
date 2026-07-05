from fea.node import Node
from fea.element import Element
from fea.solver import create_global_matrix,build_force_vector,apply_boundary_conditions,solve_system,expand_displacements
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

def test_triangle_truss_system():
    n0 = Node(identifier=0, posx=0.0, posy=0.0, is_fixed_x=True, is_fixed_y=True)
    n1 = Node(identifier=1, posx=2.0, posy=0.0, is_fixed_x=True, is_fixed_y=True)
    n2 = Node(identifier=2, posx=1.0, posy=1.5, force_y=-10)

    nodes = [n0, n1, n2]

    e0 = Element(E=200e9, A=0.001, leftnode=n0, rightnode=n1)
    e1 = Element(E=200e9, A=0.001, leftnode=n0, rightnode=n2)
    e2 = Element(E=200e9, A=0.001, leftnode=n1, rightnode=n2)

    elements = [e0, e1, e2]

    K = create_global_matrix(nodes, elements)
    F = build_force_vector(nodes)
    K_r, F_r, remove = apply_boundary_conditions(K, F, nodes)
    u_reduced = solve_system(K_r, F_r)
    full_u = expand_displacements(u_reduced, remove, len(nodes)*2)
    F_full = K @ full_u

    # Check reaction forces balance the applied load
    assert np.isclose(F_full[1] + F_full[3], 10.0, atol=1e-6)   # vertical equilibrium
    assert np.isclose(F_full[0] + F_full[2], 0.0, atol=1e-6)    # horizontal equilibrium

    # Check the two diagonals carry identical (symmetric) stress
    stress_e1 = e1.get_stress(full_u)
    stress_e2 = e2.get_stress(full_u)
    assert np.isclose(stress_e1, stress_e2, atol=1e-3)