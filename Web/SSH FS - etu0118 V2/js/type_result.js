import { getJSON, postJSON } from '../js/api.js';
import { showAlert }         from '../js/utils.js';

const mmsi = new URLSearchParams(location.search).get('mmsi');
if(!mmsi){ showAlert('Aucun MMSI fourni', 'error'); throw 'No MMSI'; }

try {
  /* NOTE the new endpoint ↓ */
  const { data } = await postJSON('php/vessel_type_predict.php', { mmsi });
  document.getElementById('typeOut').textContent = data.type || data;
} catch(err){ showAlert(err.message,'error'); }
import { showAlert } from '../js/utils.js';
import { postJSON }  from '../js/api.js';

/* 1. Récupérer le MMSI de l'URL */
const mmsi = new URLSearchParams(location.search).get('mmsi');
const out  = document.getElementById('typeOut');

if (!mmsi) {
  showAlert('MMSI manquant', 'error');
  out.textContent = '–';
  throw new Error('No MMSI');
}

/* 2. Appel backend + affichage */
(async function init() {
  try {
    const resp = await postJSON('php/predict_type.php', { mmsi });
    const obj  = resp.data ?? resp;   // compat enveloppe
    out.textContent = obj.type ?? obj;
  } catch (err) {
    showAlert(err.message, 'error');
    out.textContent = 'Erreur';
  }
})();