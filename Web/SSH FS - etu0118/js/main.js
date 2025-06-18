// main.js – point d’entrée
import { initShips }  from "./ships.js";
import { initPoints } from "./points.js";

document.addEventListener("DOMContentLoaded", () => {
  initShips();
  initPoints();
});
