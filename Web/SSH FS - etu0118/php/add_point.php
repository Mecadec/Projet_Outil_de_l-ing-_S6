<?php
/* ============================================================
   CONFIG LOGS
   ============================================================ */
$logDir  = sys_get_temp_dir() . '/etu0118_logs';
$logFile = $logDir . '/point_management.log';

function writeLog(string $msg): void {
    global $logFile;
    $ts = date('Y-m-d H:i:s');
    file_put_contents($logFile, "[$ts] $msg\n", FILE_APPEND | LOCK_EX);
}

/* ------------------------------------------------------------
   BOOTSTRAP
   ------------------------------------------------------------ */
if (!is_dir($logDir) && !mkdir($logDir, 0777, true)) {
    error_log("Impossible de créer $logDir");
}
if (!file_exists($logFile) && !touch($logFile)) {
    error_log("Impossible de créer $logFile");
}
ini_set('log_errors', 1);
ini_set('error_log', $logFile);

/* ------------------------------------------------------------
   HEADERS  &  PRE-FLIGHT
   ------------------------------------------------------------ */
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-Requested-With');
header('Access-Control-Max-Age: 3600');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

/* ------------------------------------------------------------
   PETITE FONCTION RÉPONSE JSON
   ------------------------------------------------------------ */
function respond(bool $ok, $data = null, string $err = null, int $code = 200): void {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');

    $payload = ['success' => $ok];
    if ($data !== null)  $payload['data']  = $data;
    if ($err  !== null)  $payload['error'] = $err;

    echo json_encode($payload);
    writeLog("→ HTTP $code – " . json_encode($payload));
    exit;
}

/* ------------------------------------------------------------
   CONNEXION BD
   ------------------------------------------------------------ */
$dsn  = 'mysql:host=localhost;dbname=etu0118;charset=utf8';
$user = 'etu0118';
$pass = 'jonnqeuk';

try {
    $pdo = new PDO($dsn, $user, $pass, [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES   => false,
    ]);
    writeLog('Connexion MySQL OK');
} catch (PDOException $e) {
    respond(false, null, 'Erreur BD: '.$e->getMessage(), 500);
}

/* ------------------------------------------------------------
   MÉTHODE HTTP
   ------------------------------------------------------------ */
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond(false, null, 'Méthode non autorisée', 405);
}

/* ------------------------------------------------------------
   LECTURE / PARSE JSON
   ------------------------------------------------------------ */
$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (json_last_error() !== JSON_ERROR_NONE) {
    respond(false, null, 'JSON invalide: '.json_last_error_msg(), 400);
}
writeLog('Payload: '.$raw);

/* ------------------------------------------------------------
   NORMALISATION BaseDateTime (HTML datetime-local → MySQL)
   ------------------------------------------------------------ */
   if (!empty($data['BaseDateTime'])) {
    // Cas : 2025-06-17T09:30  →  2025-06-17 09:30:00
    if (preg_match('/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/', $data['BaseDateTime'])) {
        $data['BaseDateTime'] = str_replace('T', ' ', $data['BaseDateTime']) . ':00';
        writeLog('BaseDateTime normalisé à : '.$data['BaseDateTime']);
    }
}



/* ------------------------------------------------------------
   DÉFINITION DES CHAMPS
   ------------------------------------------------------------ */
$required = [
    'BaseDateTime' => 'string',
    'LAT'          => 'numeric',
    'LON'          => 'numeric',
    'SOG'          => 'numeric',
    'COG'          => 'numeric',
    'HEADING'      => 'numeric',
    'Status'       => 'numeric',
    'MMSI'         => 'string',
    'ID'         => 'numeric',
    'Draft'        => 'numeric'
];

/* ------------------------------------------------------------
   VALIDATION
   ------------------------------------------------------------ */
$errors = [];

// présence + typage
foreach ($required as $field => $type) {
    $val = $data[$field] ?? null;
    if ($val === null || (is_string($val) && trim($val) === '')) {
        $errors[] = "Champ $field manquant";
        continue;
    }

    if ($type === 'numeric' && !is_numeric($val)) {
        $errors[] = "$field doit être numérique";
    }
    if ($type === 'string' && !is_string($val)) {
        $errors[] = "$field doit être une chaîne";
    }
}

// quelques règles métier rapides
if (!empty($data['LAT']) && ($data['LAT'] < -90 || $data['LAT'] > 90)) {
    $errors[] = 'LAT hors plage -90/90';
}
if (!empty($data['LON']) && ($data['LON'] < -180 || $data['LON'] > 180)) {
    $errors[] = 'LON hors plage -180/180';
}
if (!empty($data['BaseDateTime'])) {
    $dt = DateTime::createFromFormat('Y-m-d H:i:s', $data['BaseDateTime']);
    if (!$dt) $errors[] = 'BaseDateTime au format YYYY-mm-dd HH:ii:ss requis';
}

if ($errors) {
    respond(false, null, 'Erreurs de validation: '.implode('; ', $errors), 400);
}

/* ------------------------------------------------------------
   MAPPING → TABLE Message
   ------------------------------------------------------------ */
$fieldMap = [
    'BaseDateTime' => 'BaseDateTime',
    'LAT'          => 'LAT',
    'LON'          => 'LON',
    'SOG'          => 'SOG',
    'COG'          => 'COG',
    'HEADING'      => 'HEADING',
    'Status'       => 'Status',
    'MMSI'         => 'MMSI',
    'ID'           => 'ID',
    'Draft'        => 'Draft'
    // ID est laissé NULL → AUTO_INCREMENT si tu l’as défini ainsi
];

$cols = [];
$bind = [];
$params = [];

foreach ($fieldMap as $jsonKey => $col) {
    $cols[]         = $col;
    $bind[]         = ":$jsonKey";
    $params[":$jsonKey"] = $data[$jsonKey];
}

$sql = sprintf(
    'INSERT INTO Message (%s) VALUES (%s)',
    implode(', ', $cols),
    implode(', ', $bind)
);
writeLog("SQL: $sql");

/* ------------------------------------------------------------
   INSERTION
   ------------------------------------------------------------ */
try {
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $id = $pdo->lastInsertId(); // si la table a une AI

    respond(true, ['id' => $id], null, 201);

} catch (PDOException $e) {
    // doublon MMSI+DateTime ?  clé étrangère ?? etc.
    $code = $e->getCode() === '23000' ? 409 : 500;
    respond(false, null, 'Erreur BD: '.$e->getMessage(), $code);
}
?>