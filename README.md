# FEA Sandbox - Interactive Finite Element Analysis Tool

## Overview

A browser-based tool for building 2D triangular meshes and applying loads and constraints, all in real time with stress colouring, deformation and structural warning feedback. No external software required, running locally or in Github codespaces.

## Features
<details>

<summary> Mesh Editing </summary>

Left click in "Add node" mode to freely place nodes or manually enter coordinates. Group nodes into triangular elements directly or create rectangular shapes through 2 triangles by selecting corner nodes.

</details>
<details>

<summary>Boundary Conditions & Loads</summary>
Right click a node or element edge to either fix it in the X/Y direction, apply a point force, or evenly distribute force along an edge. Edited nodes and elements are colour coded by property (green = fixed, orange = force).

</details>
<details>

<summary>Mesh Refinement</summary>
Subdivide the mesh before solving with a configurable level of refinement up to 4^8 triangles per element. Warning messages are shown above a certain threshold as refinement grows element count exponentially so can lead to long processing time.

</details>
<details>

<summary>Solving</summary>
When "calculate" is pressed, the mesh is sent to a Python backend, which assembles a global stiffness matrix as a sparse COO matrix, converts it to CSR for boundary condition reduction and solves it with SciPy's sparse solver (spsolve).

</details>
<details>

<summary>Stress Visualization</summary>
Stress is conveyed through a colour-mapped overlay with a live legend, with a toggle for linear as well as logarithmic scaling so stress distribution is visible even when outliers may wash out colour discepancies in linear mode.

</details>
<details>

<summary>Deformed Shape Preview</summary>
Toggle between the orginal and deformed mesh, with a configurable slider to exaggerate the deformation where it may not be visible for smaller forces.

</details>
<details>

<summary>Structural warnings</summary>
Before solving a check is run for unconstrained structures or connections around single nodes (articulation points) in order to prevent unintended results (these warnings are permanently dismissable).

</details>
<details>

<summary>Crash Recovery / Session Persistence</summary>
Upon solving, reloading or exiting the page the current mesh is snapshotted to local storage, so a reload or crash prompts a message to recover the mesh as a precaution.

</details>


## Screenshots / Demo

## Getting Started
### Prerequisites
```
Python 3.12+
pip
```
### Installation
```
git clone (https://github.com/Ben-H-2/2D-FEA-Sandbox).git
cd 2D-FEA-Sandbox
pip install -r requirements.txt
```
### Running 
```
python main.py
```
This will print out the current status of the http://localhost:8000 in the terminal as well as a link to the interactive browser window.

## Usage
### Placing Nodes
### Creating Elements (Triangle / Rectangle)
### Setting Fixed Constraints
### Applying Forces
### Editing Edge Rules
### Refining the Mesh
### Running a Calculation
### Interpreting the Stress Legend
### Toggling Views (Stress / Outlines / Deformation / Scale Mode)
### Hovering for Point Stress Values

## How It Works
### Mesh Data Model (Nodes, Elements, Edge Rules)
### Refinement Algorithm
### Structural Warnings (Articulation Points, Unconstrained Structures)
### Solve Request / Response Format
### Stress Colour Mapping (Linear vs Logarithmic)
### Solve Time Estimation

## Known Limitations
- No material property support yet (assumes steel)
- No persistent save/load to file 

## Roadmap
- [ ] Material properties
- [ ] Save/load mesh to file
- [ ] Pyvista implementation

## Project Structure
### Module Dependency Graph
```mermaid
graph TD
subgraph EntryGroup["Entry Point"]
Main["main.py"]
end
subgraph BackendGroup["Backend API"]
    App["api/app.py<br/>/calculate endpoint"]
end

subgraph CoreGroup["fea/ — FEA Core"]
    Model["model.py<br/>AnalysisModel"]
    Mesh["mesh.py<br/>refine_mesh, apply_edge_rules"]
    Element["element.py<br/>Element, TriangleElement"]
    Node["node.py<br/>Node"]
    Material["material.py<br/>Material"]
    Solver["solver.py<br/>matrix assembly + solve"]
    Vis["visualisation.py<br/>show_mesh, render_model"]
end

subgraph FrontendGroup["static/ — Frontend"]
    HTML["index.html"]
    JS["app.js"]
end

subgraph TestsGroup["Tests"]
    Tests["test_model.py<br/>test_solver.py"]
end

Main --> App

App --> Model
App --> Mesh
App --> Element

Mesh --> Model
Mesh -->|"TriangleElement<br/>(Element imported, unused)"| Element

Model --> Node
Model -->|"ElementBase only<br/>(Element, TriangleElement imported, unused)"| Element
Model --> Material
Model --> Solver
Model -->|"show_mesh, render_model<br/>(render_mesh imported, unused)"| Vis

Element --> Node
Element --> Material
Element --> Solver

Vis --> Node
Vis --> Element
Vis --> Material
Vis --> Solver

App -.->|"GET / — serves"| HTML
HTML -.->|"browser loads"| JS

JS ==>|"POST /calculate"| App
App ==>|"JSON: nodes, displacements, von_mises"| JS

Tests -.-> Model
Tests -.-> Solver
Tests -.-> Node
Tests -.-> Element
Tests -.-> Material
```
* Solid → = real Python import, actively used
* Dashed -.→ = file served / loaded by the browser, not a Python import
* Thick ⇒ = live HTTP request/response between browser and server
* Dotted Tests -.→ = imported only by test files, not part of the production runtime path
### Calculation Sequence 
```mermaid
sequenceDiagram
participant JS as app.js (Browser)
participant API as api/app.py
participant Model as AnalysisModel
participant MeshMod as mesh.py
participant Solver as solver.py
participant Elem as TriangleElement
JS->>JS: checkStructuralWarnings() — client-side check
JS->>JS: saveMeshSnapshot() — localStorage
JS->>API: POST /calculate {nodes, elements, edge_rules, refine_times}

API->>Model: AnalysisModel() — loads default materials
API->>Model: add_node() for each node
API->>Elem: construct Element / TriangleElement per element
API->>Model: add_element() for each

API->>MeshMod: refine_mesh(model, times)
loop each refinement pass
    MeshMod->>Model: add_node() — new midpoint nodes
    MeshMod->>Elem: build 4 new TriangleElements
    MeshMod->>Model: add_element() x4, remove_element() original
end

API->>MeshMod: apply_edge_rules(model, edge_rules)
MeshMod->>Model: match nodes along edge, set fix/force values

API->>Model: solve()
Model->>Model: build_mesh() — validate nodes/elements exist
Model->>Solver: build_node_index(nodes)
Model->>Solver: create_global_matrix(nodes, elements, node_index)
Solver->>Elem: create_stiffness_matrix() per element
Model->>Solver: build_force_vector(nodes, node_index)
Model->>Solver: reduce_system() — apply fixed-DOF boundary conditions
Model->>Solver: solve_system() — scipy spsolve
Model->>Solver: expand_displacements() — reinsert zeros at fixed DOFs

API->>Model: get_von_mises_stresses()
Model->>Elem: get_von_mises_stress(u, node_index) per element
Elem->>Elem: get_stress() → get_strain() using B/D matrices

API-->>JS: JSON {nodes, elements, displacements, von_mises}
JS->>JS: draw() → drawResultMesh(), updateStressLegend()
JS->>JS: recordSolveTime() — localStorage
```
## Configuration / Constants Reference

## License