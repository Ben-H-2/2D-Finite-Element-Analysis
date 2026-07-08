from fea.node import Node
from fea.element import Element,TriangleElement
from fea.material import Material
from fea.solver import create_global_matrix,build_force_vector,reduce_system,solve_system,expand_displacements,get_dofs,build_node_index
import numpy as np

def test_three_node_spring_system():
    n0 = Node(identifier=0, posx=0.0, is_fixed_x=True, is_fixed_y=True)
    n1 = Node(identifier=1, posx=1.0,is_fixed_y=True)
    n2 = Node(identifier=2, posx=2.0, force_x=10,is_fixed_y=True)
    node_index = build_node_index([n0, n1, n2])

    mat0 = Material(name="spring0", E=5, nu=0.3)
    mat1 = Material(name="spring1", E=3, nu=0.3)

    e0 = Element(material=mat0, A=1, leftnode=n0, rightnode=n1)
    e1 = Element(material=mat1, A=1, leftnode=n1, rightnode=n2)

    K = create_global_matrix([n0, n1, n2], [e0, e1],node_index)
    F = build_force_vector([n0, n1, n2],node_index)
    K_r, F_r, remove = reduce_system(K, F, [n0, n1, n2],node_index)
    u = solve_system(K_r, F_r)

    u_values = u.toarray().ravel() if hasattr(u, "toarray") else np.asarray(u).ravel()
    assert np.allclose(u_values, [2.0, 5.333333], atol=1e-4)

def test_triangle_truss_system():
    n0 = Node(identifier=0, posx=0.0, posy=0.0, is_fixed_x=True, is_fixed_y=True)
    n1 = Node(identifier=1, posx=2.0, posy=0.0, is_fixed_x=True, is_fixed_y=True)
    n2 = Node(identifier=2, posx=1.0, posy=1.5, force_y=-10)
    node_index = build_node_index([n0, n1, n2])

    nodes = [n0, n1, n2]

    steel = Material(name="steel", E=200e9, nu=0.3)

    e0 = Element(material=steel, A=0.001, leftnode=n0, rightnode=n1)
    e1 = Element(material=steel, A=0.001, leftnode=n0, rightnode=n2)
    e2 = Element(material=steel, A=0.001, leftnode=n1, rightnode=n2)

    elements = [e0, e1, e2]

    K = create_global_matrix(nodes, elements,node_index)
    F = build_force_vector(nodes,node_index)
    K_r, F_r, remove = reduce_system(K, F, nodes,node_index)
    u_reduced = solve_system(K_r, F_r)
    full_u = expand_displacements(u_reduced, remove, len(nodes)*2)
    F_full = K @ full_u

    assert np.isclose(F_full[1] + F_full[3], 10.0, atol=1e-6)   
    assert np.isclose(F_full[0] + F_full[2], 0.0, atol=1e-6)    

    stress_e1 = e1.get_stress(full_u,node_index)
    stress_e2 = e2.get_stress(full_u,node_index)
    assert np.isclose(stress_e1, stress_e2, atol=1e-3)

def test_triangle_element_system():
    n0 = Node(identifier=0, posx=0.0, posy=0.0, is_fixed_x=True, is_fixed_y=True)
    n1 = Node(identifier=1, posx=3.0, posy=1.0, is_fixed_x=True, is_fixed_y=True)
    n2 = Node(identifier=2, posx=1.0, posy=4.0, force_x=1000, force_y=-500)
    node_index = build_node_index([n0, n1, n2])

    nodes = [n0, n1, n2]
    steel = Material(name="steel", E=200e9, nu=0.3)
    tri = TriangleElement(material=steel, thickness=0.01, node_a=n0, node_b=n1, node_c=n2)
    elements = [tri]

    K = create_global_matrix(nodes, elements,node_index)
    F = build_force_vector(nodes,node_index)
    K_r, F_r, remove = reduce_system(K, F, nodes,node_index)
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
    node_index = build_node_index([n0, n1, n2, n3])

    nodes = [n0, n1, n2, n3]

    steel = Material(name="steel", E=200e9, nu=0.3)

    tri1 = TriangleElement(material=steel, thickness=0.01, node_a=n0, node_b=n1, node_c=n2)
    tri2 = TriangleElement(material=steel, thickness=0.01, node_a=n0, node_b=n2, node_c=n3)

    elements = [tri1, tri2]

    K = create_global_matrix(nodes, elements,node_index)
    F = build_force_vector(nodes,node_index)
    K_r, F_r, remove = reduce_system(K, F, nodes,node_index)
    u_reduced = solve_system(K_r, F_r)
    full_u = expand_displacements(u_reduced, remove, len(nodes)*2)
    F_full = K @ full_u

    assert K.shape == (8, 8)
    assert np.allclose(K.toarray(), K.toarray().T)

    total_fx = F_full[0] + F_full[2] + F_full[4] + F_full[6]
    total_fy = F_full[1] + F_full[3] + F_full[5] + F_full[7]
    assert np.isclose(total_fx, 0.0, atol=1e-6)
    assert np.isclose(total_fy, 0.0, atol=1e-6)
