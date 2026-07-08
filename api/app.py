from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from fea.model import AnalysisModel
from fea.element import Element, TriangleElement

app = FastAPI()

class NodeIn(BaseModel):
    id: int
    posx: float
    posy: float
    force_x: float = 0.0
    force_y: float = 0.0
    is_fixed_x: bool = False
    is_fixed_y: bool = True

class ElementIn(BaseModel):
    type: str
    node_ids: list[int]
    material: str = "steel"
    A: float = 0.001
    thickness: float = 0.01

class CalculateRequest(BaseModel):
    nodes: list[NodeIn]
    elements: list[ElementIn]

@app.post("/calculate")
def calculate(req: CalculateRequest):
    model = AnalysisModel()
    id_to_node = {}
    for n in req.nodes:
        node = model.add_node(n.posx, n.posy)
        node.force_x, node.force_y = n.force_x, n.force_y
        node.is_fixed_x, node.is_fixed_y = n.is_fixed_x, n.is_fixed_y
        id_to_node[n.id] = node

    
    for e in req.elements:
        nodes = [id_to_node[i] for i in e.node_ids]
        material = model.materials[e.material]
        if e.type == "truss":
            elem = Element(material=material, A=e.A, leftnode=nodes[0], rightnode=nodes[1])
        else:
            elem = TriangleElement(material=material, thickness=e.thickness,
                                     node_a=nodes[0], node_b=nodes[1], node_c=nodes[2])
        model.add_element(elem)

    model.solve()

    return {
        "displacements": model.get_displacements().tolist(),
        "von_mises": [float(v) for v in model.get_von_mises_stresses()],
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")