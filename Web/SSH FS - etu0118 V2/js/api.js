// api.js – tiny wrapper, centralise gestion d’erreurs JSON
import { logDebug } from "./utils.js";

export async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const txt = await res.text();
    try {
      const j = JSON.parse(txt);
      throw new Error(j.error ?? `${res.status} ${res.statusText}`);
    } catch { throw new Error(`${res.status} ${res.statusText}`); }
  }
  return res.json();
}

export async function postJSON(url, body) {
  logDebug(`POST ${url}`, body);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const txt = await res.text();
  let json;
  try { json = JSON.parse(txt); } catch { throw new Error(txt); }

  if (!res.ok || json?.success === false) {
    throw new Error(json?.error ?? `${res.status} ${res.statusText}`);
  }
  return json;
}
