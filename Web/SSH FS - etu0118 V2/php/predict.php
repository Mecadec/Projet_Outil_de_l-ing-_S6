<?php


header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

try {
    /*──────────────── 1. Lecture du JSON reçu ────────────────*/
    $payload = json_decode(file_get_contents('php://input'), true);
    if (!$payload || empty($payload['mmsi'])) {
        throw new Exception("Champ 'mmsi' manquant dans le body JSON", 400);
    }
    $mmsi = $payload['mmsi'];

    /*──────────────── 2. Récupérer le dernier point BD ───────*/
    $pdo = new PDO("mysql:host=localhost;dbname=etu0118;charset=utf8", "etu0118", "jonnqeuk",
                   [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

    $stmt = $pdo->prepare(
        "SELECT LAT,LON,SOG,COG FROM Message
         WHERE MMSI = :mmsi ORDER BY BaseDateTime DESC LIMIT 1"
    );
    $stmt->execute([':mmsi' => $mmsi]);
    $pt = $stmt->fetch(PDO::FETCH_ASSOC);

    if (!$pt) {
        throw new Exception("Aucun point trouvé pour ce MMSI", 404);
    }

    /*──────────────── 3. Appel du script Python ──────────────*/
    $cmdPayload = [
      'mmsi'    => $mmsi,
      'lat'     => (float)$pt['LAT'],
      'lon'     => (float)$pt['LON'],
      'speed'   => (float)$pt['SOG'],   // <- nouveau nom
      'heading' => (float)$pt['COG']    // <- nouveau nom
    ];
    
    $cmd = escapeshellcmd("/usr/bin/python3 ../predict_cli.py");
    $proc = proc_open($cmd, [
        0 => ['pipe', 'r'],  // stdin
        1 => ['pipe', 'w'],  // stdout
        2 => ['pipe', 'w']   // stderr
    ], $pipes);

    if (!is_resource($proc)) {
        throw new Exception("Impossible d’exécuter le script Python", 500);
    }
    fwrite($pipes[0], json_encode($cmdPayload));
    fclose($pipes[0]);

    $stdout = stream_get_contents($pipes[1]);
    $stderr = stream_get_contents($pipes[2]);
    proc_close($proc);

    if ($stderr) {
        throw new Exception("python failed : " . trim($stderr), 500);
    }

    echo $stdout;            // le JSON que retourne predict_cli.py
    exit;

} catch (Exception $e) {
    http_response_code($e->getCode() ?: 500);
    echo json_encode(['error' => $e->getMessage()]);
    exit;
}
