from fea.element import Element
from fea.node import Node

n0 = Node(identifier=0, posx=0.0, is_fixed=True)
n1 = Node(identifier=1, posx=1.0, is_fixed=False)
e0 = Element(stiffness=5, leftnode=n0, rightnode=n1)
print(e0.create_stiffness_matrix())