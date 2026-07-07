from fea.node import Node
from fea.element import Element
from fea.model import AnalysisModel

def test_model_truss():
    model = AnalysisModel()

    n0 = model.add_node(posx=0.0, posy=0.0)
    n1 = model.add_node(posx=2.0, posy=0.0)
    n2 = model.add_node(posx=1.0, posy=1.5)

    steel = model.materials["steel"]

    model.add_element(Element(material=steel, A=0.001, leftnode=n0, rightnode=n1))
    model.add_element(Element(material=steel, A=0.001, leftnode=n0, rightnode=n2))
    model.add_element(Element(material=steel, A=0.001, leftnode=n1, rightnode=n2))

    model.add_support(n0, fix_x=True, fix_y=True)
    model.add_support(n1, fix_x=True, fix_y=True)
    model.add_load(n2, force_y=-10)

    model.solve()

    print("Displacements:", model.get_displacements())
    print("Reactions:", model.get_reactions())
    print("Stresses:", model.get_element_stresses())
    print("Von Mises:", model.get_von_mises_stresses())
