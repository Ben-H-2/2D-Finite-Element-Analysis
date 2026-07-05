import pyvista as pv
import numpy as np


def build_node_index_map(nodes):
    node_to_index = {}
    for i, node in enumerate(nodes):
        node_to_index[node] = i
    return node_to_index

def get_points_for_element(element):
    nodes = element.get_nodes()
    positions = []
    for node in nodes:
        coords = (node.posx,node.posy,0)
        positions.append(coords)
    return positions

def get_cell_for_element(element,node_to_index):
    nodes = element.get_nodes()
    cell = [len(nodes)]
    for node in nodes:
        cell.append(node_to_index[node])
    return cell

def build_points_array(nodes):
    points = []
    for node in nodes:
        coords = (node.posx, node.posy, 0)
        points.append(coords)
    return points

def build_cells_array(elements, node_to_index):
    cells_array = []
    for element in elements:
        cells_array.extend(get_cell_for_element(element,node_to_index))
    return cells_array

def get_deformed_position(node, full_u,scale=1):
    x_disp = scale*(full_u[node.identifier*2])
    y_disp = scale*(full_u[node.identifier*2+1])
    return (node.posx+x_disp, node.posy+y_disp, 0)

def build_deformed_points_array(nodes,full_u,scale=1):
    points = []
    for node in nodes:
        coords = get_deformed_position(node,full_u,scale)
        points.append(coords)
    return points

def build_stress_array(elements, full_u):
    von_mises_stress_list = []
    for element in elements:
        von_mises_stress = element.get_von_mises_stress(full_u)
        von_mises_stress_list.append(von_mises_stress)
    return von_mises_stress_list

def render_mesh(nodes,elements,full_u=None,scale=1):
    if full_u is None:
        points = build_points_array(nodes)
    else:
        points = build_deformed_points_array(nodes,full_u,scale)
    node_to_index = build_node_index_map(nodes)
    cells = build_cells_array(elements,node_to_index)

    points_array = np.array(points)
    cells_array = np.array(cells)

    mesh = pv.PolyData(points_array, faces = cells_array)
    return mesh

def show_mesh(mesh, show_edges=True, edge_color="black", line_width=3):
    plotter = pv.Plotter()
    plotter.add_mesh(mesh, show_edges=show_edges, edge_color=edge_color, line_width=line_width)
    plotter.add_text("W: wireframe   S: surface", font_size=10)
    plotter.show()



if __name__ == "__main__":
    from .node import Node
    from .element import Element
    from .solver import (
        create_global_matrix,
        build_force_vector,
        apply_boundary_conditions,
        solve_system,
        expand_displacements,
    )

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
    full_u = expand_displacements(u_reduced, remove, len(nodes) * 2)
    print(full_u)

    mesh = render_mesh(nodes, elements, full_u,scale=10000000)
    print(mesh)
    show_mesh(mesh)

