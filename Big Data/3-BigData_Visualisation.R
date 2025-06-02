#Gauthier
#Exploitation des données afin de créé une carte de trajectoire

# Charger les packages nécessaires
library(tidyverse)
library(leaflet)
library(lubridate)

# Charger les données CSV
df <- read_csv("20250602\vessel-total-clean.csv")  # Remplace par le chemin réel

# S'assurer que les colonnes sont bien au bon format
df <- df %>%
  mutate(
    BaseDateTime = ymd_hms(BaseDateTime),
    VesselName = as.factor(VesselName)
  )

# --- 1. Afficher TOUTES les trajectoires ---

# Créer une carte leaflet avec les trajectoires
leaflet(data = df) %>%
  addTiles() %>%
  addPolylines(
    lng = ~LON,
    lat = ~LAT,
    group = ~VesselName,
    color = "blue",
    weight = 2,
    popup = ~paste("Bateau:", VesselName)
  )

# --- 2. Afficher la trajectoire d'un seul bateau (ex: "STOLT LOTUS") ---

bateau <- "STOLT LOTUS"

df_bateau <- df %>%
  filter(VesselName == bateau) %>%
  arrange(BaseDateTime)

leaflet(data = df_bateau) %>%
  addTiles() %>%
  addPolylines(
    lng = ~LON,
    lat = ~LAT,
    color = "red",
    weight = 3,
    popup = ~paste("Heure:", BaseDateTime)
  ) %>%
  addMarkers(
    lng = ~LON,
    lat = ~LAT,
    popup = ~paste("Heure:", BaseDateTime)
  )

# --- 3. Routes principales (bonus simple) ---

# On peut faire un group_by sur les coordonnées arrondies pour voir les zones les plus traversées
df %>%
  mutate(LAT_r = round(LAT, 1), LON_r = round(LON, 1)) %>%
  count(LAT_r, LON_r, sort = TRUE) %>%
  top_n(20) %>%
  leaflet() %>%
  addTiles() %>%
  addCircles(
    lng = ~LON_r,
    lat = ~LAT_r,
    weight = 2,
    radius = ~n * 100,
    popup = ~paste("Nombre de passages:", n),
    color = "darkgreen"
  )
