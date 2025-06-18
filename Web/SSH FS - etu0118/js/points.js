// points.js – logique points de données
import { logDebug, showAlert } from "./utils.js";
import { getJSON, postJSON } from "./api.js";


console.log('%c[points.js] initialisé', 'color:#29f');

export function initPoints() {
  const pointsList  = document.getElementById("pointsList");
  const addPointFrm = document.getElementById("addPointForm");
  if (pointsList)   loadPoints(pointsList).catch(console.error);
  if (addPointFrm)  addPointFrm.addEventListener("submit", onSubmit);

  async function loadPoints(container) {
    container.innerHTML = "<p>Chargement des points…</p>";
    const { data } = await getJSON("php/get_point.php?limit=20");
    console.log('[RESP]', resp.status, await resp.clone().text());

    if (!data.length) { container.innerHTML = "<p>Aucun point.</p>"; return; }
    container.innerHTML = `
      <div class="points-grid">
        ${data.map(renderPoint).join("")}
      </div>`;
  }

  function renderPoint(p) {
    return `<div class="point-card"><div class="point-info">
      <strong>MMSI:</strong> ${p.MMSI}<br>
      <strong>ID:</strong> ${p.ID}<br>
      <strong>Date/Heure:</strong> ${p.BaseDateTime}<br>
      <strong>Lat/Lon:</strong> ${p.LAT}/${p.LON}<br>
      <strong>SOG:</strong> ${p.SOG}  – <strong>COG:</strong> ${p.COG}<br>
      <strong>Heading:</strong> ${p.HEADING}  – <strong>Status:</strong> ${p.Status}
    </div></div>`;
  }

  async function onSubmit(e) {
    e.preventDefault();
    const f = e.target;
    const body = Object.fromEntries(new FormData(f).entries());

    // normaliser date locale ➜ MySQL DATETIME
    if (body.BaseDateTime && body.BaseDateTime.includes("T")) {
      body.BaseDateTime = body.BaseDateTime.replace("T", " ") + ":00";
    }

    // cast numériques (les vides deviennent 0)
    ["LAT","LON","SOG","COG","HEADING","Draft"].forEach(k => body[k] = +body[k]||0);
    body.Status = parseInt(body.Status || 0, 10);

    await postJSON("php/add_point.php", body);

    showAlert("Point ajouté !", "success");
    f.reset();  pointsList && loadPoints(pointsList);
  }
}
