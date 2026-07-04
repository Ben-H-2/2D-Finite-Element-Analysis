import numpy as np

def create_global_matrix(nodes, elements):
    n = len(nodes)
    K = np.zeros((n, n))
    for element in elements:
        start = min(element.leftnode.identifier,element.rightnode.identifier)
        end = max(element.leftnode.identifier,element.rightnode.identifier)+1
        K[start:end, start:end] += element.create_stiffness_matrix()
    return K

def build_force_vector(nodes):
    F = np.zeros((len(nodes)))
    for node in nodes:
        F[node.identifier] = node.force
    return F

def apply_boundary_conditions(K, F, nodes):
    remove = []
    for node in nodes:
        if node.is_fixed == True:
            remove.append(node.identifier)
    K = np.delete(K,remove,axis=1)
    K = np.delete(K,remove,axis=0)
    F = np.delete(F,remove,axis=0)       
    return K, F

def solve_system(K_reduced, F_reduced):
    return(np.linalg.solve(K_reduced,F_reduced))


