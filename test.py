from fea.node import Node
from fea.element import Element,TriangleElement
from fea.solver import create_global_matrix,build_force_vector,apply_boundary_conditions,solve_system,expand_displacements,get_dofs
import numpy as np

def test_three_node_spring_system():
    n0 = Node(identifier=0, posx=0.0, is_fixed_x=True, is_fixed_y=True)
    n1 = Node(identifier=1, posx=1.0,is_fixed_y=True)
    n2 = Node(identifier=2, posx=2.0, force_x=10,is_fixed_y=True)

    e0 = Element(E=5, A=1, leftnode=n0, rightnode=n1)
    e1 = Element(E=3, A=1, leftnode=n1, rightnode=n2)

    K = create_global_matrix([n0, n1, n2], [e0, e1])
    F = build_force_vector([n0, n1, n2])
    K_r, F_r, remove = apply_boundary_conditions(K, F, [n0, n1, n2])
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

    assert np.isclose(F_full[1] + F_full[3], 10.0, atol=1e-6)   
    assert np.isclose(F_full[0] + F_full[2], 0.0, atol=1e-6)    

    stress_e1 = e1.get_stress(full_u)
    stress_e2 = e2.get_stress(full_u)
    assert np.isclose(stress_e1, stress_e2, atol=1e-3)

def test_triangle_element_system():
    n0 = Node(identifier=0, posx=0.0, posy=0.0, is_fixed_x=True, is_fixed_y=True)
    n1 = Node(identifier=1, posx=3.0, posy=1.0, is_fixed_x=True, is_fixed_y=True)
    n2 = Node(identifier=2, posx=1.0, posy=4.0, force_x=1000, force_y=-500)

    nodes = [n0, n1, n2]
    tri = TriangleElement(E=200e9, nu=0.3, thickness=0.01, node_a=n0, node_b=n1, node_c=n2)
    elements = [tri]

    K = create_global_matrix(nodes, elements)
    F = build_force_vector(nodes)
    K_r, F_r, remove = apply_boundary_conditions(K, F, nodes)
    u_reduced = solve_system(K_r, F_r)
    full_u = expand_displacements(u_reduced, remove, len(nodes)*2)
    F_full = K @ full_u

    assert np.isclose(F_full[4], 1000.0, atol=1e-6)
    assert np.isclose(F_full[5], -500.0, atol=1e-6)

    total_fx = F_full[0] + F_full[2] + F_full[4]
    total_fy = F_full[1] + F_full[3] + F_full[5]
    assert np.isclose(total_fx, 0.0, atol=1e-6)
    assert np.isclose(total_fy, 0.0, atol=1e-6)

    assert np.allclose(K.toarray(), K.toarray().T)

def test_multi_triangle_mesh():
    n0 = Node(identifier=0, posx=0.0, posy=0.0, is_fixed_x=True, is_fixed_y=True)
    n1 = Node(identifier=1, posx=2.0, posy=0.0, is_fixed_x=True, is_fixed_y=True)
    n2 = Node(identifier=2, posx=2.0, posy=1.0, force_x=1000)
    n3 = Node(identifier=3, posx=0.0, posy=1.0)

    nodes = [n0, n1, n2, n3]

    tri1 = TriangleElement(E=200e9, nu=0.3, thickness=0.01, node_a=n0, node_b=n1, node_c=n2)
    tri2 = TriangleElement(E=200e9, nu=0.3, thickness=0.01, node_a=n0, node_b=n2, node_c=n3)

    elements = [tri1, tri2]

    K = create_global_matrix(nodes, elements)
    F = build_force_vector(nodes)
    K_r, F_r, remove = apply_boundary_conditions(K, F, nodes)
    u_reduced = solve_system(K_r, F_r)
    full_u = expand_displacements(u_reduced, remove, len(nodes)*2)
    F_full = K @ full_u

    assert K.shape == (8, 8)
    assert np.allclose(K.toarray(), K.toarray().T)

    total_fx = F_full[0] + F_full[2] + F_full[4] + F_full[6]
    total_fy = F_full[1] + F_full[3] + F_full[5] + F_full[7]
    assert np.isclose(total_fx, 0.0, atol=1e-6)
    assert np.isclose(total_fy, 0.0, atol=1e-6)


test_three_node_spring_system()
test_triangle_truss_system()
test_triangle_element_system()
test_multi_triangle_mesh()
print("All tests passed")




