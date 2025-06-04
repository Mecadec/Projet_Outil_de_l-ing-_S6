##############################################################################
# 0. LIBRAIRIES & OUTIL UTILITAIRE -------------------------------------------
##############################################################################
library(tidyverse)
# petite fonction “mode statistique” (valeur la plus fréquente) -------------
mod_stat <- function(x) {
  ux <- na.omit(unique(x))
  ux[which.max(tabulate(match(x, ux)))]
}
##############################################################################
#   Détection automatique de la colonne "destination / port"                 #
##############################################################################
aliases <- c("Destination", "Port", "Dest", "DestinationPort", "destination",
             "port", "dest")
port_col <- aliases[aliases %in% names(ais)][1]   # premier alias trouvé

##############################################################################
# 1. DATASET PAR NAVIRE (clé = MMSI) -----------------------------------------
ais <- ais1 %>%
  mutate(MMSI = stringr::str_pad(MMSI, 9, pad = "0")) %>%
  group_by(MMSI) %>%
  summarise(
    first_msg_time = min(BaseDateTime, na.rm = TRUE),
    last_msg_time  = max(BaseDateTime, na.rm = TRUE),
    n_messages     = n(),
    
    VesselType       = mod_stat(VesselType),
    TransceiverClass = mod_stat(TransceiverClass),
    
    Length_m       = median(Length,  na.rm = TRUE),
    Width_m        = median(Width,   na.rm = TRUE),
    Draft_m_mean   = mean(Draft,     na.rm = TRUE),
    Draft_m_max = max(Draft, na.rm = TRUE, default = NA_real_),

    
    SOG_kn_mean    = mean(SOG, na.rm = TRUE),
    SOG_kn_median  = median(SOG, na.rm = TRUE),
    SOG_kn_max     = max(SOG, na.rm = TRUE),
    
    COG_sd         = sd(COG, na.rm = TRUE),
    
    # ─── Comptage des destinations uniquement si la colonne existe ───
    n_unique_ports = if (!is.na(port_col))
      n_distinct(.data[[port_col]], na.rm = TRUE)
    else
      NA_integer_
  ) %>%
  ungroup()
