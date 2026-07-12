const canvas = document.getElementById("canvas"); 
const ctx = canvas.getContext("2d")
const NODE_RADIUS = 3; 
const NODE_SELECTION_RADIUS = 16; 
const ELEMENT_SELECTION_RADIUS = 16;
const LOGICAL_WIDTH = 900;
const LOGICAL_HEIGHT = 600;
const REFINE_WARNING_THRESHOLD = 4; 
const warningOverlay = document.getElementById("warning-modal-overlay");
const dontShowAgainCheckbox = document.getElementById("warning-dont-show-again");

let nodes = []; 
let elements = []; 
let nextNodeId = 0;
let mode = "node";
let selectedNodeIds = [];
let showStress = false;
let showDeformed = false;
let showOutlines = false;
let lastResult = null;
let editingNode = null; 
let editingEdge = null;
let edgeRules = [];
let scale = 1;
let deformationScale = 50;

function updateModeButtons() {
    const nodeButton = document.getElementById("mode-node");
    const triangleButton = document.getElementById("mode-triangle");
    const rectangleButton = document.getElementById("mode-rectangle")

    if (nodeButton) {
        nodeButton.classList.toggle("active", mode === "node");
    }
    if (triangleButton) {
        triangleButton.classList.toggle("active", mode === "triangle");
    }
    if (rectangleButton) {
        rectangleButton.classList.toggle("active", mode == "rectangle")
    }
}

function setMode(newMode) { 
    mode = newMode;
    updateModeButtons();
}

function syncToggleButton(buttonId, isActive) {
    const btn = document.getElementById(buttonId);
    if (btn) {
        btn.classList.toggle("active", isActive);
    }
}

const nodeButton = document.getElementById("mode-node");
const triangleButton = document.getElementById("mode-triangle");
const rectangleButton = document.getElementById("mode-rectangle")
if (nodeButton) {
    nodeButton.onclick = () => setMode("node");
}
if (triangleButton) {
    triangleButton.onclick = () => setMode("triangle");
}
if (rectangleButton) {
    rectangleButton.onclick = () => setMode("rectangle")
}
updateModeButtons();

function resizeCanvas() {
    const availableWidth = window.innerWidth;
    const availableHeight = window.innerHeight;
    scale = Math.min(availableWidth / LOGICAL_WIDTH, availableHeight / LOGICAL_HEIGHT);
    canvas.width = availableWidth;
    canvas.height = availableHeight;
    ctx.setTransform(scale, 0, 0, scale, 0, 0);
    draw();
}

window.addEventListener("resize", resizeCanvas);
resizeCanvas();

function findNodeNear(x, y, radius = NODE_SELECTION_RADIUS) { 
    for (const node of nodes) { 
        const dx = node.x - x;
        const dy = node.y - y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist <= radius) {
            return node;
        }
    }
    return null;   
}

function findEdgeNear(x, y, radius = NODE_SELECTION_RADIUS) {
    let closestEdge = null;
    let closestDist = radius;

    for (const el of elements) {
        const ids = el.node_ids;
        const edgePairs = [
            [ids[0], ids[1]],
            [ids[1], ids[2]],
            [ids[2], ids[0]]
        ];

        for (const [idA, idB] of edgePairs) {
            const a = nodes.find(n => n.id === idA);
            const b = nodes.find(n => n.id === idB);
            if (!a || !b) continue;

            const dist = pointToSegmentDistance(x, y, a.x, a.y, b.x, b.y);
            if (dist <= closestDist) {
                closestDist = dist;
                const a = Math.min(idA, idB);
                const b = Math.max(idA, idB);

                closestEdge = {
                    node_a_id: a,
                    node_b_id: b
                };  
            }
        }
    }

    return closestEdge;
}

function pointToSegmentDistance(px, py, ax, ay, bx, by) {
    const dx = bx - ax;
    const dy = by - ay;
    const lengthSq = dx * dx + dy * dy;

    if (lengthSq === 0) {
        const ddx = px - ax, ddy = py - ay;
        return Math.sqrt(ddx * ddx + ddy * ddy);
    }

    let t = ((px - ax) * dx + (py - ay) * dy) / lengthSq;
    t = Math.max(0, Math.min(1, t));

    const closestX = ax + t * dx;
    const closestY = ay + t * dy;

    const ddx = px - closestX;
    const ddy = py - closestY;
    return Math.sqrt(ddx * ddx + ddy * ddy);
}

function getEffectiveNodeState(nodeId) {
    let isFixedX = false, isFixedY = false;
    let forceX = 0, forceY = 0;

    for (const rule of edgeRules) {
        if (rule.node_a_id !== nodeId && rule.node_b_id !== nodeId) continue;

        if (rule.type === "fix") {
            if (rule.fix_x) isFixedX = true;
            if (rule.fix_y) isFixedY = true;
        } else if (rule.type === "force") {
            forceX += rule.force_x;
            forceY += rule.force_y;
        }
    }

    return { isFixedX, isFixedY, forceX, forceY };
}

function getEdgeRuleForElementEdge(idA, idB) {
    const a = Math.min(idA, idB);
    const b = Math.max(idA, idB);
    return edgeRules.find(r => r.node_a_id === a && r.node_b_id === b);
}

function stressColor(value, maxValue) {
    const t = maxValue > 0 ? value / maxValue : 0;
    const r = Math.floor(255 * t);
    const b = Math.floor(255 * (1 - t));
    return `rgb(${r}, 0, ${b})`;
}

function drawResultMesh() { 
    const resultNodes = lastResult.nodes; 
    const resultElements = lastResult.elements; 
    const vonMises = lastResult.von_mises;
    const displacements = lastResult.displacements; 

    const maxStress = Math.max(...vonMises);

    const nodeById = new Map(resultNodes.map(n => [n.id, n])); 

    resultElements.forEach((el, i) => {
        const [idA, idB, idC] = el.node_ids;
        const a = nodeById.get(idA);
        const b = nodeById.get(idB);
        const c = nodeById.get(idC);
        if (!a || !b || !c) return;

        const posA = showDeformed
            ? {x: a.posx + displacements[idA * 2] * deformationScale, y: a.posy + displacements[idA * 2 + 1] * deformationScale}
            : {x: a.posx, y: a.posy};
        const posB = showDeformed
            ? {x: b.posx + displacements[idB * 2] * deformationScale, y: b.posy + displacements[idB * 2 + 1] * deformationScale}
            : {x: b.posx, y: b.posy};
        const posC = showDeformed
            ? {x: c.posx + displacements[idC * 2] * deformationScale, y: c.posy + displacements[idC * 2 + 1] * deformationScale}
            : {x: c.posx, y: c.posy};

        ctx.beginPath();
        ctx.moveTo(posA.x, posA.y);
        ctx.lineTo(posB.x, posB.y);
        ctx.lineTo(posC.x, posC.y);
        ctx.closePath();

        ctx.fillStyle = stressColor(vonMises[i], maxStress);
    ctx.fill();

    ctx.lineJoin = "round";
    if (showOutlines) {
        ctx.strokeStyle = "black";
        ctx.lineWidth = 1;
        ctx.stroke();
    } else {
        ctx.strokeStyle = ctx.fillStyle;
        ctx.lineWidth = 1.5;
        ctx.stroke();
    }
    });
    resultNodes.forEach((n) => {
        const x = showDeformed ? n.posx + displacements[n.id * 2] * deformationScale : n.posx;
        const y = showDeformed ? n.posy + displacements[n.id * 2 + 1] * deformationScale : n.posy;
        if (showOutlines) {
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fillStyle = "black";
            ctx.fill();
        }
    });
}

function drawEditableMesh() { 
    elements.forEach((el, i) => {
        const [idA, idB, idC] = el.node_ids;
        const a = nodes.find(n => n.id === idA);
        const b = nodes.find(n => n.id === idB);
        const c = nodes.find(n => n.id === idC);
        if (!a || !b || !c) return;

        const edges = [[a, b, idA, idB], [b, c, idB, idC], [c, a, idC, idA]];

        for (const [p1, p2, ea, eb] of edges) {
            const rule = getEdgeRuleForElementEdge(ea, eb);

            let strokeStyle = "black";
            if (rule) {
                if (rule.type === "fix" && (rule.fix_x || rule.fix_y)) {
                    strokeStyle = "green";
                } else if (rule.type === "force" && (rule.force_x !== 0 || rule.force_y !== 0)) {
                    strokeStyle = "orange";
                }
            }

            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = strokeStyle;
            ctx.lineWidth = strokeStyle === "black" ? 1 : 2.5;
            ctx.stroke();
        }
    });

    nodes.forEach(node => {
        const isSelected = selectedNodeIds.includes(node.id);
        const radius = isSelected ? NODE_RADIUS + 3 : NODE_RADIUS;

        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        const effective = getEffectiveNodeState(node.id);
        const isFixed = node.is_fixed_x || node.is_fixed_y || effective.isFixedX || effective.isFixedY;
        const hasForce = node.force_x !== 0 || node.force_y !== 0 || effective.forceX !== 0 || effective.forceY !== 0;

        if (isFixed) {
            ctx.fillStyle = "green";
        } else if (hasForce) {
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
    ctx.clearRect(0, 0, canvas.width, canvas.height); 

    if (showStress && lastResult) {
        drawResultMesh(); 
    } else {
        drawEditableMesh(); 
    }
}

canvas.addEventListener("click", (e) => { 
    const x = e.offsetX / scale, y = e.offsetY / scale;

    if (mode === "node") {
        showStress = false; 
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
    } else if (mode == "rectangle") {
        showStress = false;
        const Node = findNodeNear(x, y);
        if (!Node) return;

        if (!selectedNodeIds.includes(Node.id)) {
            selectedNodeIds.push(Node.id);
        }

        if (selectedNodeIds.length === 2) {
            let node_a = nodes.find(n => n.id === selectedNodeIds[0]);
            let node_b = nodes.find(n => n.id === selectedNodeIds[1]);
            let node_c = findOrCreateNode(node_a.x, node_b.y);
            let node_d = findOrCreateNode(node_b.x, node_a.y)
            elements.push({ type: "triangle", node_ids: [node_a.id,node_c.id,node_d.id]
            })
            elements.push({ type: "triangle", node_ids: [node_b.id,node_c.id,node_d.id]
            });
            selectedNodeIds = []
        }
    }
        draw();
});


canvas.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    const x = e.offsetX / scale, y = e.offsetY / scale;
    const node = findNodeNear(x, y);

    if (node) {
        showStress = false;

        editingNode = node;
        document.getElementById("edge-panel").style.display = "none"
        
        document.getElementById("node-fx").value = node.force_x;
        document.getElementById("node-fy").value = -node.force_y;
        document.getElementById("node-fixx").checked = node.is_fixed_x;
        document.getElementById("node-fixy").checked = node.is_fixed_y;

        const panel = document.getElementById("node-panel");
        panel.style.left = e.pageX + "px";
        panel.style.top = e.pageY + "px";
        panel.style.display = "block";
        return;
    }
    const edge = findEdgeNear(x, y);

    if (edge) {
        showStress = false;
        editingEdge = edge;
        document.getElementById("node-panel").style.display = "none"

        const existingRule = edgeRules.find(r =>
            r.node_a_id === edge.node_a_id &&
            r.node_b_id === edge.node_b_id
        );

        if (existingRule) {
            document.getElementById("edge-type").value = existingRule.type;
            updateEdgeFieldVisibility()

            if (existingRule.type === "fix") {
                document.getElementById("edge-fixx").checked = existingRule.fix_x;
                document.getElementById("edge-fixy").checked = existingRule.fix_y;
            } else {
                document.getElementById("edge-fx").value = existingRule.force_x;
                document.getElementById("edge-fy").value = -existingRule.force_y;
            }
        } else {
            document.getElementById("edge-type").value = "fix";
            updateEdgeFieldVisibility()
            document.getElementById("edge-fixx").checked = false;
            document.getElementById("edge-fixy").checked = false;
            document.getElementById("edge-fx").value = 0;
            document.getElementById("edge-fy").value = 0;
        }

        const panel = document.getElementById("edge-panel");
        panel.style.left = e.pageX + "px";
        panel.style.top = e.pageY + "px";
        panel.style.display = "block";
        return;
    }
});

function closeAllPanels() {
    document.getElementById("node-panel").style.display = "none";
    document.getElementById("edge-panel").style.display = "none";
}

function findOrCreateNode(x, y, tolerance = 0.01) {
    for (const node of nodes) {
        const dx = node.x - x;
        const dy = node.y - y;
        if (Math.sqrt(dx * dx + dy * dy) <= tolerance) {
            return node;
        }
    }
    const newNode = {
        id: nextNodeId++,
        x: x, y: y,
        force_x: 0, force_y: 0,
        is_fixed_x: false, is_fixed_y: false
    };
    nodes.push(newNode);
    return newNode;
}
    

document.getElementById("node-panel-apply").onclick = () => {
    if (!editingNode) return;
    editingNode.force_x = parseFloat(document.getElementById("node-fx").value) || 0;
    editingNode.force_y = -parseFloat(document.getElementById("node-fy").value) || 0;
    editingNode.is_fixed_x = document.getElementById("node-fixx").checked;
    editingNode.is_fixed_y = document.getElementById("node-fixy").checked;
    document.getElementById("node-panel").style.display = "none";
    editingNode = null;
    draw();
};

document.getElementById("clear-mesh-btn").onclick = () => {
    if (nodes.length === 0 && elements.length === 0) return;
    const confirmed = confirm("Clear the entire mesh? This cannot be undone.");
    if (!confirmed) return;

    nodes = [];
    elements = [];
    nextNodeId = 0;
    selectedNodeIds = [];
    edgeRules = [];
    lastResult = null;
    showStress = false;
    showDeformed = false;
    editingNode = null;
    editingEdge = null;

    syncToggleButton("toggle-stress-btn", showStress);
    syncToggleButton("toggle-deformed-btn", showDeformed);
    closeAllPanels();
    draw();
};

function updateEdgeFieldVisibility() {
    const isFix = document.getElementById("edge-type").value === "fix";
    document.getElementById("edge-fix-fields").style.display = isFix ? "block" : "none";
    document.getElementById("edge-force-fields").style.display = isFix ? "none" : "block";
}

const refineInput = document.getElementById("refine-input");

function updateRefineWarning() {
    const value = parseInt(refineInput.value);
    const isHigh = value > REFINE_WARNING_THRESHOLD;
    refineInput.classList.toggle("refine-warning", isHigh);
    refineInput.title = isHigh ? "High chance of breaking" : "";
}

function shouldShowRefineWarning(refineTimes) {
    if (refineTimes <= REFINE_WARNING_THRESHOLD) return false;
    return localStorage.getItem("suppressRefineWarning") !== "true";
}

function showRefineWarning() {
    return new Promise((resolve) => {
        warningOverlay.style.display = "flex";

        const cleanup = () => {
            warningOverlay.style.display = "none";
            document.getElementById("warning-proceed-btn").onclick = null;
            document.getElementById("warning-cancel-btn").onclick = null;
        };

        document.getElementById("warning-proceed-btn").onclick = () => {
            if (dontShowAgainCheckbox.checked) {
                localStorage.setItem("suppressRefineWarning", "true");
            }
            cleanup();
            resolve(true);
        };

        document.getElementById("warning-cancel-btn").onclick = () => {
            cleanup();
            resolve(false);
        };
    });
}

if (refineInput) {
    refineInput.addEventListener("input", updateRefineWarning);
    updateRefineWarning(); // run once on load in case of a pre-filled value
}

document.getElementById("edge-type").addEventListener("change", updateEdgeFieldVisibility);

document.getElementById("node-panel-cancel").onclick = () => {
    document.getElementById("node-panel").style.display = "none";
    editingNode = null;
};
document.getElementById("edge-panel-cancel").onclick = () => {
    document.getElementById("edge-panel").style.display = "none";
    editingEdge = null;
};

document.getElementById("edge-panel-apply").onclick = () => {
    const type = document.getElementById("edge-type").value;

    const rule = {
        node_a_id: editingEdge.node_a_id,
        node_b_id: editingEdge.node_b_id,
        type: type
    };

    if (type === "fix") {
        rule.fix_x = document.getElementById("edge-fixx").checked;
        rule.fix_y = document.getElementById("edge-fixy").checked;
    } else {
        if (type === "fix") {
            rule.fix_x = document.getElementById("edge-fixx").checked;
            rule.fix_y = document.getElementById("edge-fixy").checked;
        } else {
            rule.force_x = parseFloat(document.getElementById("edge-fx").value) || 0;
            rule.force_y = -parseFloat(document.getElementById("edge-fy").value) || 0;
        }
    }

    edgeRules = edgeRules.filter(r =>
        !(r.node_a_id === rule.node_a_id && r.node_b_id === rule.node_b_id)
    );
    edgeRules.push(rule);

    document.getElementById("edge-panel").style.display = "none";
    editingEdge = null;
    draw();
};

document.getElementById("calculate-btn").onclick = async () => {
    const refineTimes = parseInt(refineInput.value) || 0;
    
    if (shouldShowRefineWarning(refineTimes)) {
        const proceed = await showRefineWarning();
        if (!proceed) return;
    }

    const usedNodeIds = new Set(elements.flatMap(el => el.node_ids));
    const usedNodes = nodes.filter(n => usedNodeIds.has(n.id));
    
    const payload = {
        nodes: usedNodes.map(n => ({
            id: n.id, posx: n.x, posy: n.y,
            force_x: n.force_x, force_y: n.force_y,
            is_fixed_x: n.is_fixed_x, is_fixed_y: n.is_fixed_y
        })),
        elements: elements.map(el => ({
            type: el.type, node_ids: el.node_ids
        })),
        refine_times: refineTimes,
        edge_rules: edgeRules
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
    showStress = true; 
    syncToggleButton("toggle-stress-btn", showStress);
    draw();
};

document.getElementById("toggle-stress-btn").onclick = () => {
    showStress = !showStress;
    syncToggleButton("toggle-stress-btn", showStress);
    draw();
};
document.getElementById("toggle-deformed-btn").onclick = () => {
    showDeformed = !showDeformed;
    syncToggleButton("toggle-deformed-btn", showDeformed);
    draw();
};

document.getElementById("toggle-outlines-btn").onclick = () => {
    showOutlines = !showOutlines;
    syncToggleButton("toggle-outlines-btn", showOutlines);
    draw();
};

const deformSlider = document.getElementById("deform-scale-slider");
const deformMinInput = document.getElementById("deform-scale-min");
const deformMaxInput = document.getElementById("deform-scale-max");

if (deformSlider) {
    deformSlider.addEventListener("input", () => {
        deformationScale = parseFloat(deformSlider.value) || 0;
        document.getElementById("deform-scale-value").textContent = deformationScale;
        draw();
    });
}

if (deformMinInput) {
    deformMinInput.addEventListener("input", () => {
        const min = parseFloat(deformMinInput.value) || 0;
        deformSlider.min = min;
    });
}

if (deformMaxInput) {
    deformMaxInput.addEventListener("input", () => {
        const max = parseFloat(deformMaxInput.value) || 200;
        deformSlider.max = max;
    });

}



draw();
 