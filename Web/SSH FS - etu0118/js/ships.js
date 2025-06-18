// ships.js – logique navires
import { logDebug, showAlert } from "./utils.js";
import { getJSON, postJSON } from "./api.js";

export function initShips() {
  const shipsList  = document.getElementById("shipsList");
  const addShipFrm = document.getElementById("addShipForm");
  if (shipsList)   loadShips(shipsList).catch(console.error);
  if (addShipFrm)  addShipFrm.addEventListener("submit", onSubmit);

  async function loadShips(container) {
    container.innerHTML = "<p>Chargement des navires…</p>";
    const { data } = await getJSON("php/get_ships.php");
    if (!data.length) {
      container.innerHTML = "<p>Aucun navire enregistré.</p>";
      return;
    }
    container.innerHTML = `
      <div class="ships-grid">
        ${data.map(renderShip).join("")}
      </div>`;
  }

  function renderShip(s) {
    return `<div class="ship-card"><div class="ship-info">
       <h3>${s.VesselName ?? "Sans nom"}</h3>
       <div class="ship-details">
         <div class="ship-detail"><span>MMSI:</span> ${s.MMSI}</div>
         <div class="ship-detail"><span>IMO:</span>  ${s.IMO}</div>
         <div class="ship-detail"><span>Indicatif:</span> ${s.Callsign}</div>
         <div class="ship-detail"><span>Dim:</span> ${s.Length}×${s.Width} m</div>
       </div></div></div>`;
  }

  async function onSubmit(e) {
    e.preventDefault();
    const f = e.target;
    const body = Object.fromEntries(new FormData(f).entries());
    body.Length = +body.Length; body.Width = +body.Width; body.Draft = +body.Draft;
    await postJSON("php/add_ship.php", body);
    showAlert("Navire ajouté !", "success");
    f.reset();  shipsList && loadShips(shipsList);
  }
}
