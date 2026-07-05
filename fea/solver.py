import numpy as np

def get_dofs(nodes_list):
    dofs = []
    for node in nodes_list:
        dofs.append(node.identifier*2)
        dofs.append(node.identifier*2+1)
    return dofs

def create_global_matrix(nodes, elements):
    n = len(nodes)*2
    K = np.zeros((n, n))
    for element in elements:
        local_matrix = element.create_stiffness_matrix()
        node_list = element.get_nodes()
        dofs = get_dofs(node_list)
        K[np.ix_(dofs, dofs)] += local_matrix
    return K

def build_force_vector(nodes):
    F = np.zeros((len(nodes)*2))
    for node in nodes:
        F[node.identifier*2] = node.force_x
        F[node.identifier*2+1] = node.force_y
    return F

def apply_boundary_conditions(K, F, nodes):
    remove = []
    for node in nodes:
        if node.is_fixed_x == True:
            remove.append(node.identifier*2)
        if node.is_fixed_y == True:
            remove.append(node.identifier*2+1)
    K = np.delete(K,remove,axis=1)
    K = np.delete(K,remove,axis=0)
    F = np.delete(F,remove,axis=0)       
    return K, F, remove

def solve_system(K_reduced, F_reduced):
    return(np.linalg.solve(K_reduced,F_reduced))

def expand_displacements(u_reduced, remove, total_dofs):
    full_u = np.zeros(total_dofs)
    counter = 0
    for position in range(total_dofs):
        if position not in remove:
            full_u[position] = u_reduced[counter]
            counter += 1
    return full_u



