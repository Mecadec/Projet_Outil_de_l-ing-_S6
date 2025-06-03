library(dplyr)
library(stringr)

# Chargement
df <- read.csv("C:/Users/Gauth/OneDrive/Documents/GitHub/Projet_Outil_de_l-ing-_S6/Big Data/Data/vessel-total-clean.csv",
               na.strings = c("", "\\N"))

# 1. Vitesse > 45
removed_speed <- df %>% filter(SOG > 45)
df1 <- df %>% filter(SOG <= 45 | is.na(SOG))

# 2. Doublons
dup_idx <- duplicated(df1[, c("MMSI", "BaseDateTime", "LAT", "LON")])
removed_dups <- df1[dup_idx, ]
df2 <- df1[!dup_idx, ]

# 3. Date manquante
removed_date <- df2 %>% filter(is.na(BaseDateTime))
df3 <- df2 %>% filter(!is.na(BaseDateTime))

# 4. Coordonnées hors limites
removed_coords <- df3 %>% filter(is.na(LAT) | is.na(LON) | LAT < -90 | LAT > 90 | LON < -180 | LON > 180)
df4 <- df3 %>% filter(between(LAT, -90, 90), between(LON, -180, 180))

# 5. Complétion noms
df_clean <- df4 %>%
  group_by(MMSI) %>%
  mutate(VesselName = ifelse(is.na(VesselName) | VesselName == "",
                             first(na.omit(VesselName)), VesselName)) %>%
  ungroup()
# Sauvegarde résultat final
write.csv(df_clean, "C:/Users/Gauth/OneDrive/Documents/GitHub/Projet_Outil_de_l-ing-_S6/Big Data/Data/After_Sort.csv", row.names = FALSE)

# Optionnel : affichage console
cat("=== Nettoyage terminé ===\n")
cat("Lignes initiales :", nrow(df), "\n")
cat("Lignes finales :", nrow(df_clean), "\n")
