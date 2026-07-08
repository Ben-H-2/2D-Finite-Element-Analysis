from fea.element import Element,TriangleElement
from fea.model import AnalysisModel

def get_edge_key(node_a, node_b):
    return frozenset([node_a, node_b])

def get_or_create_midpoint(model, node_a, node_b, midpoint_cache):
    key = get_edge_key(node_a, node_b)
    if key in midpoint_cache:
        return midpoint_cache[key]
    mx = (node_a.posx + node_b.posx) / 2
    my = (node_a.posy + node_b.posy) / 2
    mid_node = model.add_node(mx, my)
    midpoint_cache[key] = mid_node
    return mid_node

def refine_mesh(model, times=1):
    for _ in range(times):
        old_elements = model.elements[:]
        midpoint_cache = {}
        for triangle in old_elements:
            node_a = triangle.node_a
            node_b = triangle.node_b
            node_c = triangle.node_c

            midpoint_ab = get_or_create_midpoint(model, node_a, node_b, midpoint_cache)
            midpoint_ca = get_or_create_midpoint(model, node_c, node_a, midpoint_cache)
            midpoint_bc = get_or_create_midpoint(model, node_b, node_c, midpoint_cache)

            new_triangles = [
                TriangleElement(material=triangle.material, thickness=triangle.thickness,
                                 node_a=node_a, node_b=midpoint_ab, node_c=midpoint_ca),
                TriangleElement(material=triangle.material, thickness=triangle.thickness,
                                 node_a=midpoint_ab, node_b=node_b, node_c=midpoint_bc),
                TriangleElement(material=triangle.material, thickness=triangle.thickness,
                                 node_a=midpoint_ca, node_b=midpoint_bc, node_c=node_c),
                TriangleElement(material=triangle.material, thickness=triangle.thickness,
                                 node_a=midpoint_ab, node_b=midpoint_bc, node_c=midpoint_ca),
            ]
            for t in new_triangles:
                model.add_element(t)

            model.remove_element(triangle)

