const canvas = document.getElementById("canvas"); //document represents the whole webpage
const ctx = canvas.getContext("2d")
const NODE_RADIUS = 6; //default to 6 but here so can be modified later
const NODE_SELECTION_RADIUS = 16; // larger click area for easier selection

let nodes = []; //let means it is like a python variable and can be changed unlike const
let elements = []; //; represents new line, indentation is visual in js
let nextNodeId = 0;
let mode = "node";
let selectedNodeIds = [];
let showStress = false;
let lastResult = null;
let editingNode = null; //tracks which node the panel is currently editing

function updateModeButtons() {
    const nodeButton = document.getElementById("mode-node");
    const triangleButton = document.getElementById("mode-triangle");

    if (nodeButton) {
        nodeButton.classList.toggle("active", mode === "node");
    }
    if (triangleButton) {
        triangleButton.classList.toggle("active", mode === "triangle");
    }
}

function setMode(newMode) { //can recognise the button mode 
    mode = newMode;
    updateModeButtons();
}

const nodeButton = document.getElementById("mode-node");
const triangleButton = document.getElementById("mode-triangle");
if (nodeButton) {
    nodeButton.onclick = () => setMode("node");
}
if (triangleButton) {
    triangleButton.onclick = () => setMode("triangle");
}
updateModeButtons();

function findNodeNear(x, y, radius = NODE_SELECTION_RADIUS) { // same as python function but uses "function" and {}
    for (const node of nodes) { //js equivalent of for node in nodes
        const dx = node.x - x;
        const dy = node.y - y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist <= radius) {
            return node;
        }
    }
    return null;   
}

function stressColor(value, maxValue) {
    const t = maxValue > 0 ? value / maxValue : 0;
    const r = Math.floor(255 * t);
    const b = Math.floor(255 * (1 - t));
    return `rgb(${r}, 0, ${b})`;
}

function drawResultMesh() { // draws the mesh the BACKEND solved (after refine_mesh ran), not our own nodes/elements
    const resultNodes = lastResult.nodes; //[{id, posx, posy}, ...]
    const resultElements = lastResult.elements; //[{node_ids: [a,b,c]}, ...]
    const vonMises = lastResult.von_mises;

    const maxStress = Math.max(...vonMises);

    const nodeById = new Map(resultNodes.map(n => [n.id, n])); //same job as findNodeNear but by id lookup instead of distance, O(1) not O(n)

    resultElements.forEach((el, i) => {
        const [idA, idB, idC] = el.node_ids;
        const a = nodeById.get(idA);
        const b = nodeById.get(idB);
        const c = nodeById.get(idC);
        if (!a || !b || !c) return;

        ctx.beginPath();
        ctx.moveTo(a.posx, a.posy);
        ctx.lineTo(b.posx, b.posy);
        ctx.lineTo(c.posx, c.posy);
        ctx.closePath();

        ctx.fillStyle = stressColor(vonMises[i], maxStress);
        ctx.fill();
        ctx.strokeStyle = "black";
        ctx.stroke();
    });

    resultNodes.forEach(n => { //small dots just so refined nodes are visible, not interactive
        ctx.beginPath();
        ctx.arc(n.posx, n.posy, 3, 0, Math.PI * 2);
        ctx.fillStyle = "black";
        ctx.fill();
    });
}

function drawEditableMesh() { // draws OUR clicked nodes/elements -- this is basically your old draw() body, unchanged
    elements.forEach((el, i) => {
        const [idA, idB, idC] = el.node_ids;
        const a = nodes.find(n => n.id === idA);
        const b = nodes.find(n => n.id === idB);
        const c = nodes.find(n => n.id === idC);
        if (!a || !b || !c) return;

        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.lineTo(c.x, c.y);
        ctx.closePath();
        ctx.strokeStyle = "black";
        ctx.stroke();
    });

    nodes.forEach(node => {
        const isSelected = selectedNodeIds.includes(node.id);
        const radius = isSelected ? NODE_RADIUS + 3 : NODE_RADIUS;

        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        if (node.is_fixed_x || node.is_fixed_y) {
            ctx.fillStyle = "green";
        } else if (node.force_x !== 0 || node.force_y !== 0) {
            ctx.fillStyle = "orange";
        } else {
            ctx.fillStyle = "blue";
        }
        ctx.fill();

        if (isSelected) {
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius + 3, 0, Math.PI * 2);
            ctx.strokeStyle = "white";
            ctx.lineWidth = 2;
            ctx.stroke();
        }
    });
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height); //clears rectangle size of entire canvas as things are automatically drawn on top of one another

    if (showStress && lastResult) {
        drawResultMesh(); //post-solve mesh coloured
    } else {
        drawEditableMesh(); //what is clicked so far
    }
}

canvas.addEventListener("click", (e) => { //monitors for click events on the canvas and calls the function when it happens
    const x = e.offsetX, y = e.offsetY;

    if (mode === "node") {
        showStress = false;  //pushes the user into edit mode of a local mesh
        nodes.push({
            id: nextNodeId++,
            x: x, y: y,
            force_x: 0, force_y: 0,
            is_fixed_x: false, is_fixed_y: false
        });
        draw();
    } else if (mode === "triangle") {
        showStress = false; // same as previous
        const node = findNodeNear(x, y);
        if (!node) return;

        if (!selectedNodeIds.includes(node.id)) {
            selectedNodeIds.push(node.id);
        }

        if (selectedNodeIds.length === 3) {
            elements.push({ type: "triangle", node_ids: [...selectedNodeIds] });
            selectedNodeIds = [];
        }
        draw();
    }
});


canvas.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    const x = e.offsetX, y = e.offsetY;
    const node = findNodeNear(x, y);
    if (!node) return;
    showStress = false;

    editingNode = node;
    document.getElementById("panel-fx").value = node.force_x;
    document.getElementById("panel-fy").value = node.force_y;
    document.getElementById("panel-fixx").checked = node.is_fixed_x;
    document.getElementById("panel-fixy").checked = node.is_fixed_y;

    const panel = document.getElementById("node-panel");
    panel.style.left = e.pageX + "px";
    panel.style.top = e.pageY + "px";
    panel.style.display = "block";
});

document.getElementById("panel-apply").onclick = () => {
    if (!editingNode) return;
    editingNode.force_x = parseFloat(document.getElementById("panel-fx").value) || 0;
    editingNode.force_y = parseFloat(document.getElementById("panel-fy").value) || 0;
    editingNode.is_fixed_x = document.getElementById("panel-fixx").checked;
    editingNode.is_fixed_y = document.getElementById("panel-fixy").checked;
    document.getElementById("node-panel").style.display = "none";
    editingNode = null;
    draw();
};

document.getElementById("panel-cancel").onclick = () => {
    document.getElementById("node-panel").style.display = "none";
    editingNode = null;
};

document.getElementById("calculate-btn").onclick = async () => {
    const refineTimes = parseInt(document.getElementById("refine-input").value);
    const payload = {
        nodes: nodes.map(n => ({
            id: n.id, posx: n.x, posy: n.y,
            force_x: n.force_x, force_y: n.force_y,
            is_fixed_x: n.is_fixed_x, is_fixed_y: n.is_fixed_y
        })),
        elements: elements.map(el => ({
            type: el.type, node_ids: el.node_ids
        })),
        refine_times: refineTimes
    };

    const response = await fetch("/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        alert("Calculation failed: " + (await response.text()));
        return;
    }
    lastResult = await response.json();
    showStress = true; //flip to results view automatically once solved
    draw();
};

document.getElementById("toggle-stress-btn").onclick = () => {
    showStress = !showStress;
    draw();
};

draw();