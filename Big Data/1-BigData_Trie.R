library(dplyr)
library(stringr)# Lecture de la bdd :
df <- read.csv("C:/Users/Gauth/OneDrive/Documents/GitHub/Projet_Outil_de_l-ing-_S6/Big Data/Data/vessel-total-clean.csv",na.strings = c("", "\\N", "NA"))

#On supprime les doublons.
doublons <- duplicated(df[, c("MMSI", "BaseDateTime")])
df_sans_doublons <- df[!doublons, ]


# ===================================== Supprimer toute la ligne si valeur manquante ===================================== 
#  MMSI, LAT, LON, SOG, BaseDateTime
df_sans_val_maquantes <- df_sans_doublons %>% filter((!is.na(MMSI))) %>% filter((!is.na(LAT))) %>% filter((!is.na(LON))) %>% filter((!is.na(BaseDateTime))) 

#  %>% est un equivalent à un select()
# Ces informations sont cruciales. Sans l’une de ces informations, la donnée est inexploitable. On supprime la ligne.

# ===================================== Supprimer toute la ligne si valeur aberrante =====================================
#  Si la vitesse est supérieure à 40 nœuds, on la considère comme aberrante.
df_sans_SOG_Ab <- df_sans_val_maquantes %>% filter(SOG <= 40)

#  Si LON et LAT hors Golf du Mexique
df_coo_golf_Mex <- df_sans_SOG_Ab %>% filter(LAT >= 20 & LAT <= 40) %>% filter(LON >= -110 & LON <= -70) # Revoir avec la carte

# ===================================== Supprimer uniquement la valeur: (la remplacer par NA) ===================================== 
#  COG: la plage de valeur est de 0 à 359,9°. Si la valeur est de 360° ou plus, on la supprime.
#  Heading: la plage de valeur est de 0 à 359. Si la valeur est de 360° ou plus, on la supprime.

df_valeur_NA <- df_coo_golf_Mex %>% mutate(COG = ifelse(COG >= 360, NA, COG)) %>% mutate(Heading = ifelse(Heading >= 360, NA, Heading))

# ===================================== Remplacer si valeur manquante =====================================  
#  Status: Si il n'y a pas de valeur, il faut mettre le bateau en code 15, qui corresponds à Indéfini / inconnu: valeur par défaut si non renseignée

df_fin <- df_valeur_NA %>% mutate(Status = ifelse(is.na(Status),15,Status))


# ===================================== Export final =====================================  
write.csv(df_fin, "C:/Users/Gauth/OneDrive/Documents/GitHub/Projet_Outil_de_l-ing-_S6/Big Data/Data/After_Sort.csv", row.names = FALSE)

# ===================================== Export final sans val manquante length et width =====================================
df_fin_sans_lenght_width_vide <- df_sans_doublons %>% filter((!is.na(Length))) %>% filter((!is.na(Width)))
write.csv(df_fin_sans_lenght_width_vide, "C:/Users/Gauth/OneDrive/Documents/GitHub/Projet_Outil_de_l-ing-_S6/Big Data/Data/After_Sort_sans_l&w_vide.csv", row.names = FALSE)



cat("Lignes initiales :", nrow(df), "\n")
cat("Bateaux initiales :", length(unique(df$MMSI)),"\n")
cat("=== Nettoyage terminé ===\n")
cat("Lignes enlever :", nrow(df)-nrow(df_fin), "\n")
cat("Lignes finales :", nrow(df_fin), "\n")
cat("Bateaux restant :", length(unique(df_fin$MMSI)),"\n")
cat("=== Nettoyage Sans les valeurs nulles de la length et width ===\n")
cat("Lignes enlever :", nrow(df)-nrow(df_fin_sans_lenght_width_vide), "\n")
cat("Lignes finales :", nrow(df_fin_sans_lenght_width_vide), "\n")
cat("Bateaux restant :", length(unique(df_fin_sans_lenght_width_vide$MMSI)),"\n")
