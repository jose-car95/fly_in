// The API lives on a different origin (port 8000) than this page (8080),
// so every request is cross-origin and relies on the API's CORS allowance.
const API_BASE = "http://127.0.0.1:8000/api/v1";

// Ask the API for the catalog and render each map as a clickable button.
async function loadMaps() {
  const list = document.getElementById("map-list");
  try {
    const response = await fetch(`${API_BASE}/maps`);
    const maps = await response.json();
    list.textContent = "";
    for (const map of maps) {
      list.appendChild(mapItem(map));
    }
  } catch (error) {
    list.textContent = "Could not reach the API. Is it running?";
  }
}

// One map as a button that runs its simulation when clicked.
function mapItem(map) {
  const item = document.createElement("li");
  const button = document.createElement("button");
  button.className = "map-btn";
  button.textContent = `${map.index}. ${map.path}`;
  button.addEventListener("click", () => simulate(map));
  item.appendChild(button);
  return item;
}

// Send the chosen map to the API and show its plan and metrics.
async function simulate(map) {
  const response = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ index: map.index })
  });
  const result = await response.json();
  renderResult(map, result);
}

// Paint the metrics and one line per turn into the result section.
function renderResult(map, result) {
  document.getElementById("result-title").textContent = map.path;
  renderMetrics(result.metrics);
  renderTurns(result.turns);
  document.getElementById("result").hidden = false;
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

function renderTurns(turns) {
  const list = document.getElementById("turns");
  list.textContent = "";
  for (const line of turns) {
    const item = document.createElement("li");
    item.textContent = line;
    list.appendChild(item);
  }
}

// Run once the page's elements exist.
document.addEventListener("DOMContentLoaded", loadMaps);
