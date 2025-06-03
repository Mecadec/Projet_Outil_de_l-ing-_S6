donnees <- read.csv("C:/Users/Paul/Documents/GitHub/Projet_Outil_de_l-ing-_S6/Big Data/Data/vessel-total-clean.csv")

View(donnees)
summary(donnees)

#######################################################################################
############################### - Identification - ####################################
#######################################################################################
#VesselName, MMSI, IMO, CallSign.

table(donnees$VesselName)
#corresponds au nombre d'éléments uniques des vessels name
length(unique(donnees$VesselName))
#--> 150 noms distincts --> 150 bateaux dans la base de données

#idem pour MMSI 
table(donnees$MMSI)
length(unique(donnees$MMSI))
#--> 150 MMSI distincts --> autant de noms de bateaux que de MMSI --> cohérent

table(donnees$IMO)
length(unique(donnees$IMO))
#--> 122 bateaux avec une apellation IMO (n'est pas donnée à tout les bateaux)

length(unique(donnees$CallSign))
table(donnees$CallSign)
#--> 151 Call sign

#→ Le numéro MMSI est le meilleur identifiant pour distinguer les navires, car il est attribué
#  à tous les bateaux et il est unique à chacun.

#######################################################################################
################################## - position - #######################################
#######################################################################################

#longitude et latitude

#######################################################################################
########################### - Données de navigation - #################################
#######################################################################################
#Vitesse - SOG (vitesse sur le fond), COG (cap suivi sur le fond), cap (Heading, la ou pointe le bateau).



#vitesse (SOG - speed over ground)

str(donnees$SOG)  #Pour voir le type
hist(donnees$SOG,main = "Distribution de la vitesse des bateaux", xlab = "Vitesse (SOG) en nœuds",
col = "blue")
#vitesse (SOG - speed over ground) --> On Remarque une valeur abérante



#cap (COG - course over ground)

str(donnees$COG)  #Pour voir le type
table(donnees$COG)
hist(donnees$COG, main = "Distribution du cap des bateaux", 
     xlab = "Cap (COG) en degrés",
     col = "blue",breaks = seq(0, 360, by = 10))  #barre tous les 10 degrés)
#--> la proportion de bateau ayant un cap entre 350 et 360 degrés est curieusement très élevé.



#cap (Heading --> la ou pointe le bateau)

str(donnees$Heading)  #Pour voir le type
table(donnees$Heading)
hist(donnees$Heading, main = "Distribution du cap (heading) des bateaux", 
     xlab = "Cap (Heading) en degrés",
     col = "blue",breaks = seq(0, 600, by = 5))  #barre tous les 10 degrés))
#--> Grosse proportion de bateau ayant un heading incohérent 500+ degré alors que la plage devrait aller
#    de 1 à 360


#######################################################################################
########################### - Données de navigation - #################################
#######################################################################################
#Caractéristiques du navire : Type (vessel type - AIS), longueur, largeur,
#tirant d'eau, type de cargaison (cargo)



#Type (vessel type - AIS)

length(unique(donnees$VesselType))
str(donnees$VesselType)
table(donnees$VesselType)

donnees$categorie <- ifelse(donnees$VesselType >= 60 & donnees$VesselType <= 69, "Passenger",
                     ifelse(donnees$VesselType >= 70 & donnees$VesselType <= 79, "Cargo",
                     ifelse(donnees$VesselType >= 80 & donnees$VesselType <= 89, "Tanker", NA)))

#table de fréquence par catégorie
frequence_cat <- table(categorie)

barplot(freq_cat,
        main = "Répartition des navires par catégorie",
        xlab = "Catégorie de navire",
        ylab = "Nombre d'observations",
        col = c("lightgreen", "khaki", "salmon"),
        ylim = c(0, 200000),
        las = 1)



#longueur

str(donnees$Length)  # Pour voir le type --> ne fonctionne pas car en char et non en num
donnees$Length <- as.numeric(donnees$Length)
hist(donnees$Length,main = "Distribution de la longueur des bateaux",xlab = "Longueur (en mètres)",
col = "green")
#rien à dire



#largeur

str(donnees$Width)  # Pour voir le type --> ne fonctionne pas car en chr et non en num
donnees$Width <- as.numeric(donnees$Width)
hist(donnees$Width,main = "Distribution de la largeur des bateaux",xlab = "Largeur (en mètres)",
col = "orange")
#cohérent avec la longeur



#tirant d'eau

str(donnees$Draft)
donnees$Draft <- as.numeric(donnees$Draft)
hist(donnees$Draft,main = "Distribution du tirant d'eau des bateaux",xlab = "Tirant d'eau (en mètres)",
col = "blue", breaks = seq(0, 26, by = 1))
# tirant d'eau de 21m ? --> possible, certains ULCC (Ultra Large Crude Carrier) ont
#                           un tirant d'eau de 20 à 22m



#type de cargaison

#######################################################################################
########################### - Données de navigation - #################################
#######################################################################################

length(unique(donnees$TransceiverClass))

#######################################################################################
####################################### - Tri - #######################################
#######################################################################################

# Si vitesse > 45 kn on supprime
# Si doublons on supprime
# Si date manquante on supprime
# Si longitude latitude qui ne sont pas dans les normes on supprime ou remet en normes si possible
# Si msi mais pas de nom mettre nom correspondant





# 1. Vitesse > 45
removed_speed <- df %>% filter(SOG > 45)
df1 <- df %>% filter(SOG <= 45 | is.na(SOG))

# 2. Doublons
removed_dups <- df1 %>%
  duplicated(df1[, c("MMSI", "BaseDateTime", "LAT", "LON")]) %>%
  which() %>%
  df1[., ]
df2 <- df1 %>%
  distinct(MMSI, BaseDateTime, LAT, LON, .keep_all = TRUE)

# 3. Date manquante
removed_date <- df2 %>% filter(is.na(BaseDateTime))
df3 <- df2 %>% filter(!is.na(BaseDateTime))

# 4. Coordonnées hors limites
removed_coords <- df3 %>% filter(is.na(LAT) | is.na(LON) | LAT < -90 | LAT > 90 | LON < -180 | LON > 180)
df4 <- df3 %>% filter(between(LAT, -90, 90), between(LON, -180, 180))

# 5. Remplir noms
df_clean <- df4 %>%
  group_by(MMSI) %>%
  mutate(VesselName = ifelse(is.na(VesselName) | VesselName == "",
                             first(na.omit(VesselName)), VesselName)) %>%
  ungroup()

# Export du résultat
write.csv(df_clean, "After_Sort.csv", row.names = FALSE)

# Affichage des lignes supprimées
cat("=== Lignes supprimées pour SOG > 45 ===\n")
print(removed_speed)

cat("\n=== Doublons supprimés ===\n")
print(removed_dups)

cat("\n=== Dates manquantes ===\n")
print(removed_date)

cat("\n=== Coordonnées invalides ===\n")
print(removed_coords)








#######################################################################################
#id,MMSI,BaseDateTime,LAT,LON,SOG,COG,Heading,VesselName,IMO,CallSign
#VesselType,Status,Length,Width,Draft,Cargo,TransceiverClass

#univarié --> longeur-vitesse, etc pour chaque variable numérique
#variables textuelles --> nom du bateau --> nombre de valeurs différentes --> ça veu dire 15000 bateau
#bivarié --> partie régression logistique --> qui dépends de quoi