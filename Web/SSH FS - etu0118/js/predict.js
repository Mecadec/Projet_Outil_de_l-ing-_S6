

mapboxgl.accessToken = 'pk.eyJ1IjoibWVjYWRlYyIsImEiOiJjbWMwa3E3enEwMTY4MmtwajlybTI0cHBvIn0.ViQ5X-5mq08GAYbszceg8A';   // ← ton token

let map, curMarker;        // objets persistants
const LINE_ID   = 'predLine';
const POINT_ID  = 'predPoints';


  import {logDebug, showAlert} from '../js/utils.js';
  import {getJSON, postJSON}   from '../js/api.js';
export const chooser  = document.getElementById('shipChooser');
export const PER_PAGE = 10;
export let   ships    = [];          // etc.

  const mapCard = document.getElementById('map-card');
  const tbody   = document.getElementById('predTableBody');

  function renderPage() {
    const start = pageIdx * PER_PAGE;
    const slice = ships.slice(start, start + PER_PAGE);
  
    chooser.innerHTML = slice.map((s, i) => `
      <label class="d-flex align-items-center gap-2">
        <input type="radio" name="mmsi" value="${s.MMSI}" ${i === 0 ? 'checked' : ''}/>
        ${s.VesselName || 'Sans nom'} (MMSI ${s.MMSI})
      </label>`).join('');
  
    // forcer sélection du premier élément de la page
    chooser.querySelector('input[name=mmsi]').dispatchEvent(new Event('change'));
  
    document.getElementById('pageInfo').textContent =
      `${pageIdx + 1} / ${Math.ceil(ships.length / PER_PAGE)}`;
  }
  
  chooser.addEventListener('change', e => handleSelect(e.target.value));
  
  
    // ───────────────────────────────────────── tableau
    function renderTable(preds){
      tbody.innerHTML = preds.map(p=>`
        <tr>
          <td>+${p.minutes} min</td>
          <td>${p.lat.toFixed(5)}</td>
          <td>${p.lon.toFixed(5)}</td>
        </tr>`).join('');
    }
  

  // ───────────────────────────────────────── sélection d’un MMSI
  async function handleSelect(mmsi){
    if(!mmsi) return;
    try {
      /* 1. Dernier point */
      const {data:[pt]} = await getJSON(`php/get_point.php?mmsi=${mmsi}&limit=1`);
      if(!pt){ showAlert('Aucun point trouvé','error'); return; }

// ─── appel prédiction + compatibilité enveloppe {success,data:…} ───
const resp = await postJSON('php/predict.php', { mmsi });
const obj  = resp.data ?? resp;      // prend resp.data si présent, sinon resp

console.log('payload reçu', obj);    // (optionnel) vérif dans la console

renderMap(obj);
renderTable(obj.predictions);

      mapCard.style.display='block';
    }catch(e){ showAlert(e.message,'error'); }
  }
// paramètres pagination
let pageIdx   = 0;      // page courante 0-based

(async function init() {
  try {
    ships = (await getJSON('php/get_ships.php')).data;
    if (!ships.length) {
      chooser.textContent = 'Aucun navire';
      return;
    }

    // boutons
    document.getElementById('prevBtn').onclick = () => changePage(-1);
    document.getElementById('nextBtn').onclick = () => changePage(+1);

    renderPage();
  } catch (err) { showAlert(err.message, 'error'); }
})();

function changePage(delta) {
  const maxPage = Math.ceil(ships.length / PER_PAGE) - 1;
  pageIdx = Math.min(Math.max(0, pageIdx + delta), maxPage);
  renderPage();
}


  /* ───────────────────────── Ajout couleurs prédiction */
const COLORS = {5: 'red', 10: 'orange', 15: 'yellow'};

function renderMap(obj) {
    const [lat, lon] = obj.now;
  
    /* ── 1. initialisation (une seule fois) ───────────────── */
    if (!map) {
      map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [lon, lat],
        zoom: 8
      });
  
      // contrôle zoom + rotation
      map.addControl(new mapboxgl.NavigationControl());
    } else {
      map.setCenter([lon, lat]);
    }
  
    /* ── 2. marqueur position actuelle ────────────────────── */
    if (curMarker) curMarker.remove();
    curMarker = new mapboxgl.Marker({color:'#0067ff'})
                 .setLngLat([lon, lat])
                 .setPopup(new mapboxgl.Popup().setHTML('Position actuelle'))
                 .addTo(map);
  
    /* ── 3. préparer GeoJSON pour la ligne et les points ──── */
    const coords = [[lon, lat], ...obj.predictions.map(p => [p.lon, p.lat])];
  
    const geoLine = {
      'type': 'Feature',
      'geometry': { 'type': 'LineString', 'coordinates': coords }
    };
  
    const geoPoints = {
      'type': 'FeatureCollection',
      'features': obj.predictions.map(p => ({
        'type':'Feature',
        'properties': { 'minutes': p.minutes },
        'geometry': { 'type':'Point', 'coordinates':[p.lon, p.lat] }
      }))
    };
  
    /* ── 4. mettre à jour / créer sources & couches ───────── */
    map.once('load', () => addLayers());           // 1ᵉʳ chargement
    if (map.isStyleLoaded()) addLayers();          // appels suivants
  
    function addLayers() {
      // -------- ligne
      if (map.getSource(LINE_ID)) {
        map.getSource(LINE_ID).setData(geoLine);
      } else {
        map.addSource(LINE_ID, { 'type':'geojson', 'data': geoLine });
        map.addLayer({
          'id': LINE_ID,
          'type':'line',
          'source': LINE_ID,
          'layout': { 'line-join':'round', 'line-cap':'round' },
          'paint': { 'line-color':'#8338ec', 'line-width':3 }
        });
      }
  
      // -------- points
      if (map.getSource(POINT_ID)) {
        map.getSource(POINT_ID).setData(geoPoints);
      } else {
        map.addSource(POINT_ID, { 'type':'geojson', 'data': geoPoints });
        map.addLayer({
          'id': POINT_ID,
          'type':'circle',
          'source': POINT_ID,
          'paint': {
            'circle-radius':6,
            'circle-color': [
              'match', ['get','minutes'],
              5,  '#ff0000',
              10, '#ffa500',
              15, '#ffff00',
              /* other */ '#000'
            ],
            'circle-stroke-width':1,
            'circle-stroke-color':'#000'
          }
        });
      }
    }
  }
  

/* ===================== tableau récap ==================== 
function renderTable(obj) {
  tbody.innerHTML = obj.predictions.map(p => `
    <tr>
      <td>+${p.minutes} min</td>
      <td>${p.lat.toFixed(5)}</td>
      <td>${p.lon.toFixed(5)}</td>
    </tr>`).join('');
}
*/