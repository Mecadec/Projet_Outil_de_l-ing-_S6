# ─── Installe geosphere si absent ───────────────────────────────────────────
if (!requireNamespace("geosphere", quietly = TRUE)) {
  install.packages("geosphere", repos = "https://cloud.r-project.org")
}
library(geosphere)       # distHaversine disponible
