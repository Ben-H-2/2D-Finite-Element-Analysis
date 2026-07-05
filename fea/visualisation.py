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

def render_mesh(nodes,elements):
    mesh = pv.PolyData(np.array(build_points_array(nodes)), faces = np.array(build_cells_array(elements,build_node_index_map(nodes))))
    return mesh

if __name__ == "__main__":
    from .node import Node
    from .element import TriangleElement

    n0 = Node(identifier=0, posx=0.0, posy=0.0, is_fixed_x=True, is_fixed_y=True)
    n1 = Node(identifier=1, posx=3.0, posy=0.0, is_fixed_x=True, is_fixed_y=True)
    n2 = Node(identifier=2, posx=1.0, posy=4.0, force_x=1000, force_y=-500)

    nodes = [n0, n1, n2]

    tri = TriangleElement(E=200e9, nu=0.3, thickness=0.01, node_a=n0, node_b=n1, node_c=n2)
    elements = [tri]

    mesh = render_mesh(nodes, elements)
    mesh.plot()
    print(mesh)

