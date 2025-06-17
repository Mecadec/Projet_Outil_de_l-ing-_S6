<?php

error_log('CWD=' . getcwd());
error_log('__DIR__=' . __DIR__);

header('Content-Type: application/json; charset=utf-8');

$input = file_get_contents('php://input');
if (!$input) { http_response_code(400); exit('{"error":"no input"}'); }

$cmd = escapeshellcmd("../predict_cli.py");
$descriptors = [
  0 => ["pipe","r"],   // stdin
  1 => ["pipe","w"],   // stdout
  2 => ["pipe","w"]    // stderr
];
$proc = proc_open($cmd, $descriptors, $pipes, null, ['PYTHONUTF8'=>'1']);

if (!is_resource($proc)) { http_response_code(500); exit('{"error":"proc"}'); }

fwrite($pipes[0], $input); fclose($pipes[0]);
$result = stream_get_contents($pipes[1]); fclose($pipes[1]);
$err    = stream_get_contents($pipes[2]); fclose($pipes[2]);
$code   = proc_close($proc);

if ($code !== 0) {
    http_response_code(500);
    echo json_encode(["error"=>"python failed","detail"=>$err]);
} else {
    echo $result;          // déjà du JSON prêt pour ton JS
}
