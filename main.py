from fea.node import Node
from fea.element import Element
from fea.solver import create_global_matrix, build_force_vector, apply_boundary_conditions, solve_system, expand_displacements
import fea.visualisation

def main():
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

    for element in elements:
        stress = element.get_stress(full_u)
        print(stress)

if __name__ == "__main__":
    main()