import pyvista as pv
import numpy as np
from fea.material import Material
from .node import Node
from .element import TriangleElement
from .solver import (
    build_node_index
    )


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

def build_stress_array(elements, full_u, node_index):
    von_mises_stress_list = []
    for element in elements:
        von_mises_stress = element.get_von_mises_stress(full_u, node_index)
        von_mises_stress_list.append(von_mises_stress)
    return von_mises_stress_list

def render_mesh(nodes, elements, full_u=None, scale=1):
    stress_array = None
    if full_u is None:
        points = build_points_array(nodes)
    else:
        points = build_deformed_points_array(nodes, full_u, scale)
        node_index = build_node_index(nodes)
        stress_array = np.array(build_stress_array(elements, full_u, node_index))
    node_to_index = build_node_index_map(nodes)
    cells = build_cells_array(elements, node_to_index)

    points_array = np.array(points)
    cells_array = np.array(cells)

    mesh = pv.PolyData(points_array, faces=cells_array)
    if stress_array is not None:
        mesh.cell_data["von_mises_stress"] = stress_array
    return mesh

def show_mesh(mesh, show_edges=False, edge_color="black", line_width=3):
    if "von_mises_stress" in mesh.cell_data:
        scalars_to_use = "von_mises_stress"
    else:
        scalars_to_use = None
    plotter = pv.Plotter()
    plotter.add_mesh(mesh, show_edges=show_edges, edge_color=edge_color, line_width=line_width, scalars = scalars_to_use)
    plotter.add_text("W: wireframe   S: surface", font_size=10)
    plotter.view_xy()
    plotter.show()

def make_edge_fixer(edge, nx, ny):
    def is_fixed_fn(col,row):
        if edge == "left":
            return col == 0
        elif edge == "right":
            return col == nx
        elif edge == "top":
            return row == ny
        elif edge == "bottom":
            return row == 0
        return False
    return is_fixed_fn

def make_edge_loader(force_x,force_y,edge,nx,ny):
    edge_check = make_edge_fixer(edge, nx, ny)
    def is_forced_fn(col,row):
        if edge_check(col,row):
            return (force_x, force_y)
        else:
            return (0,0)
    return is_forced_fn 


def generate_rectangle_mesh(length,height,nx,ny,is_fixed_fn, force_fn):
          
    nodes = []
    node_grid = {} 
    identifier = 0
    for col in range(nx + 1):
        for row in range(ny + 1):
            x = length * col / nx
            y = height * row / ny
            is_fixed = is_fixed_fn(col,row)
            force_x,force_y = force_fn(col,row)
            n = Node(identifier=identifier, posx=x, posy=y,
                      is_fixed_x=is_fixed, is_fixed_y=is_fixed,
                      force_y=force_y,force_x=force_x)
            node_grid[(col, row)] = n
            nodes.append(n)
            identifier += 1

    steel = Material(name="steel", E=200e9, nu=0.3)

    elements = []
    for col in range(nx):
        for row in range(ny):
            a = node_grid[(col, row)]
            b = node_grid[(col+1, row)]
            c = node_grid[(col+1, row+1)]
            d = node_grid[(col, row+1)]
            if (col+row) % 2 == 0:
                elements.append(TriangleElement(material=steel, thickness=0.01, node_a=a, node_b=b, node_c=c))
                elements.append(TriangleElement(material=steel, thickness=0.01, node_a=a, node_b=c, node_c=d))
            else:
                elements.append(TriangleElement(material=steel, thickness=0.01, node_a=a, node_b=b, node_c=d))
                elements.append(TriangleElement(material=steel, thickness=0.01, node_a=b, node_b=c, node_c=d))
        
    return nodes, elements


if __name__ == "__main__":
    pass
 
    

