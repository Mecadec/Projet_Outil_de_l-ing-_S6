##############################################################################
#   MATRICE DE CORRÉLATION – SEGMENT “CARGO” (codes 70-79)                   #
##############################################################################
library(tidyverse)
library(ggcorrplot)

cargo <- ais %>% 
  filter(between(as.numeric(VesselType), 70, 79)) %>%   # cast temporaire
  select(where(is.numeric)) %>% 
  select(-MMSI, -LAT, -LON)

# 2. Matrice de corrélation (Pearson)
corr_cargo <- cor(cargo, use = "pairwise.complete.obs")

# 3. Visualisation
g_corr_cargo <- ggcorrplot(
  corr_cargo,
  type    = "lower",
  lab     = TRUE,
  tl.cex  = 8,
  lab_size = 3,
  ggtheme = ggplot2::theme_minimal()
) +
  ggtitle("Matrice de corrélation – Navires Cargo (70-79)")

save_png(g_corr_cargo, "15_corr_matrix_cargo.png")
