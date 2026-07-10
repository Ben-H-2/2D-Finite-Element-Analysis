from fea.element import Element,TriangleElement
from fea.model import AnalysisModel
from math import sqrt

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

def apply_edge_rules(model, edge_rules, id_to_node, epsilon = 1e-6):
    for rule in edge_rules:
        node_a = id_to_node[rule.node_a_id]
        node_b = id_to_node[rule.node_b_id]

        dx = node_b.posx - node_a.posx
        dy = node_b.posy - node_a.posy
        length_sq = dx*dx + dy*dy

        matched_nodes = []
        for node in model.nodes:
            t = ((node.posx - node_a.posx) * dx + (node.posy - node_a.posy) * dy) / length_sq
            closest_x = node_a.posx + t * dx
            closest_y = node_a.posy + t * dy
            dist = sqrt((node.posx - closest_x)**2 + (node.posy - closest_y)**2)
            if dist <= epsilon and -epsilon <= t <= 1+epsilon:
                matched_nodes.append(node)
        if rule.type == "fix":
            for node in matched_nodes:
                if rule.fix_x:
                    node.is_fixed_x = True
                if rule.fix_y:
                    node.is_fixed_y = True
        elif rule.type == "force":
            number_of_nodes = len(matched_nodes)
            load_x = rule.force_x / number_of_nodes
            load_y = rule.force_y / number_of_nodes
            for node in matched_nodes:
                node.force_x += load_x
                node.force_y += load_y



                



