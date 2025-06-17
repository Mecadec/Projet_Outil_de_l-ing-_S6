// Fonction utilitaire pour la journalisation
function logDebug(message, data = null) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    console.log(logMessage);
    
    if (data !== null) {
        console.log('Données:', data);
    }
}

// Fonction pour afficher des messages d'alerte
function showAlert(message, type) {
    // Supprimer les alertes existantes
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }

    // Créer une nouvelle alerte
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    // Insérer l'alerte avant le conteneur principal
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    } else {
        document.body.insertBefore(alertDiv, document.body.firstChild);
    }
    
    // Supprimer l'alerte après 5 secondes
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Fonction pour charger la liste des navires
async function loadShips() {
    const shipsList = document.getElementById('shipsList');
    if (!shipsList) return;
    
    try {
        shipsList.innerHTML = '<p>Chargement des navires...</p>';
        
        // Récupérer la liste des navires depuis le serveur
        const response = await fetch('php/get_ships.php');
        
        // Vérifier si la réponse est OK (statut 200-299)
        if (!response.ok) {
            const errorText = await response.text();
            try {
                // Essayer de parser l'erreur comme du JSON
                const errorData = JSON.parse(errorText);
                throw new Error(errorData.error || 'Erreur lors du chargement des navires');
            } catch (e) {
                // Si le parsing échoue, utiliser le texte brut
                throw new Error(`Erreur ${response.status}: ${response.statusText}`);
            }
        }
        
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Erreur lors du chargement des navires');
        }

        const ships = result.data || [];

        if (ships.length === 0) {
            shipsList.innerHTML = '<p>Aucun navire enregistré pour le moment.</p>';
            return;
        }

        // Afficher la liste des navires
        let html = '<div class="ships-grid">';
        ships.forEach(ship => {
            html += `
                <div class="ship-card">
                    <div class="ship-info">
                        <h3>${ship.VesselName || 'Sans nom'}</h3>
                        <div class="ship-details">
                            <div class="ship-detail">
                                <span>MMSI:</span> ${ship.MMSI || 'N/A'}
                            </div>
                            <div class="ship-detail">
                                <span>IMO:</span> ${ship.IMO || 'N/A'}
                            </div>
                            <div class="ship-detail">
                                <span>Indicatif:</span> ${ship.Callsign || 'N/A'}
                            </div>
                            <div class="ship-detail">
                                <span>Dimensions:</span> ${ship.Length || '0'}m x ${ship.Width || '0'}m
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        shipsList.innerHTML = html;
    } catch (error) {
        console.error('Erreur lors du chargement des navires:', error);
        
        // Afficher un message d'erreur à l'utilisateur
        showAlert(`Erreur: ${error.message || 'Impossible de charger les navires'}`, 'error');
        
        // Afficher un message d'erreur dans la liste
        if (shipsList) {
            shipsList.innerHTML = `
                <div class="error-message">
                    <p>Une erreur est survenue lors du chargement des navires.</p>
                    <p>Détails: ${error.message || 'Erreur inconnue'}</p>
                    <button onclick="loadShips()" class="btn">Réessayer</button>
                </div>`;
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Éléments du DOM
    const addShipForm = document.getElementById('addShipForm');
    const shipsList = document.getElementById('shipsList');
    const addPointForm = document.getElementById('addPointForm');
    const pointsList = document.getElementById('pointsList');

    // Charger la liste des navires au chargement de la page
    if (shipsList) {
        logDebug('Chargement initial de la liste des navires...');
        loadShips().catch(error => {
            logDebug('Erreur lors du chargement initial des navires:', error);
        });
    }

    // Gestion de la soumission du formulaire
    if (addShipForm) {
        addShipForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            logDebug('Début de la soumission du formulaire');
            
            // Récupérer les données du formulaire
            const formData = {
                MMSI: document.getElementById('mmsi')?.value || '',
                VesselName: document.getElementById('vesselName')?.value || '',
                IMO: document.getElementById('imo')?.value || '',
                Callsign: document.getElementById('callsign')?.value || '',
                Length: parseFloat(document.getElementById('length')?.value) || 0,
                Width: parseFloat(document.getElementById('width')?.value) || 0,
                TransceiverClass: document.getElementById('transceiverClass')?.value || 'A'
            };
            
            logDebug('Données du formulaire préparées', formData);

            try {
                logDebug('Envoi de la requête au serveur...');
                // Envoyer les données au serveur
                const response = await fetch('php/add_ship.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });

                logDebug(`Réponse reçue, statut: ${response.status} ${response.statusText}`);
                
                let data;
                try {
                    const responseText = await response.text();
                    logDebug('Réponse brute du serveur:', responseText);
                    
                    try {
                        data = JSON.parse(responseText);
                        logDebug('Réponse JSON parsée avec succès', data);
                    } catch (jsonError) {
                        logDebug('Erreur lors du parsing de la réponse JSON', {
                            error: jsonError,
                            responseText: responseText
                        });
                        throw new Error(`La réponse du serveur n'est pas au format JSON valide: ${jsonError.message}`);
                    }
                } catch (error) {
                    logDebug('Erreur lors de la lecture de la réponse', error);
                    throw error;
                }

                if (response.ok) {
                    logDebug('Succès de l\'opération');
                    // Afficher un message de succès
                    showAlert('Navire ajouté avec succès !', 'success');
                    // Réinitialiser le formulaire
                    if (addShipForm) addShipForm.reset();
                    // Recharger la liste des navires
                    loadShips();
                } else {
                    // Afficher un message d'erreur
                    const errorMessage = data.error || `Erreur HTTP ${response.status}: ${response.statusText}`;
                    logDebug('Erreur du serveur:', errorMessage);
                    showAlert(`Erreur: ${errorMessage}`, 'error');
                }
            } catch (error) {
                logDebug('Erreur lors de la soumission du formulaire:', error);
                showAlert(`Erreur: ${error.message || 'Une erreur est survenue lors de l\'ajout du navire'}`, 'error');
            } finally {
                logDebug('Fin de la soumission du formulaire');
            }
        });
    }

    // Fonction pour charger la liste des points
    async function loadPoints() {
        if (!pointsList) return;
        try {
            pointsList.innerHTML = '<p>Chargement des points de données...</p>';
            const response = await fetch('php/get_point.php');
            if (!response.ok) {
                const errorText = await response.text();
                try {
                    const errorData = JSON.parse(errorText);
                    throw new Error(errorData.error || 'Erreur lors du chargement des points');
                } catch (e) {
                    throw new Error(`Erreur ${response.status}: ${response.statusText}`);
                }
            }
            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error || 'Erreur lors du chargement des points');
            }
            const points = result.data || [];
            if (points.length === 0) {
                pointsList.innerHTML = '<p>Aucun point de donnée enregistré pour le moment.</p>';
                return;
            }
            // Afficher la liste des points
            let html = '<div class="points-grid">';
            points.forEach(point => {
                html += `
                    <div class="point-card">
                        <div class="point-info">
                            <strong>ID:</strong> ${point.ID || 'N/A'}<br>
                            <strong>MMSI:</strong> ${point.MMSI || 'N/A'}<br>
                            <strong>Date/Heure:</strong> ${point.BaseDateTime || 'N/A'}<br>
                            <strong>Lat:</strong> ${point.LAT || 'N/A'}<br>
                            <strong>Lon:</strong> ${point.LON || 'N/A'}<br>
                            <strong>SOG:</strong> ${point.SOG || 'N/A'}<br>
                            <strong>COG:</strong> ${point.COG || 'N/A'}<br>
                            <strong>Heading:</strong> ${point.HEADING || 'N/A'}<br>
                            <strong>Status:</strong> ${point.Status || 'N/A'}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            pointsList.innerHTML = html;
        } catch (error) {
            console.error('Erreur lors du chargement des points:', error);
            pointsList.innerHTML = `<p class="error">Erreur lors du chargement des points : ${error.message}</p>`;
        }
    }

    // Charger la liste des points au chargement de la page
    if (pointsList) {
        logDebug('Chargement initial de la liste des points...');
        loadPoints().catch(error => {
            logDebug('Erreur lors du chargement initial des points:', error);
        });
    }

    // Gestion de la soumission du formulaire d'ajout de point
    if (addPointForm) {
        addPointForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            logDebug('Début de la soumission du formulaire de point');
            // Récupérer les données du formulaire
            const formData = {
                ID: document.getElementById('pointId')?.value || '',
                MMSI: document.getElementById('pointMmsi')?.value || '',
                BaseDateTime: document.getElementById('pointBaseDateTime')?.value || '',
                LAT: parseFloat(document.getElementById('pointLat')?.value) || 0,
                LON: parseFloat(document.getElementById('pointLon')?.value) || 0,
                SOG: parseFloat(document.getElementById('pointSog')?.value) || 0,
                COG: parseFloat(document.getElementById('pointCog')?.value) || 0,
                HEADING: parseFloat(document.getElementById('pointHeading')?.value) || 0,
                Status: parseInt(document.getElementById('pointStatus')?.value) || 0,
                Draft: parseFloat(document.getElementById('pointDraft')?.value) || 0  // Ajoutez cette ligne
            };
            logDebug('Données du formulaire de point préparées', formData);
            try {
                logDebug('Envoi de la requête au serveur (point)...');
                const response = await fetch('php/add_point.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                logDebug(`Réponse reçue, statut: ${response.status} ${response.statusText}`);
                let data;
                try {
                    const responseText = await response.text();
                    logDebug('Réponse brute du serveur (point):', responseText);
                    try {
                        data = JSON.parse(responseText);
                        logDebug('Réponse JSON point parsée avec succès', data);
                    } catch (jsonError) {
                        logDebug('Erreur lors du parsing de la réponse JSON (point)', {
                            error: jsonError,
                            responseText: responseText
                        });
                        throw new Error(`La réponse du serveur n'est pas au format JSON valide: ${jsonError.message}`);
                    }
                } catch (error) {
                    logDebug('Erreur lors de la lecture de la réponse (point)', error);
                    throw error;
                }
                if (response.ok) {
                    logDebug('Succès de l\'opération point');
                    showAlert('Point ajouté avec succès !', 'success');
                    if (addPointForm) addPointForm.reset();
                    loadPoints();
                } else {
                    const errorMessage = data.error || `Erreur HTTP ${response.status}: ${response.statusText}`;
                    logDebug('Erreur du serveur (point):', errorMessage);
                    showAlert(`Erreur: ${errorMessage}`, 'error');
                }
            } catch (error) {
                logDebug('Erreur lors de la soumission du formulaire de point:', error);
                showAlert(`Erreur: ${error.message || 'Une erreur est survenue lors de l\'ajout du point'}`, 'error');
            } finally {
                logDebug('Fin de la soumission du formulaire de point');
            }
        });
    }
});


const map = L.map('map').setView([48, -4], 5);                 // centre par défaut
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            { attribution:'© OSM' }).addTo(map);

document.getElementById('predictForm').addEventListener('submit', async e=>{
  e.preventDefault();
  const body = {
    mmsi:   +predMmsi.value,
    lat:    +predLat.value,
    lon:    +predLon.value,
    speed:  +predSog.value,
    heading:+predCog.value
  };

  try {
    const res  = await fetch('/php/predict.php', {
                  method:'POST',
                  headers:{'Content-Type':'application/json'},
                  body: JSON.stringify(body)
                });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || res.statusText);

    // Nettoyer ancienne prédiction
    map.eachLayer(l=>{ if (l.options && l.options.pred) map.removeLayer(l); });

    // Marqueur actuel
    const cur = L.marker(json.now, {pred:true}).addTo(map)
                 .bindPopup(`Navire ${json.mmsi}<br>Position actuelle`).openPopup();
    map.setView(json.now, 9);

    // Segments et marqueurs futurs
    json.predictions.forEach(p=>{
      const line = L.polyline([json.now, [p.lat, p.lon]],
                    {color:'red',weight:2, dashArray:'4', pred:true})
                    .addTo(map)
                    .bindTooltip(`+${p.minutes} min`);
      const tri  = L.marker([p.lat, p.lon],
                    {icon: L.divIcon({className:'',html:'▲', iconSize:[12,12]}), pred:true})
                    .addTo(map);
    });

  } catch(err){
     alert('Erreur prédiction: '+err.message);
  }
});


// ------------------------------------------------------------------
//  Prédiction TYPE DE NAVIRE
// ------------------------------------------------------------------
const vtForm   = document.getElementById('vesselTypeForm');
const vtResult = document.getElementById('vesselTypeResult');

if (vtForm) {
  vtForm.addEventListener('submit', async e => {
    e.preventDefault();
    const body = {
      SOG:  parseFloat(vtSog.value),
      COG:  parseFloat(vtCog.value),
      Length: parseFloat(vtLen.value),
      Width:  parseFloat(vtWid.value),
      Draft:  parseFloat(vtDraft.value),
      Latitude:  parseFloat(vtLat.value),
      Longitude: parseFloat(vtLon.value)
    };

    try {
      const res  = await fetch('/php/predict_type.php', {
                     method:'POST',
                     headers:{'Content-Type':'application/json'},
                     body: JSON.stringify(body)
                   });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || res.statusText);

      vtResult.innerHTML =
        `<p>Type prédit : <strong>${json.vessel_type}</strong>`
        + (json.confidence !== null
           ? ` (confiance ≈ ${json.confidence*100|0} %)</p>` : '</p>');
      showAlert('Prédiction effectuée', 'success');
    } catch (err) {
      showAlert(`Erreur prédiction : ${err.message}`, 'error');
    }
  });
}
