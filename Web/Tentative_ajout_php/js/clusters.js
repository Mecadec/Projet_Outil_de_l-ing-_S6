document.addEventListener('DOMContentLoaded', function() {
    // Initialisation de la carte Mapbox
    mapboxgl.accessToken = 'pk.eyJ1IjoibWVjYWRlYyIsImEiOiJjbWMwa3E3enEwMTY4MmtwajlybTI0cHBvIn0.ViQ5X-5mq08GAYbszceg8A';
    
    // Création de la carte centrée sur le golfe du Mexique
    const map = new mapboxgl.Map({
        container: 'clusters-map',
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [-90.0, 25.0], // Coordonnées du golfe du Mexique
        zoom: 3 // Niveau de zoom pour voir toute la zone
    });
    
    // Ajout des contrôles de navigation
    map.addControl(new mapboxgl.NavigationControl());
    
    // Fonction pour charger les clusters
    async function loadClusters() {
        // Afficher un indicateur de chargement
        const loadingElement = document.createElement('div');
        loadingElement.className = 'loading-overlay';
        loadingElement.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Chargement...</span></div>';
        document.getElementById('clusters-map').appendChild(loadingElement);
        
        try {
            // Ici, vous devrez remplacer cette URL par votre endpoint API pour les clusters
            const API_URL = '../php/get_clusters.php';
            const response = await fetch(API_URL);
            
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            
            const clustersData = await response.json();
            
            // Vérifier si la réponse contient des données valides
            if (!clustersData || !clustersData.success) {
                throw new Error(clustersData.error || 'Erreur lors de la récupération des clusters');
            }
            
            // Ici, vous devrez traiter les données des clusters et les afficher sur la carte
            console.log('Données des clusters:', clustersData);
            
            // Exemple d'ajout d'un marqueur (à adapter selon votre structure de données)
            if (clustersData.data && clustersData.data.length > 0) {
                clustersData.data.forEach(cluster => {
                    new mapboxgl.Marker({
                        color: `#${Math.floor(Math.random()*16777215).toString(16)}`
                    })
                    .setLngLat([cluster.longitude, cluster.latitude])
                    .setPopup(new mapboxgl.Popup({ offset: 25 })
                        .setHTML(`<b>Cluster #${cluster.id}</b><br>${cluster.count} bateaux`))
                    .addTo(map);
                });
                
                // Ajuster la vue pour afficher tous les clusters
                if (clustersData.data.length > 1) {
                    const bounds = clustersData.data.reduce((bounds, cluster) => {
                        return bounds.extend([cluster.longitude, cluster.latitude]);
                    }, new mapboxgl.LngLatBounds(
                        [clustersData.data[0].longitude, clustersData.data[0].latitude],
                        [clustersData.data[0].longitude, clustersData.data[0].latitude]
                    ));
                    
                    map.fitBounds(bounds, {
                        padding: 50,
                        maxZoom: 12
                    });
                }
            }
            
        } catch (error) {
            console.error('Erreur lors du chargement des clusters:', error);
            alert(`Erreur lors du chargement des clusters: ${error.message}`);
        } finally {
            // Masquer l'indicateur de chargement
            if (loadingElement.parentNode) {
                loadingElement.remove();
            }
        }
    }
    
    // Gestionnaire d'événement pour le bouton de génération des clusters
    document.getElementById('run-clustering').addEventListener('click', loadClusters);
    
    // Charger les clusters au chargement de la page
    // loadClusters(); // Décommentez cette ligne si vous voulez charger les clusters automatiquement
});
