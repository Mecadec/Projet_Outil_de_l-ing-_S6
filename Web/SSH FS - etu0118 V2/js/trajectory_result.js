
mapboxgl.accessToken = 'pk.eyJ1IjoibWVjYWRlYyIsImEiOiJjbWMwa3E3enEwMTY4MmtwajlybTI0cHBvIn0.ViQ5X-5mq08GAYbszceg8A';
import { showAlert } from '../js/utils.js';
import { postJSON }  from '../js/api.js';

/* Identifiants Mapbox */
const LINE_ID  = 'predLine';
const POINT_ID = 'predPoints';
const COLORS   = {5:'#ff0000', 10:'#ffa500', 15:'#ffff00'};

let map, curMarker;           // objets persistants
const tbody = document.getElementById('predTableBody');

/* 1. Récupérer le MMSI de l'URL */
const mmsi = new URLSearchParams(location.search).get('mmsi');
if (!mmsi) {
  showAlert('MMSI manquant', 'error');
  throw new Error('No MMSI');
}

/* 2. Appel backend + rendu */
(async function init() {
  try {
    const resp = await postJSON('php/predict.php', { mmsi });
    const obj  = resp.data ?? resp;   // compat enveloppe {success,data:…}
    renderMap(obj);
    renderTable(obj.predictions);
  } catch (err) { showAlert(err.message, 'error'); }
})();

/* ───────────────────────────────────────── Helpers */
function renderTable(preds) {
  tbody.innerHTML = preds.map(p => `
    <tr>
      <td>+${p.minutes} min</td>
      <td>${p.lat.toFixed(5)}</td>
      <td>${p.lon.toFixed(5)}</td>
    </tr>`).join('');
}

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
    map.addControl(new mapboxgl.NavigationControl());
  } else {
    map.setCenter([lon, lat]);
  }

  /* ── 2. marqueur position actuelle ────────────────────── */
  if (curMarker) curMarker.remove();
  curMarker = new mapboxgl.Marker({ color: '#0067ff' })
    .setLngLat([lon, lat])
    .setPopup(new mapboxgl.Popup().setHTML('Position actuelle'))
    .addTo(map);

  /* ── 3. préparer GeoJSON pour la ligne et les points ──── */
  const coords = [[lon, lat], ...obj.predictions.map(p => [p.lon, p.lat])];

  const geoLine = {
    type: 'Feature',
    geometry: { type: 'LineString', coordinates: coords }
  };

  const geoPoints = {
    type: 'FeatureCollection',
    features: obj.predictions.map(p => ({
      type: 'Feature',
      properties: { minutes: p.minutes },
      geometry: { type: 'Point', coordinates: [p.lon, p.lat] }
    }))
  };

  /* ── 4. mettre à jour / créer sources & couches ───────── */
  map.once('load', () => addLayers());          // premier chargement
  if (map.isStyleLoaded()) addLayers();        // rafraîchissements

  function addLayers() {
    // -------- ligne
    if (map.getSource(LINE_ID)) {
      map.getSource(LINE_ID).setData(geoLine);
    } else {
      map.addSource(LINE_ID, { type: 'geojson', data: geoLine });
      map.addLayer({
        id: LINE_ID,
        type: 'line',
        source: LINE_ID,
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: { 'line-color': '#8338ec', 'line-width': 3 }
      });
    }

    // -------- points
    if (map.getSource(POINT_ID)) {
      map.getSource(POINT_ID).setData(geoPoints);
    } else {
      map.addSource(POINT_ID, { type: 'geojson', data: geoPoints });
      map.addLayer({
        id: POINT_ID,
        type: 'circle',
        source: POINT_ID,
        paint: {
          'circle-radius': 6,
          'circle-color': [
            'match', ['get', 'minutes'],
            5, COLORS[5],
            10, COLORS[10],
            15, COLORS[15],
            /* other */ '#000'
          ],
          'circle-stroke-width': 1,
          'circle-stroke-color': '#000'
        }
      });
    }
  }
}