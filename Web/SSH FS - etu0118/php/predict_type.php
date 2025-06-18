<?php
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');

/* ─── 1. lecture + validation payload ─────────────────────── */
$raw = file_get_contents('php://input') ?: '{}';
$data = json_decode($raw, true);

$mmsi = $data['mmsi'] ?? null;
if (!$mmsi) {
  http_response_code(400);
  echo json_encode(['error' => 'MMSI manquant']);
  exit;
}

/* ─── 2. chemins Python + script ──────────────────────────── */
$script = realpath(__DIR__ . '/../vessel_type_predict.py');
$python = '/var/www/etu0118/venv15/bin/python';

if (!$script || !is_file($script)) {
  http_response_code(500);
  echo json_encode(['error' => 'Script Python introuvable']);
  exit;
}

/* ─── 3. exécution sécurisée ──────────────────────────────── */
$cmd = escapeshellcmd($python) . ' ' . escapeshellarg($script) . ' ' . escapeshellarg($mmsi);
exec($cmd . ' 2>&1', $output, $status);

if ($status !== 0) {
  http_response_code(500);
  echo json_encode([
    'error'  => 'Échec Python',
    'detail' => implode("\n", $output)
  ]);
  exit;
}

/* ─── 4. normalisation de la sortie ───────────────────────── */
$json = trim(implode("\n", $output));
$result = json_decode($json, true);

/* Le script Python devrait idéalement produire {"type":"Cargo"}   */
/* Mais s’il renvoie {"vessel_type":"Cargo"} on adapte :          */
$type = $result['type']
     ?? $result['vessel_type']
     ?? $result['predicted_type']
     ?? null;

if (!$type) {                       // aucune clé reconnue
  http_response_code(500);
  echo json_encode(['error' => 'Format JSON inattendu', 'raw' => $result]);
} else {
  echo json_encode(['type' => $type], JSON_UNESCAPED_UNICODE);
}
