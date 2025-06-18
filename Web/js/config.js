// Configuration de l'application
const CONFIG = {
    // URL de base de l'API
    API_BASE_URL: 'http://localhost/etu0110', // À modifier selon votre configuration serveur
    
    // Fonction utilitaire pour construire les URLs de l'API
    apiUrl: function(endpoint) {
        return `${this.API_BASE_URL}/${endpoint.replace(/^\/+/, '')}`;
    }
};

// Exporter la configuration pour une utilisation dans d'autres fichiers
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = CONFIG;
}
