##############################################################################
# Tirant d'eau moyen – global et par type de navire                          #
##############################################################################

library(dplyr)

# 1. Global : toutes observations valides (> 0 mètre)
draft_global <- ais %>% 
  filter(!is.na(Draft), Draft > 0) %>% 
  summarise(tirant_moyen_m = mean(Draft, na.rm = TRUE))

print(draft_global)
#>   tirant_moyen_m
#> 1          7.842   # <-- exemple

# 2. Détail par type de navire
draft_by_type <- ais %>% 
  filter(!is.na(Draft), Draft > 0) %>% 
  group_by(VesselType) %>% 
  summarise(
    nb_obs   = n(),
    draft_m  = mean(Draft, na.rm = TRUE)
  ) %>% 
  arrange(desc(draft_m))

print(draft_by_type)
