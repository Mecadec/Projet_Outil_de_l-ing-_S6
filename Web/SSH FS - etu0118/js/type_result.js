import { getJSON, postJSON } from '../js/api.js';
import { showAlert }         from '../js/utils.js';

const mmsi = new URLSearchParams(location.search).get('mmsi');
if(!mmsi){ showAlert('Aucun MMSI fourni', 'error'); throw 'No MMSI'; }

try {
  /* NOTE the new endpoint ↓ */
  const { data } = await postJSON('php/vessel_type_predict.php', { mmsi });
  document.getElementById('typeOut').textContent = data.type || data;
} catch(err){ showAlert(err.message,'error'); }
