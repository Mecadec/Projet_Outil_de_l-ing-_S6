<?php
header('Content-Type: application/json; charset=utf-8');

$payload = file_get_contents('php://input') ?: '{}';
$script  = realpath(__DIR__ . '/../vessel_type_predict.py'); // hors dossier php
$py = '/var/www/etu0118/venv15/bin/python';                         // chemin de python
if (!$script) {
    http_response_code(500);
    echo json_encode(['error'=>'script introuvable']);
    exit;
}

$descs = [
  0 => ['pipe','r'], 1 => ['pipe','w'], 2 => ['pipe','w'],
];
$proc = proc_open("$py $script", $descs, $pipes);
if (!is_resource($proc)) {
    http_response_code(500);
    echo json_encode(['error'=>'proc_open failed']);
    exit;
}

fwrite($pipes[0], $payload); fclose($pipes[0]);
$out = stream_get_contents($pipes[1]); fclose($pipes[1]);
$err = stream_get_contents($pipes[2]); fclose($pipes[2]);
$code = proc_close($proc);

if ($code !== 0) {
    http_response_code(500);
    echo json_encode(['error'=>'python failed','detail'=>$err]);
} else {
    echo $out;   // déjà un JSON {"vessel_type": …}
}
