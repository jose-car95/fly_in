// The API lives on a different origin (port 8000) than this page (8080),
// so the request is cross-origin and relies on the API's CORS allowance.
const API_BASE = "http://127.0.0.1:8000/api/v1";

// Ask the API for the map catalog and render it as a list.
async function loadMaps() {
  const list = document.getElementById("map-list");
  try {
    const response = await fetch(`${API_BASE}/maps`);
    const maps = await response.json();
    list.textContent = "";
    for (const map of maps) {
      const item = document.createElement("li");
      item.textContent = `${map.index}. ${map.path}`;
      list.appendChild(item);
    }
  } catch (error) {
    list.textContent = "Could not reach the API. Is it running?";
  }
}

// Run once the page's elements exist.
document.addEventListener("DOMContentLoaded", loadMaps);
