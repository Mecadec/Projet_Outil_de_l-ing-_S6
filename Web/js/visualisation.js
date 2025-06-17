document.addEventListener('DOMContentLoaded', function() {
    // URL de l'API pour récupérer les données des bateaux
    const API_URL = '../php/get_ships.php';
    
    // Éléments du DOM
    const boatsTableBody = document.querySelector('#boats-table tbody');
    
    // Fonction pour formater la date
    function formatDate(dateString) {
        const options = { 
            year: 'numeric', 
            month: '2-digit', 
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        };
        return new Date(dateString).toLocaleString('fr-FR', options);
    }
    
    // Fonction pour charger les données des bateaux
    async function loadBoatsData() {
        try {
            const response = await fetch(API_URL);
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            const responseData = await response.json();
            
            // Vérifier si la réponse contient des données
            if (!responseData || !responseData.success) {
                throw new Error(responseData.error || 'Erreur lors de la récupération des données');
            }

            const shipsData = responseData.data || [];
            
            // Vider le tableau avant d'ajouter de nouvelles données
            boatsTableBody.innerHTML = '';
            
            if (!Array.isArray(shipsData) || shipsData.length === 0) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td colspan="6" class="text-center">Aucun bateau trouvé</td>
                `;
                boatsTableBody.appendChild(row);
                return;
            }
            
            // Ajouter chaque bateau au tableau
            shipsData.forEach(ship => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${ship.MMSI || 'N/A'}</td>
                    <td>${ship.VesselName || 'Inconnu'}</td>
                    <td>${ship.VesselType || 'N/A'}</td>
                    <td>${ship.Callsign || 'N/A'}</td>
                    <td>${ship.IMO || 'N/A'}</td>
                    <td>${ship.Cluster || 'Non classé'}</td>
                `;
                boatsTableBody.appendChild(row);
            });
            
            // Initialiser la carte si elle existe sur la page
            if (document.getElementById('map')) {
                initializeMap(shipsData);
            }
            
        } catch (error) {
            console.error('Erreur lors du chargement des données des bateaux:', error);
            boatsTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-danger">
                        Erreur lors du chargement des données. Veuillez réessayer plus tard.
                    </td>
                </tr>`;
        }
    }
    
    // Fonction pour initialiser la carte avec les positions des bateaux
    function initializeMap(boatsData) {
        // Vérifier si Mapbox est chargé
        if (typeof mapboxgl === 'undefined') {
            console.error('Mapbox GL JS non chargé');
            return;
        }
        
        // Initialiser la carte
        mapboxgl.accessToken = 'pk.eyJ1IjoiZXR1MDExMCIsImEiOiJjbHNtZzV5cWswb3FhMmpxcGJ6bDZkZ2VxIn0.5Xp5X5X5X5X5X5X5X5Xw';
        const map = new mapboxgl.Map({
            container: 'map',
            style: 'mapbox://styles/mapbox/streets-v11',
            center: [2.3522, 48.8566], // Paris par défaut
            zoom: 5
        });
        
        // Ajouter les marqueurs pour chaque bateau
        boatsData.forEach(boat => {
            if (boat.latitude && boat.longitude) {
                new mapboxgl.Marker()
                    .setLngLat([parseFloat(boat.longitude), parseFloat(boat.latitude)])
                    .setPopup(new mapboxgl.Popup().setHTML(`
                        <div>
                            <h4>Bateau MMSI: ${boat.mmsi || 'N/A'}</h4>
                            <p>Vitesse: ${boat.vitesse || 'N/A'} nœuds</p>
                            <p>Cap: ${boat.cap || 'N/A'}°</p>
                            <p>Dernière mise à jour: ${boat.date_heure ? formatDate(boat.date_heure) : 'N/A'}</p>
                        </div>
                    `))
                    .addTo(map);
            }
        });
        
        // Ajuster la vue pour afficher tous les marqueurs
        if (boatsData.length > 0) {
            const bounds = new mapboxgl.LngLatBounds();
            boatsData.forEach(boat => {
                if (boat.latitude && boat.longitude) {
                    bounds.extend([parseFloat(boat.longitude), parseFloat(boat.latitude)]);
                }
            });
            map.fitBounds(bounds, { padding: 50 });
        }
    }
    
    // Charger les données au chargement de la page
    if (window.location.pathname.includes('visualisation.html')) {
        loadBoatsData();
    }
});
