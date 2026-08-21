// The API lives on a different origin (port 8000) than this page (8080),
// so every request is cross-origin and relies on the API's CORS allowance.
const API_BASE = "http://127.0.0.1:8000/api/v1";

// SVG elements need their namespace, and map units are scaled to pixels.
const SVG_NS = "http://www.w3.org/2000/svg";
const SCALE = 160;
const MARGIN = 60;
const ZONE_RADIUS = 20;
const DRONE_RADIUS = 9;
// In user units (not screen px), so labels scale with the map and their
// width stays small next to the SCALE-wide gap between zones: no overlap.
const LABEL_FONT_SIZE = 13;
const FRAME_MS = 650;

// The color names the official maps use that are also valid CSS colors.
const KNOWN_COLORS = new Set([
  "black", "gray", "grey", "red", "green", "yellow", "blue", "magenta",
  "purple", "cyan", "white", "orange", "gold", "brown", "maroon",
  "crimson", "darkred", "lime", "violet"
]);
const FALLBACK_COLOR = "#4aa3ff";
// The CLI paints color=rainbow letter by letter, cycling these hues; the web
// mirrors that (and fills a rainbow zone circle with a gradient of them).
const RAINBOW_COLORS = [
  "#e06c75", "#e5c07b", "#98c379", "#56b6c2", "#61afef", "#c678dd"
];

function isRainbow(color) {
  return (color || "").toLowerCase() === "rainbow";
}

let maps = [];         // catalog, to resolve the selected index to a map
let animation = null;  // { frames, drones, timer }
let camera = null;     // { svg, box, baseBox, drag }

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  return response.json();
}

// -- Map picker -------------------------------------------------------------

async function loadMaps() {
  const select = document.getElementById("map-select");
  try {
    maps = await fetchJson(`${API_BASE}/maps`);
    select.textContent = "";
    select.appendChild(option("", "— Choose a map —"));
    for (const map of maps) {
      select.appendChild(option(String(map.index), `${map.index}. ${map.path}`));
    }
  } catch (error) {
    select.textContent = "";
    select.appendChild(option("", "Could not reach the API"));
  }
}

function option(value, text) {
  const el = document.createElement("option");
  el.value = value;
  el.textContent = text;
  return el;
}

function simulateSelected() {
  const value = document.getElementById("map-select").value;
  if (!value) {
    return;
  }
  const map = maps.find((candidate) => candidate.index === Number(value));
  if (map) {
    chooseMap(map);
  }
}

// Changing the picker clears the view: a new map needs a new Simulate click.
function onSelectChange() {
  stopAnimation();
  document.getElementById("result").hidden = true;
}

// Draw the map, run its simulation, and arm the turn-by-turn animation.
async function chooseMap(map) {
  stopAnimation();
  document.getElementById("result-title").textContent = map.path;
  const detail = await fetchJson(`${API_BASE}/maps/${map.index}`);
  renderMapInfo(detail);
  const positions = zonePositions(detail.zones);
  const svg = buildSvg(detail, positions);
  mountMap(svg);
  const result = await fetchJson(`${API_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ index: map.index })
  });
  renderMetrics(result.metrics);
  renderTurns(result.turns, zoneColorMap(detail.zones));
  setupAnimation(detail, positions, result.turns, svg);
  document.getElementById("result").hidden = false;
}

// -- Drawing the static map -------------------------------------------------

function zonePositions(zones) {
  const positions = {};
  for (const zone of zones) {
    positions[zone.name] = { x: zone.x * SCALE, y: zone.y * SCALE };
  }
  return positions;
}

function buildSvg(detail, positions) {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("class", "map-svg");
  svg.setAttribute("viewBox", viewBox(Object.values(positions)));
  svg.appendChild(rainbowDefs());
  for (const conn of detail.connections) {
    svg.appendChild(line(positions[conn.a], positions[conn.b]));
  }
  for (const zone of detail.zones) {
    svg.appendChild(zoneCircle(zone, positions[zone.name], detail));
    svg.appendChild(zoneLabel(zone, positions[zone.name]));
  }
  const drones = document.createElementNS(SVG_NS, "g");
  drones.setAttribute("class", "drones");
  svg.appendChild(drones);
  return svg;
}

// The viewBox is the bounding box of every zone, plus a margin around it.
function viewBox(points) {
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const minX = Math.min(...xs) - MARGIN;
  const minY = Math.min(...ys) - MARGIN;
  const width = Math.max(...xs) - Math.min(...xs) + 2 * MARGIN;
  const height = Math.max(...ys) - Math.min(...ys) + 2 * MARGIN;
  return `${minX} ${minY} ${width} ${height}`;
}

// A gradient of the rainbow hues, used to fill a color=rainbow zone circle.
function rainbowDefs() {
  const defs = document.createElementNS(SVG_NS, "defs");
  const gradient = document.createElementNS(SVG_NS, "linearGradient");
  gradient.setAttribute("id", "rainbow");
  RAINBOW_COLORS.forEach((color, index) => {
    const stop = document.createElementNS(SVG_NS, "stop");
    const share = index / (RAINBOW_COLORS.length - 1);
    stop.setAttribute("offset", `${share * 100}%`);
    stop.setAttribute("stop-color", color);
    gradient.appendChild(stop);
  });
  defs.appendChild(gradient);
  return defs;
}

function line(a, b) {
  const el = document.createElementNS(SVG_NS, "line");
  el.setAttribute("x1", a.x);
  el.setAttribute("y1", a.y);
  el.setAttribute("x2", b.x);
  el.setAttribute("y2", b.y);
  el.setAttribute("class", "conn");
  return el;
}

function zoneCircle(zone, pos, detail) {
  const el = document.createElementNS(SVG_NS, "circle");
  el.setAttribute("cx", pos.x);
  el.setAttribute("cy", pos.y);
  el.setAttribute("r", ZONE_RADIUS);
  el.setAttribute(
    "fill", isRainbow(zone.color) ? "url(#rainbow)" : zoneColor(zone.color)
  );
  const terminal = zone.name === detail.start || zone.name === detail.end;
  el.setAttribute("class", terminal ? "zone zone--terminal" : "zone");
  // Native tooltip: hovering a zone shows its full name even on dense maps
  // where the drawn labels are small or overlap.
  const tooltip = document.createElementNS(SVG_NS, "title");
  tooltip.textContent = zone.name;
  el.appendChild(tooltip);
  return el;
}

function zoneLabel(zone, pos) {
  const el = document.createElementNS(SVG_NS, "text");
  el.setAttribute("x", pos.x);
  el.setAttribute("y", pos.y + ZONE_RADIUS + 22);
  el.setAttribute("text-anchor", "middle");
  el.setAttribute("font-size", LABEL_FONT_SIZE);
  el.setAttribute("class", "zone-label");
  if (isRainbow(zone.color)) {
    for (const child of rainbowChars(zone.name, "tspan")) {
      el.appendChild(child);
    }
  } else {
    el.textContent = zone.name;
  }
  return el;
}

// One element per character of name, each in the next rainbow hue. Kind is
// "tspan" for SVG text, "span" for HTML (the turns modal).
function rainbowChars(name, kind) {
  return [...name].map((character, index) => {
    const color = RAINBOW_COLORS[index % RAINBOW_COLORS.length];
    if (kind === "tspan") {
      const tspan = document.createElementNS(SVG_NS, "tspan");
      tspan.textContent = character;
      tspan.setAttribute("fill", color);
      return tspan;
    }
    const span = document.createElement("span");
    span.textContent = character;
    span.style.color = color;
    return span;
  });
}

function zoneColor(color) {
  if (color && KNOWN_COLORS.has(color.toLowerCase())) {
    return color;
  }
  return FALLBACK_COLOR;
}

// -- Animating the drones ---------------------------------------------------

// Re-derive where each drone stands after every turn, from the plan lines.
// "D<id>-<zone>" lands a drone on a zone; "D<id>-<a>-<b>" is a restricted
// transit, drawn at the midpoint of the connection.
function framesFromTurns(detail, positions, turns) {
  const current = {};
  for (let id = 1; id <= detail.nb_drones; id += 1) {
    current[id] = positions[detail.start];
  }
  const frames = [{ ...current }];
  for (const turnLine of turns) {
    for (const token of turnLine.split(" ")) {
      const parts = token.split("-");
      const id = Number(parts[0].slice(1));
      if (parts.length === 2) {
        current[id] = positions[parts[1]];
      } else {
        current[id] = midpoint(positions[parts[1]], positions[parts[2]]);
      }
    }
    frames.push({ ...current });
  }
  return frames;
}

function midpoint(a, b) {
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
}

function setupAnimation(detail, positions, turns, svg) {
  const frames = framesFromTurns(detail, positions, turns);
  const group = svg.querySelector(".drones");
  const drones = {};
  for (let id = 1; id <= detail.nb_drones; id += 1) {
    const el = document.createElementNS(SVG_NS, "circle");
    el.setAttribute("r", DRONE_RADIUS);
    el.setAttribute("class", "drone");
    placeDrone(el, frames[0][id]);
    group.appendChild(el);
    drones[id] = el;
  }
  animation = { frames, drones, timer: null };
  showFrame(0);
}

function placeDrone(el, point) {
  el.style.transform = `translate(${point.x}px, ${point.y}px)`;
}

function showFrame(index) {
  for (const id of Object.keys(animation.drones)) {
    placeDrone(animation.drones[id], animation.frames[index][id]);
  }
  const last = animation.frames.length - 1;
  document.getElementById("turn-label").textContent =
    `Turn ${index} / ${last}`;
}

function play() {
  if (!animation) {
    return;
  }
  stopTimer();
  showFrame(0);
  let index = 0;
  animation.timer = window.setInterval(() => {
    index += 1;
    showFrame(index);
    if (index >= animation.frames.length - 1) {
      stopTimer();
    }
  }, FRAME_MS);
}

// Stop halts the animation and returns the drones to the start.
function stop() {
  stopTimer();
  if (animation) {
    showFrame(0);
  }
}

function stopTimer() {
  if (animation && animation.timer) {
    window.clearInterval(animation.timer);
    animation.timer = null;
  }
}

function stopAnimation() {
  stopTimer();
  animation = null;
}

// -- Zoom and pan (moving the viewBox window over the drawing) --------------

function mountMap(svg) {
  const view = document.getElementById("map-view");
  view.textContent = "";
  view.appendChild(svg);
  const box = parseBox(svg.getAttribute("viewBox"));
  camera = { svg, box, baseBox: { ...box }, drag: null };
  svg.addEventListener("wheel", onWheel, { passive: false });
  svg.addEventListener("mousedown", onDragStart);
}

function parseBox(text) {
  const [minX, minY, width, height] = text.split(" ").map(Number);
  return { minX, minY, width, height };
}

function applyBox() {
  const b = camera.box;
  camera.svg.setAttribute(
    "viewBox", `${b.minX} ${b.minY} ${b.width} ${b.height}`
  );
}

// Zoom keeping the point under the cursor fixed. factor < 1 zooms in.
function zoomAt(clientX, clientY, factor) {
  if (!camera) {
    return;
  }
  const box = camera.box;
  const nextWidth = box.width * factor;
  if (nextWidth < camera.baseBox.width * 0.2 ||
      nextWidth > camera.baseBox.width * 5) {
    return;
  }
  const rect = camera.svg.getBoundingClientRect();
  const px = (clientX - rect.left) / rect.width;
  const py = (clientY - rect.top) / rect.height;
  const anchorX = box.minX + px * box.width;
  const anchorY = box.minY + py * box.height;
  box.width *= factor;
  box.height *= factor;
  box.minX = anchorX - px * box.width;
  box.minY = anchorY - py * box.height;
  applyBox();
}

function zoomAtCenter(factor) {
  if (!camera) {
    return;
  }
  const rect = camera.svg.getBoundingClientRect();
  zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, factor);
}

// Restore the original viewBox: the whole map, centered.
function resetZoom() {
  if (!camera) {
    return;
  }
  camera.box = { ...camera.baseBox };
  applyBox();
}

function onWheel(event) {
  event.preventDefault();
  zoomAt(event.clientX, event.clientY, event.deltaY < 0 ? 0.9 : 1.1);
}

function onDragStart(event) {
  if (camera) {
    camera.drag = { x: event.clientX, y: event.clientY };
  }
}

function onDragMove(event) {
  if (!camera || !camera.drag) {
    return;
  }
  const rect = camera.svg.getBoundingClientRect();
  const dx = (event.clientX - camera.drag.x) * camera.box.width / rect.width;
  const dy = (event.clientY - camera.drag.y) * camera.box.height / rect.height;
  camera.box.minX -= dx;
  camera.box.minY -= dy;
  camera.drag = { x: event.clientX, y: event.clientY };
  applyBox();
}

function onDragEnd() {
  if (camera) {
    camera.drag = null;
  }
}

// -- Metrics and turns ------------------------------------------------------

// Show the map's own facts (as opposed to the run's metrics).
function renderMapInfo(detail) {
  document.getElementById("map-info").textContent =
    `Drones: ${detail.nb_drones}  ·  Zones: ${detail.zones.length}` +
    `  ·  Connections: ${detail.connections.length}` +
    `  ·  ${detail.start} → ${detail.end}`;
}

function renderMetrics(metrics) {
  const container = document.getElementById("metrics");
  container.textContent = "";
  const figures = [
    ["Turns", metrics.turns],
    ["Total moves", metrics.total_moves],
    ["Drones/turn", metrics.drones_per_turn]
  ];
  for (const [label, value] of figures) {
    container.appendChild(metricCell(label, value));
  }
}

function metricCell(label, value) {
  const cell = document.createElement("div");
  cell.className = "metric";
  const valueEl = document.createElement("span");
  valueEl.className = "metric-value";
  valueEl.textContent = value;
  const labelEl = document.createElement("span");
  labelEl.className = "metric-label";
  labelEl.textContent = label;
  cell.append(valueEl, labelEl);
  return cell;
}

// Paint each turn line, coloring the zone names with their zone color, as
// the CLI --visual view does. A token is "D<id>-<zone>" or "D<id>-<a>-<b>";
// zone names cannot contain dashes, so splitting on "-" is safe.
function renderTurns(turns, colorByName) {
  const list = document.getElementById("turns");
  list.textContent = "";
  for (const movementLine of turns) {
    const item = document.createElement("li");
    movementLine.split(" ").forEach((token, index) => {
      if (index > 0) {
        item.appendChild(document.createTextNode(" "));
      }
      appendToken(item, token, colorByName);
    });
    list.appendChild(item);
  }
}

function appendToken(item, token, colorByName) {
  token.split("-").forEach((part, index) => {
    if (index > 0) {
      item.appendChild(document.createTextNode("-"));
    }
    if (index === 0) {
      item.appendChild(document.createTextNode(part));
    } else {
      appendZoneName(item, part, colorByName[part]);
    }
  });
}

function appendZoneName(item, name, color) {
  if (isRainbow(color)) {
    for (const child of rainbowChars(name, "span")) {
      item.appendChild(child);
    }
    return;
  }
  const span = document.createElement("span");
  span.textContent = name;
  span.style.color = zoneColor(color);
  item.appendChild(span);
}

function zoneColorMap(zones) {
  const colors = {};
  for (const zone of zones) {
    colors[zone.name] = zone.color;
  }
  return colors;
}

function openTurns() {
  document.getElementById("turns-modal").hidden = false;
}

function closeTurns() {
  document.getElementById("turns-modal").hidden = true;
}

// -- Wiring -----------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  loadMaps();
  document.getElementById("simulate-btn")
    .addEventListener("click", simulateSelected);
  document.getElementById("map-select")
    .addEventListener("change", onSelectChange);
  document.getElementById("play-btn").addEventListener("click", play);
  document.getElementById("stop-btn").addEventListener("click", stop);
  document.getElementById("zoom-in")
    .addEventListener("click", () => zoomAtCenter(0.8));
  document.getElementById("zoom-out")
    .addEventListener("click", () => zoomAtCenter(1.25));
  document.getElementById("zoom-reset").addEventListener("click", resetZoom);
  document.getElementById("turns-btn").addEventListener("click", openTurns);
  document.getElementById("turns-close").addEventListener("click", closeTurns);
  const modal = document.getElementById("turns-modal");
  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeTurns();
    }
  });
  window.addEventListener("mousemove", onDragMove);
  window.addEventListener("mouseup", onDragEnd);
});
