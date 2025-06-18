// utils.js – fonctions génériques, aucune dépendance
export function logDebug(msg, data = null) {
    const ts = new Date().toISOString();
    console.log(`[${ts}] ${msg}`, data ?? "");
  }
  
  /** type = success | error */
  export function showAlert(message, type = "success") {
    document.querySelectorAll(".alert").forEach(a => a.remove());
  
    const div = Object.assign(document.createElement("div"), {
      className: `alert alert-${type}`,
      textContent: message
    });
    const container = document.querySelector(".container") ?? document.body;
    container.prepend(div);
    setTimeout(() => div.remove(), 5_000);
  }
  