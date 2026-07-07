from dataclasses import dataclass

@dataclass
class Material:
    name: str
    E: float
    nu: float