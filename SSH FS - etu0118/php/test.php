<?php
// Activer l'affichage des erreurs pour le débogage
ini_set('display_errors', 1);
error_reporting(E_ALL);

// En-têtes CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-Requested-With');
header('Access-Control-Max-Age: 3600');
header('Content-Type: application/json; charset=utf-8');

// Répondre immédiatement aux requêtes OPTIONS (prévol)
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Fonction pour envoyer une réponse JSON
function sendJsonResponse($success, $data = null, $error = null, $statusCode = 200) {
    http_response_code($statusCode);
    echo json_encode([
        'success' => $success,
        'data' => $data,
        'error' => $error
    ]);
    exit;
}

try {
    // Vérifier la méthode HTTP
    $requestMethod = $_SERVER['REQUEST_METHOD'] ?? 'GET';
    
    if ($requestMethod === 'GET') {
        // Réponse de test pour les requêtes GET
        sendJsonResponse(true, [
            'message' => 'Test réussi!',
            'server_time' => date('Y-m-d H:i:s'),
            'php_version' => phpversion(),
            'server_software' => $_SERVER['SERVER_SOFTWARE'] ?? 'Inconnu'
        ]);
    } elseif ($requestMethod === 'POST') {
        // Lire les données POST brutes
        $json = file_get_contents('php://input');
        $data = json_decode($json, true);
        
        // Réponse avec les données reçues
        sendJsonResponse(true, [
            'message' => 'Données reçues avec succès!',
            'received_data' => $data,
            'timestamp' => date('Y-m-d H:i:s')
        ]);
    } else {
        sendJsonResponse(false, null, 'Méthode non autorisée', 405);
    }
} catch (Exception $e) {
    sendJsonResponse(false, null, 'Erreur: ' . $e->getMessage(), 500);
}
?>
