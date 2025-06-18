document.addEventListener('DOMContentLoaded', function() {
    
    // Éléments du DOM
    const boatsTableBody = document.querySelector('#boats-table tbody');
    
    // Initialisation de la carte Mapbox
    mapboxgl.accessToken = 'pk.eyJ1IjoibWVjYWRlYyIsImEiOiJjbWMwa3E3enEwMTY4MmtwajlybTI0cHBvIn0.ViQ5X-5mq08GAYbszceg8A';
    
    // Création de la carte centrée sur le golfe du Mexique
    const map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [-90.0, 25.0], // Coordonnées du golfe du Mexique
        zoom: 3 // Niveau de zoom pour voir toute la zone
    });
    
    // Ajout des contrôles de navigation
    map.addControl(new mapboxgl.NavigationControl());
    
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

    async function loadTrajet(mmsi) {
        const API_URL = `../php/get_point.php?mmsi=${encodeURIComponent(mmsi)}`;
        
        // Afficher un indicateur de chargement
        const loadingElement = document.createElement('div');
        loadingElement.className = 'loading-overlay';
        loadingElement.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Chargement...</span></div>';
        document.getElementById('map').appendChild(loadingElement);
        
        try {
            const response = await fetch(API_URL);
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            const responseData = await response.json();
            
            // Vérifier si la réponse contient des données valides
            if (!responseData || !responseData.success) {
                throw new Error(responseData.error || 'Erreur lors de la récupération des données');
            }
            
            // Extraire les points de trajectoire
            const points = responseData.data || [];
            console.log('Points de trajectoire:', points);
            
            if (points.length === 0) {
                throw new Error('Aucun point de trajectoire trouvé pour ce bateau');
            }
            
            // Préparer les coordonnées pour la ligne de trajectoire
            const coordinates = points
                .filter(point => point.Latitude && point.Longitude)
                .map(point => [parseFloat(point.Longitude), parseFloat(point.Latitude)]);
                
            if (coordinates.length < 2) {
                throw new Error('Pas assez de points de géolocalisation valides');
            }
            
            // Calculer les bornes pour le zoom
            const bounds = coordinates.reduce((bounds, coord) => {
                return bounds.extend(coord);
            }, new mapboxgl.LngLatBounds(coordinates[0], coordinates[0]));
            
            // Ajuster la vue pour afficher toute la trajectoire
            map.fitBounds(bounds, {
                padding: 50,
                maxZoom: 12
            });
            
            // Supprimer l'ancienne trajectoire si elle existe
            if (map.getSource('route')) {
                map.removeLayer('route');
                map.removeSource('route');
            }
            
            // Ajouter la nouvelle trajectoire
            map.addSource('route', {
                type: 'geojson',
                data: {
                    type: 'Feature',
                    properties: {},
                    geometry: {
                        type: 'LineString',
                        coordinates: coordinates
                    }
                }
            });
            
            map.addLayer({
                id: 'route',
                type: 'line',
                source: 'route',
                layout: {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                paint: {
                    'line-color': '#3b82f6',
                    'line-width': 3,
                    'line-opacity': 0.8
                }
            });
            
            // Ajouter un marqueur au point de départ
            const startPoint = coordinates[0];
            new mapboxgl.Marker({ color: '#10b981' })
                .setLngLat(startPoint)
                .setPopup(new mapboxgl.Popup({ offset: 25 })
                    .setHTML('<b>Départ</b>'))
                .addTo(map);
                
            // Ajouter un marqueur au point d'arrivée
            const endPoint = coordinates[coordinates.length - 1];
            new mapboxgl.Marker({ color: '#ef4444' })
                .setLngLat(endPoint)
                .setPopup(new mapboxgl.Popup({ offset: 25 })
                    .setHTML('<b>Arrivée</b>'))
                .addTo(map);
            
        } catch (error) {
            console.error('Erreur lors du chargement de la trajectoire:', error);
            alert(`Erreur lors du chargement de la trajectoire: ${error.message}`);
        } finally {
            // Masquer l'indicateur de chargement
            if (loadingElement.parentNode) {
                loadingElement.remove();
            }
        }
    }
    
    // Fonction pour charger les données des bateaux
    async function loadBoatsData() {
        API_URL = '../php/get_ships.php';
        try {
            const response = await fetch(API_URL);
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            const responseData = await response.json();
            console.log('Données reçues du serveur:', responseData);
            
            // Vérifier si la réponse contient des données valides
            if (!responseData || !responseData.success) {
                throw new Error(responseData.error || 'Erreur lors de la récupération des données');
            }
            
            // Extraire le tableau des bateaux de la réponse
            const boatsData = responseData.data || [];
            
            // Vider le tableau avant d'ajouter de nouvelles données
            boatsTableBody.innerHTML = '';
            
            if (!Array.isArray(boatsData) || boatsData.length === 0) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td colspan="6" class="text-center">Aucun bateau trouvé</td>
                `;
                boatsTableBody.appendChild(row);
                return;
            }
            
            // Ajouter chaque bateau au tableau
            boatsData.forEach(ship => {
                const row = document.createElement('tr');
                // Ajouter un gestionnaire de clic pour afficher les détails du bateau
                row.style.cursor = 'pointer';
                row.onclick = () => {
                    // Ici, vous pourriez ajouter une logique pour afficher plus de détails
                    console.log('Bateau sélectionné:', ship);
                    loadTrajet(ship.MMSI);
                };
                
                row.innerHTML = `
                    <td>${ship.MMSI || 'N/A'}</td>
                    <td>${ship.IMO || 'Inconnu'}</td>
                    <td>${ship.VesselName || 'N/A'}</td>
                    <td>${ship.Callsign || 'N/A'}</td>
                    <td>${ship.Length || 'N/A'}</td>
                    <td>${ship.Width || 'N/A'}</td>
                    <td>${ship.TransceiverClass || 'N/A'}</td>  
                `;
                boatsTableBody.appendChild(row);
            });
            
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
    
    
    // Charger les données au chargement de la page
    if (window.location.pathname.includes('visualisation.html')) {
        loadBoatsData();
    }
});
