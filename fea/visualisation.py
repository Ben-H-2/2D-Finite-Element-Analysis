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
