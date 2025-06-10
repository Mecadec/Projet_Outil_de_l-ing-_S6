##############################################################################
#  COMPARAISON VITESSE CALCULÉE vs SOG – 10 NAVIRES, VERSION ROBUSTE         #
##############################################################################
library(tidyverse)
library(geosphere)

set.seed(set.seed(as.numeric(Sys.time()))   # graine = timestamp → presque unique
)

# 1. Pré‐filtre : messages utiles
ais_moving <- ais %>% 
  filter(!is.na(LAT), !is.na(LON),
         !is.na(SOG), SOG > 1) %>%          # >1 kn = en route
  mutate(MMSI = stringr::str_pad(MMSI, 9, pad = "0")) %>% 
  arrange(MMSI, BaseDateTime)

# 2. Construit les paires + calcule Δt et distance
pairs <- ais_moving %>% 
  group_by(MMSI) %>% 
  mutate(
    lat_next = lead(LAT), lon_next = lead(LON),
    t_next   = lead(BaseDateTime),
    dt_min   = as.numeric(difftime(t_next, BaseDateTime, units = "mins")),
    dist_nm  = distHaversine(cbind(LON, LAT),
                             cbind(lon_next, lat_next))/1852
  ) %>% 
  ungroup() %>% 
  filter(!is.na(dt_min), dt_min > 0, dt_min <= 30)   # ≤ 30 min

# 3. MMSI éligibles : au moins 1 paire
eligible <- unique(pairs$MMSI)
n_avail  <- length(eligible)

if (n_avail < 1) { stop("Aucun navire ne possède 2 points à moins de 30 min !") }

sample_ids <- if (n_avail >= 10) sample(eligible, 10) else eligible

# 4. Sélectionne pour chaque MMSI la paire la plus courte
compare_tbl <- pairs %>% 
  filter(MMSI %in% sample_ids) %>% 
  group_by(MMSI) %>% 
  slice_min(dt_min, n = 1, with_ties = FALSE) %>% 
  ungroup() %>% 
  mutate(
    speed_calc = (dist_nm / (dt_min/60)),      # nœuds
    diff_kn    = round(speed_calc - SOG, 2)
  ) %>% 
  transmute(
    MMSI,
    time_start = BaseDateTime,
    time_end   = t_next,
    SOG_reported = round(SOG, 2),
    speed_calc   = round(speed_calc, 2),
    diff_kn
  )

# 5. Sortie
if(nrow(compare_tbl) < 10){
  message("Seulement ", nrow(compare_tbl),
          " navires éligibles (≤30 min) trouvés.")
}
print(compare_tbl)
