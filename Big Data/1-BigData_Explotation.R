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

length(unique(donnees$VesselType))
str(donnees$VesselType)
table(donnees$VesselType)
freq_sorted <- sort(freq, decreasing = TRUE)

barplot(freq_sorted, 
        main = "Répartition des types de navires (codes AIS)", 
        xlab = "Code VesselType", 
        ylab = "Nombre d'observations", 
        col = "green", 
        las = 2)


# Regrouper les types en catégories
donnees$Categorie <- ifelse(donnees$VesselType >= 60 & donnees$VesselType <= 69, "Passenger",
                     ifelse(donnees$VesselType >= 70 & donnees$VesselType <= 79, "Cargo",
                     ifelse(donnees$VesselType >= 80 & donnees$VesselType <= 89, "Tanker", NA)))

# Créer une table de fréquence par catégorie
freq_cat <- table(categorie)

# Afficher le barplot
barplot(freq_cat,
        main = "Répartition des navires par catégorie (AIS)", 
        xlab = "Catégorie de navire", 
        ylab = "Nombre d'observations", 
        col = c("lightgreen", "khaki", "salmon"))




str(donnees$Length)  # Pour voir le type --> ne fonctionne pas car en char et non en num
donnees$Length <- as.numeric(donnees$Length)
hist(donnees$Length,main = "Distribution de la longueur des bateaux",xlab = "Longueur (en mètres)",
col = "green")
#rien à dire

str(donnees$Width)  # Pour voir le type --> ne fonctionne pas car en chr et non en num
donnees$Width <- as.numeric(donnees$Width)
hist(donnees$Width,main = "Distribution de la largeur des bateaux",xlab = "Largeur (en mètres)",
col = "orange")
#cohérent avec la longeur

str(donnees$Draft)
donnees$Draft <- as.numeric(donnees$Draft)
hist(donnees$Draft,main = "Distribution du tirant d'eau des bateaux",xlab = "Tirant d'eau (en mètres)",
col = "blue", breaks = seq(0, 26, by = 1))
# tirant d'eau de 21m ? --> possible, certains ULCC (Ultra Large Crude Carrier) ont
#                           un tirant d'eau de 20 à 22m

length(unique(donnees$TransceiverClass))

#######################################################################################
####################################### - Tri - #######################################
#######################################################################################

#vitesse
#doublons --> nom et date
#longitude latitude qui ne sont pas dans les normes
#









#######################################################################################
#id,MMSI,BaseDateTime,LAT,LON,SOG,COG,Heading,VesselName,IMO,CallSign
#VesselType,Status,Length,Width,Draft,Cargo,TransceiverClass

#univarié --> longeur-vitesse, etc pour chaque variable numérique
#variables textuelles --> nom du bateau --> nombre de valeurs différentes --> ça veu dire 15000 bateau
#bivarié --> partie régression logistique --> qui dépends de quoi