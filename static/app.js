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

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height); //clears rectangle size of entire canvas as things are automatically drawn on top of one another

    let maxStress = 0;
    if (showStress && lastResult) { //&& means and
        maxStress = Math.max(...lastResult.von_mises); //... spreads out array values so max function can operate on them
    }

    elements.forEach((el, i) => { //for each another looping method, el=element i=index
        const [idA, idB, idC] = el.node_ids;
        const a = nodes.find(n => n.id === idA); //returns the first item where callback returns true
        const b = nodes.find(n => n.id === idB);
        const c = nodes.find(n => n.id === idC);
        if (!a || !b || !c) return;

        ctx.beginPath(); //draws on the canvas like a pen beginning a path and drawing between lines
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.lineTo(c.x, c.y);
        ctx.closePath();

        if (showStress && lastResult) {
            ctx.fillStyle = stressColor(lastResult.von_mises[i], maxStress); //sets the next fill colour as it is a property not a parameter
            ctx.fill(); //fills current shape
        }
        ctx.strokeStyle = "black"; //sets the next fill colour for the outline
        ctx.stroke(); //fills outline with colour
    });

    nodes.forEach(node => {
        const isSelected = selectedNodeIds.includes(node.id);
        const radius = isSelected ? NODE_RADIUS + 3 : NODE_RADIUS;

        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2); //draws a circle centered at the nodes position with 
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

canvas.addEventListener("click", (e) => { //monitors for click events on the canvas and calls the function when it happens
    const x = e.offsetX, y = e.offsetY;

    if (mode === "node") {
        nodes.push({
            id: nextNodeId++,
            x: x, y: y,
            force_x: 0, force_y: 0,
            is_fixed_x: false, is_fixed_y: false
        });
        draw();
    } else if (mode === "triangle") {
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

    const fx = prompt("Force X:", node.force_x);
    if (fx === null) return;
    const fy = prompt("Force Y:", node.force_y);
    const fixX = confirm("Fix X displacement?");
    const fixY = confirm("Fix Y displacement?");

    node.force_x = parseFloat(fx) || 0;
    node.force_y = parseFloat(fy) || 0;
    node.is_fixed_x = fixX;
    node.is_fixed_y = fixY;
    draw();
});

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
    lastResult = await response.json();
    draw();
};

document.getElementById("toggle-stress-btn").onclick = () => {
    showStress = !showStress;
    draw();
};

draw();