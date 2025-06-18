<?php
// Headers CORS et JSON
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-Requested-With');
header('Access-Control-Max-Age: 3600');
header('Content-Type: application/json; charset=utf-8');

// Répondre immédiatement aux requêtes OPTIONS (pré-vol CORS)
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// Configuration de la base de données
$host = 'localhost';
$dbname = 'etu0118';
$user = 'etu0118';
$pass = 'jonnqeuk';


// ------------------------------------------------------------------
// Limite de lignes renvoyées   (GET ?limit=xx   ou valeur par défaut)
// ------------------------------------------------------------------
$limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 20;
if ($limit < 1 || $limit > 1000) {      // borne pour éviter l'abus
    $limit = 20;
}



/**
 * Envoie une réponse JSON standardisée
 */
function sendJsonResponse($success, $data = null, $error = null, $statusCode = 200) {
    http_response_code($statusCode);
    echo json_encode([
        'success' => $success,
        'data' => $data,
        'error' => $error
    ], JSON_UNESCAPED_UNICODE | JSON_NUMERIC_CHECK);
    exit;
}

try {
    // Connexion à la base de données
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $user, $pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false
    ]);

    // Vérifier si la table existe
    $tableExists = $pdo->query("SHOW TABLES LIKE 'Message'")->rowCount() > 0;
    if (!$tableExists) {
        sendJsonResponse(false, null, 'La table Message n\'existe pas', 404);
    }

    // Récupérer les colonnes de la table
    $stmt = $pdo->query("SHOW COLUMNS FROM Message");
    $columns = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    // Définir les colonnes souhaitées (celles qui existent dans la table)
    $desiredColumns = ['ID', 'BaseDateTime', 'LAT', 'LON', 'SOG', 'COG', 'HEADING', 'Status', 'MMSI', 'Draft'];
    $validColumns = array_intersect($desiredColumns, $columns);

    if (empty($validColumns)) {
        sendJsonResponse(false, null, 'Aucune colonne valide trouvée dans la table Message', 500);
    }


    $sql = "SELECT " . implode(',', $validColumns) . "
    FROM Message
    ORDER BY ID DESC
    LIMIT :lim";

$stmt = $pdo->prepare($sql);
$stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
$stmt->execute();
$points = $stmt->fetchAll();


    // Formater les données si nécessaire (par exemple, conversion de types)
    $formattedPoints = array_map(function($point) {
        // Convertir les champs numériques
        $numericFields = ['LAT', 'LON', 'SOG', 'COG', 'HEADING', 'Draft'];
        foreach ($numericFields as $field) {
            if (isset($point[$field])) {
                $point[$field] = (float)$point[$field];
            }
        }
        
        // Convertir les champs entiers
        $intFields = ['ID', 'Status'];
        foreach ($intFields as $field) {
            if (isset($point[$field])) {
                $point[$field] = (int)$point[$field];
            }
        }
        
        return $point;
    }, $points);

    // Envoyer la réponse
    sendJsonResponse(true, $formattedPoints);
    
} catch (PDOException $e) {
    // Journaliser l'erreur (à implémenter avec un système de logs)
    error_log('Erreur PDO dans get_points.php: ' . $e->getMessage());
    
    // Envoyer une réponse d'erreur détaillée en développement, générique en production
    $errorMessage = (strpos($_SERVER['HTTP_HOST'] ?? '', 'localhost') !== false)
        ? 'Erreur de base de données : ' . $e->getMessage()
        : 'Une erreur est survenue lors de la récupération des données';
        
    sendJsonResponse(false, null, $errorMessage, 500);
    
} catch (Exception $e) {
    // Journaliser l'erreur
    error_log('Erreur inattendue dans get_points.php: ' . $e->getMessage());
    
    // Envoyer une réponse d'erreur
    $errorMessage = (strpos($_SERVER['HTTP_HOST'] ?? '', 'localhost') !== false)
        ? 'Erreur serveur : ' . $e->getMessage()
        : 'Une erreur inattendue est survenue';
        
    sendJsonResponse(false, null, $errorMessage, 500);
}




