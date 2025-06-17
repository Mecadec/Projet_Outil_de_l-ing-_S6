<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-Requested-With');
header('Access-Control-Max-Age: 3600');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

$host = 'localhost';
$dbname = 'etu0118';
$user = 'etu0118';
$pass = 'jonnqeuk';

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
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
    ]);

    $stmt = $pdo->query("SHOW COLUMNS FROM bateau");
    $columns = $stmt->fetchAll(PDO::FETCH_COLUMN);
    $desiredColumns = ['MMSI', 'VesselName', 'IMO', 'Callsign', 'Length', 'Width', 'Draft', 'TransceiverClass','MMSI_Message', 'BaseDateTime_Message', 'VesselType', 'Cluster'];

    $validColumns = array_intersect($desiredColumns, $columns);

    if (empty($validColumns)) {
        sendJsonResponse(false, null, "Aucune colonne valide trouvée dans la table bateau", 500);
    }

    $sql = "SELECT " . implode(',', $validColumns) . " FROM bateau ORDER BY VesselName";
    $stmt = $pdo->query($sql);
    $ships = $stmt->fetchAll();

    if ($ships === false) {
        $ships = [];
    }

    sendJsonResponse(true, $ships);
} catch (PDOException $e) {
    sendJsonResponse(false, null, "Erreur base de données: " . $e->getMessage(), 500);
} catch (Exception $e) {
    sendJsonResponse(false, null, "Erreur serveur: " . $e->getMessage(), 500);
}
?>
