<?php
// Configuration des logs - Utiliser le répertoire temporaire système
$logDir = sys_get_temp_dir() . '/etu0118_logs';
$logFile = $logDir . '/ship_management.log';

// Fonction pour écrire dans le log
function writeLog($message) {
    global $logFile;
    $timestamp = date('Y-m-d H:i:s');
    $logMessage = "[$timestamp] $message" . PHP_EOL;
    
    // Écrire directement dans le fichier
    if (is_writable($logFile)) {
        file_put_contents($logFile, $logMessage, FILE_APPEND);
    } else {
        // Si l'écriture échoue, utiliser error_log qui écrira dans les logs système
        error_log("Impossible d'écrire dans le fichier de log ($logFile). Message: $message");
    }
}

// Démarrer la journalisation
writeLog('=== Démarrage du script add_ship.php ===');
writeLog('Répertoire temporaire système: ' . sys_get_temp_dir());

// Créer le répertoire de logs s'il n'existe pas
if (!file_exists($logDir)) {
    if (!mkdir($logDir, 0777, true)) {
        error_log("Impossible de créer le répertoire de logs: $logDir");
    } else {
        writeLog("Répertoire de logs créé: $logDir");
    }
}

// Créer le fichier de log s'il n'existe pas
if (!file_exists($logFile)) {
    if (!touch($logFile)) {
        error_log("Impossible de créer le fichier de log: $logFile");
    } else {
        chmod($logFile, 0666); // Donner les permissions en écriture à tous
        writeLog("Fichier de log créé: $logFile");
    }
}

// Configurer la gestion des erreurs
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', $logFile);

// En-têtes CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');

header('Access-Control-Allow-Headers: Content-Type, X-Requested-With');
header('Access-Control-Max-Age: 3600');

// Répondre immédiatement aux requêtes OPTIONS (prévol)
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Configuration de la base de données
$host = 'localhost';
$dbname = 'etu0118';
$user = 'etu0118';
$pass = 'jonnqeuk';

writeLog('Configuration BD: ' . json_encode([
    'host' => $host,
    'dbname' => $dbname,
    'user' => $user,
    'pass' => $pass // Ne pas logger le mot de passe
]));

function sendJsonResponse($success, $data = null, $error = null, $statusCode = 200) {
    writeLog('Début de la fonction sendJsonResponse');
    http_response_code($statusCode);
    $response = [
        'success' => $success,
    ];
    
    if ($data !== null) {
        $response['data'] = $data;
    }
    
    if ($error !== null) {
        $response['error'] = $error;
    }
    
    $jsonResponse = json_encode($response);
    writeLog("Envoi de la réponse JSON: " . $jsonResponse);
    header('Content-Type: application/json; charset=utf-8');
    echo $jsonResponse;
    writeLog('Fin de la fonction sendJsonResponse');
    exit;
}

try {
    writeLog('Tentative de connexion à la base de données...');
    
    // Connexion à la base de données
    $dsn = "mysql:host=$host;dbname=$dbname;charset=utf8";
    $options = [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ];
    
    $pdo = new PDO($dsn, $user, $pass, $options);
    writeLog('Connexion à la base de données réussie');
    
    $requestMethod = $_SERVER['REQUEST_METHOD'] ?? 'INCONNUE';
    writeLog('Méthode de requête: ' . $requestMethod);
    
    if ($requestMethod !== 'POST') {          // OPTIONS déjà géré plus haut
        $errorMsg = 'Méthode non autorisée: ' . $requestMethod;
        writeLog($errorMsg);
        sendJsonResponse(false, null, $errorMsg, 405);
    }

    // Récupération des données POST
    $json = file_get_contents('php://input');
    writeLog('Données brutes reçues: ' . substr($json, 0, 500)); // Limité à 500 caractères
    
    $data = json_decode($json, true);
    $jsonError = json_last_error();
    
    // Vérification du JSON
    if ($jsonError !== JSON_ERROR_NONE) {
        $errorMsg = 'JSON invalide: ' . json_last_error_msg() . ' (code: ' . $jsonError . ')';
        writeLog($errorMsg);
        writeLog('Contenu reçu: ' . $json);
        sendJsonResponse(false, null, $errorMsg, 400);
    }
    
    writeLog('Données JSON décodées: ' . json_encode($data));

    // Vérification des champs obligatoires
    $requiredFields = ['MMSI', 'VesselName', 'IMO', 'Callsign', 'Length', 'Width', 'TransceiverClass'];
    $missingFields = [];
    
    writeLog('Vérification des champs obligatoires...');
    
    foreach ($requiredFields as $field) {
        $value = $data[$field] ?? null;
        $isMissing = false;
        
        if ($value === null) {
            $isMissing = true;
            $reason = 'non défini';
        } elseif (is_string($value) && trim($value) === '') {
            $isMissing = true;
            $reason = 'chaîne vide';
        }
        
        if ($isMissing) {
            writeLog(sprintf('Champ manquant: %s (%s)', $field, $reason));
            $missingFields[] = $field;
        } else {
            writeLog(sprintf('Champ présent: %s = %s', $field, 
                is_scalar($value) ? $value : gettype($value)));
        }
    }
    
    if (!empty($missingFields)) {
        $errorMsg = 'Champs manquants: ' . implode(', ', $missingFields);
        writeLog($errorMsg);
        sendJsonResponse(false, null, $errorMsg, 400);
    }

    // Validation des types de données
    $errors = [];
    
    if (!is_numeric($data['Length']) || $data['Length'] <= 0) {
        $errors[] = 'La longueur doit être un nombre positif';
    }
    
    if (!is_numeric($data['Width']) || $data['Width'] <= 0) {
        $errors[] = 'La largeur doit être un nombre positif';
    }

    
    if (!in_array($data['TransceiverClass'], ['A', 'B'])) {
        $errors[] = 'La classe d\'émetteur doit être A ou B';
    }
    
    if (!empty($errors)) {
        sendJsonResponse(false, null, 'Erreurs de validation: ' . implode('; ', $errors), 400);
    }

    
    // Préparer les colonnes et les valeurs pour l'insertion
    writeLog('Préparation des données pour l\'insertion...');


    // Mapper les données aux colonnes de la table
    $fieldMapping = [
        'MMSI' => 'MMSI',
        'VesselName' => 'VesselName',
        'IMO' => 'IMO',
        'Callsign' => 'Callsign',
        'Length' => 'Length',
        'Width' => 'Width',
        'TransceiverClass' => 'TransceiverClass'
    ];

    $columnsToInsert = [];
$placeholders    = [];
$values          = [];

foreach ($fieldMapping as $field => $column) {
    if (isset($data[$field])) {
        $columnsToInsert[] = $column;
        $placeholders[]    = ":$field";
        $values[":$field"] = $data[$field];
        writeLog(sprintf('  %s = %s', $field,
            is_scalar($data[$field]) ? $data[$field] : gettype($data[$field])));
    }
}


    
    if (empty($columnsToInsert)) {
        $errorMsg = 'Aucune colonne valide trouvée pour l\'insertion';
        writeLog($errorMsg);
        sendJsonResponse(false, null, $errorMsg, 400);
    }
    
    writeLog('Colonnes à insérer: ' . implode(', ', $columnsToInsert));
    writeLog('Paramètres: ' . json_encode($values));

    // Construire la requête d'insertion
    $query = sprintf(
        "INSERT INTO bateau (%s) VALUES (%s)",
        implode(', ', $columnsToInsert),
        implode(', ', $placeholders)
    );
    
    writeLog('Requête SQL préparée: ' . $query);
    
    try {
        // Préparer et exécuter la requête
        writeLog('Préparation de la requête...');
        $stmt = $pdo->prepare($query);
        
        writeLog('Exécution de la requête avec les paramètres: ' . json_encode($values));
        $startTime = microtime(true);
        $result = $stmt->execute($values);
        $executionTime = round((microtime(true) - $startTime) * 1000, 2);
        
        writeLog(sprintf('Requête exécutée en %s ms', $executionTime));
        
        if ($result === false) {
            $errorInfo = $stmt->errorInfo();
            $errorMsg = sprintf('Erreur d\'exécution: %s (code: %s)', $errorInfo[2] ?? 'Inconnue', $errorInfo[1] ?? '0');
            writeLog($errorMsg);
            throw new Exception($errorMsg);
        }
        
        // Récupérer le MMSI du navire inséré (clé primaire)
        $mmsi = $data['MMSI'];
        writeLog("Nouveau navire inséré avec le MMSI: $mmsi");
        
        // Récupérer les données complètes du navire
        $query = "SELECT * FROM bateau WHERE MMSI = ?";
        writeLog("Récupération des données du navire avec la requête: $query");
        
        $stmt = $pdo->prepare($query);
        $stmt->execute([$mmsi]);
        $ship = $stmt->fetch();
        
        if ($ship === false) {
            writeLog("Avertissement: Impossible de récupérer les données du navire après l'insertion");
            // Renvoyer quand même une réponse de succès avec le MMSI
            sendJsonResponse(true, ['MMSI' => $mmsi], 'Navire créé avec succès', 201);
        } else {
            writeLog('Données du navire récupérées avec succès');
            sendJsonResponse(true, $ship, null, 201);
        }
        
    } catch (PDOException $e) {
        $errorMsg = 'Erreur PDO lors de l\'exécution de la requête: ' . $e->getMessage();
        writeLog($errorMsg);
        writeLog('Code erreur: ' . $e->getCode());
        writeLog('Stack trace: ' . $e->getTraceAsString());
        
        // Vérifier si c'est une erreur de contrainte d'unicité
        if ($e->getCode() == '23000' || strpos($e->getMessage(), 'Duplicate entry') !== false) {
            $errorMsg = 'Un navire avec ce MMSI existe déjà';
            writeLog($errorMsg);
            sendJsonResponse(false, null, $errorMsg, 409);
        }
        
        throw $e; // Relancer pour être attrapé par le bloc catch principal
        throw new Exception('Échec de l\'insertion dans la base de données');
    }

} catch(PDOException $e) {
    // Gestion des erreurs de base de données
    $errorCode = $e->getCode();
    $errorMessage = $e->getMessage();
    
    // Journaliser l'erreur complète
    writeLog('Erreur PDO: ' . $errorMessage);
    writeLog('Code erreur: ' . $errorCode);
    writeLog('Stack trace: ' . $e->getTraceAsString());
    
    // Gestion des erreurs de contrainte d'unicité
    if ($errorCode == 23000 || strpos($errorMessage, 'Duplicate entry') !== false) {
        $errorMsg = 'Un navire avec ce MMSI existe déjà';
        writeLog($errorMsg);
        sendJsonResponse(false, null, $errorMsg, 409);
    }
    
    // Autres erreurs PDO
    $errorDetails = 'Une erreur est survenue lors de l\'accès à la base de données';
    // En développement, afficher plus de détails
    if (strpos($_SERVER['HTTP_HOST'] ?? '', 'localhost') !== false) {
        $errorDetails = $e->getMessage();
    }
    
    writeLog('Erreur PDO: ' . $errorDetails);
    sendJsonResponse(false, null, $errorDetails, 500);
    
} catch(Exception $e) {
    // Autres exceptions
    $errorMessage = $e->getMessage();
    writeLog('Erreur inattendue: ' . $errorMessage);
    writeLog('Stack trace: ' . $e->getTraceAsString());
    
    $errorDetails = 'Une erreur inattendue est survenue';
    if (strpos($_SERVER['HTTP_HOST'] ?? '', 'localhost') !== false) {
        $errorDetails = $errorMessage;
    }
    
    writeLog('Erreur inattendue: ' . $errorDetails);
    sendJsonResponse(false, null, $errorDetails, 400);
}

writeLog('=== Fin du script add_ship.php ===');
?>
