library(dplyr)
library(stringr)

# Chargement avec toutes les valeurs manquantes reconnues
df <- read.csv("C:/Users/Gauth/OneDrive/Documents/GitHub/Projet_Outil_de_l-ing-_S6/Big Data/Data/vessel-total-clean.csv",
               na.strings = c("", "\\N", "NA"))

# 1. Vitesse > 45
removed_speed <- df %>% filter(SOG > 45)
df1 <- df %>% filter(SOG <= 45 | is.na(SOG))

# 2. Doublons
dup_idx <- duplicated(df1[, c("MMSI", "BaseDateTime", "LAT", "LON")])
removed_dups <- df1[dup_idx, ]
df2 <- df1[!dup_idx, ]

# 3. Dates manquantes
removed_date <- df2 %>% filter(is.na(BaseDateTime))
df3 <- df2 %>% filter(!is.na(BaseDateTime))

# 4. Coordonnées invalides
removed_coords <- df3 %>% filter(is.na(LAT) | is.na(LON) | LAT < -90 | LAT > 90 | LON < -180 | LON > 180)
df4 <- df3 %>% filter(between(LAT, -90, 90), between(LON, -180, 180))

# 5. Complétion VesselName
df_clean <- df4 %>%
  group_by(MMSI) %>%
  mutate(
    VesselName = ifelse(is.na(VesselName) | VesselName == "", first(na.omit(VesselName)), VesselName)
  ) %>%
  ungroup()

# 6. Remplissage cohérent par groupe
df_filled <- df_clean %>%
  group_by(MMSI) %>%
  mutate(
    CallSign = ifelse(is.na(CallSign) | CallSign == "", first(na.omit(CallSign)), CallSign),
    IMO = ifelse(is.na(IMO), first(na.omit(IMO)), IMO),
    
    Length = ifelse(is.na(Length), as.numeric(names(sort(table(Length), decreasing = TRUE)[1])), Length),
    Width = ifelse(is.na(Width), as.numeric(names(sort(table(Width), decreasing = TRUE)[1])), Width),
    Draft = ifelse(is.na(Draft), as.numeric(names(sort(table(Draft), decreasing = TRUE)[1])), Draft),
    VesselType = ifelse(is.na(VesselType), as.numeric(names(sort(table(VesselType), decreasing = TRUE)[1])), VesselType),
    Cargo = ifelse(is.na(Cargo), as.numeric(names(sort(table(Cargo), decreasing = TRUE)[1])), Cargo),
    
    Status = ifelse(is.na(Status) | Status == "", first(na.omit(Status)), Status),
    Heading = ifelse(is.na(Heading), round(mean(Heading, na.rm = TRUE)), Heading),
    COG = ifelse(is.na(COG), round(mean(COG, na.rm = TRUE), 1), COG),
    SOG = ifelse(is.na(SOG), round(mean(SOG, na.rm = TRUE), 1), SOG)
  ) %>%
  ungroup() %>%
  
  
  # 7. Remplissage global si toujours NA
  mutate(
    CallSign = ifelse(is.na(CallSign) | CallSign == "", "UNKNOWN", CallSign),
    Length = ifelse(is.na(Length), round(mean(Length, na.rm = TRUE)), Length),
    Width = ifelse(is.na(Width), round(mean(Width, na.rm = TRUE)), Width),
    Draft = ifelse(is.na(Draft), round(mean(Draft, na.rm = TRUE), 1), Draft),
    VesselType = ifelse(is.na(VesselType), as.numeric(names(sort(table(VesselType), decreasing = TRUE)[1])), VesselType),
    Cargo = ifelse(is.na(Cargo), as.numeric(names(sort(table(Cargo), decreasing = TRUE)[1])), Cargo),
    Heading = ifelse(is.na(Heading), 511, Heading),
    COG = ifelse(is.na(COG), 0, COG),
    SOG = ifelse(is.na(SOG), 0, SOG)
  )

# 8. Export final
write.csv(df_filled, "C:/Users/Gauth/OneDrive/Documents/GitHub/Projet_Outil_de_l-ing-_S6/Big Data/Data/After_Sort.csv", row.names = FALSE)

# Résumé
cat("=== Nettoyage terminé ===\n")
cat("Lignes initiales :", nrow(df), "\n")
cat("Lignes finales :", nrow(df_filled), "\n")
