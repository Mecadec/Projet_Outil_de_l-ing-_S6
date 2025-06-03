library(shiny)         # Interface web interactive (UI + serveur)
library(tidyverse)     # Manipulation et nettoyage des données (dplyr, readr, tibble...)
library(leaflet)       # Carte interactive (affichage trajectoires)
library(lubridate)     # Gestion et conversion des dates (ymd_hms, difftime)
library(leaflet.extras) # Extensions Leaflet (heatmap)

  
  # shiny -> ui, server, reactive, renderLeaflet, observeEvent
  # tidyverse -> read_csv, mutate, filter, arrange, bind_rows
  # leaflet -> leaflet(), addTiles(), leafletProxy(), addPolylines(), addHeatmap(), addLegend()
  # lubridate -> ymd_hms() pour convertir BaseDateTime, difftime() pour différences temporelles
  # leaflet.extras -> addHeatmap() dans la carte pour routes fréquentées
  

# Chargement et préparation des données
df <- read_csv("C:/Users/Gauth/OneDrive/Documents/GitHub/Projet_Outil_de_l-ing-_S6/Big Data/Data/After_Sort.csv") %>%
  mutate(
    BaseDateTime = suppressWarnings(ymd_hms(BaseDateTime)),  # Conversion date-heure
    VesselName = as.factor(VesselName)                       # Facteur pour les noms de bateaux
  ) %>%
  arrange(VesselName, BaseDateTime)                         # Tri par bateau et date

# UI avec sélection du bateau et option heatmap
ui <- fluidPage(
  titlePanel("Trajectoires bateaux"),
  sidebarLayout(
    sidebarPanel(
      selectInput("bateau", "Choisir un bateau :", choices = unique(df$VesselName), selected = NULL),
      checkboxInput("show_heatmap", "Afficher les routes fréquentées", value = FALSE)
    ),
    mainPanel(
      leafletOutput("map", height = "700px", width = "100%")
    )
  )
)

# Serveur Shiny
server <- function(input, output, session) {
  
  # Carte initiale vide avec tuiles OSM
  output$map <- renderLeaflet({
    leaflet() %>% addTiles()
  })
  
  # Dès qu'un bateau est sélectionné, affichage de sa trajectoire
  observeEvent(input$bateau, {
    req(input$bateau)
    
    # Filtrer données du bateau sélectionné et trier
    df_bateau <- df %>%
      filter(VesselName == input$bateau) %>%
      arrange(BaseDateTime) %>%
      mutate(time_diff = as.numeric(difftime(BaseDateTime, lag(BaseDateTime), units = "hours")))
    
    # Fonction interpolation pour combler les grandes lacunes temporelles (>1h) entre points
    interpolate_points <- function(p1, p2, interval_mins = 15) {
      t_seq <- seq(p1$BaseDateTime, p2$BaseDateTime, by = paste(interval_mins, "mins"))
      t_seq <- t_seq[-c(1, length(t_seq))] # retirer les bornes
      if (length(t_seq) == 0) return(NULL)
      tibble(
        BaseDateTime = t_seq,
        LAT = approx(c(p1$BaseDateTime, p2$BaseDateTime), c(p1$LAT, p2$LAT), xout = t_seq)$y,
        LON = approx(c(p1$BaseDateTime, p2$BaseDateTime), c(p1$LON, p2$LON), xout = t_seq)$y
      )
    }
    
    traj_full <- list()
    for (i in 2:nrow(df_bateau)) {
      prev <- df_bateau[i - 1, ]
      curr <- df_bateau[i, ]
      traj_full <- append(traj_full, list(prev)) # Ajouter point précédent
      if (!is.na(curr$time_diff) && curr$time_diff > 1) { # Si lacune > 1h
        interp <- interpolate_points(prev, curr)
        if (!is.null(interp)) {
          interp$VesselName <- prev$VesselName
          traj_full <- append(traj_full, list(interp)) # Ajouter points interpolés
        }
      }
    }
    
    # Ajouter dernier point et trier la trajectoire complète
    traj_full <- bind_rows(traj_full, df_bateau[nrow(df_bateau), ]) %>%
      arrange(BaseDateTime)
    
    # Mise à jour de la carte avec la trajectoire
    leafletProxy("map") %>%
      clearShapes() %>%
      clearMarkers() %>%
      fitBounds(
        lng1 = min(traj_full$LON, na.rm = TRUE),
        lat1 = min(traj_full$LAT, na.rm = TRUE),
        lng2 = max(traj_full$LON, na.rm = TRUE),
        lat2 = max(traj_full$LAT, na.rm = TRUE)
      ) %>%
      addPolylines(
        data = traj_full,
        lng = ~LON,
        lat = ~LAT,
        color = "black",
        weight = 2,
        dashArray = "5,5",
        opacity = 0.7
      )
  })
  
  # Gestion de l'affichage de la heatmap des routes fréquentées
  observe({
    proxy <- leafletProxy("map")
    proxy %>% clearGroup("heatmap") %>% clearControls()
    
    if (input$show_heatmap) {
      proxy %>%
        addHeatmap(
          data = df,
          lng = ~LON,
          lat = ~LAT,
          radius = 8,
          blur = 15,
          max = 0.05,
          group = "heatmap"
        ) %>%
        addLegend(
          position = "bottomright",
          colors = c("blue", "limegreen", "yellow", "orange", "red"),
          labels = c("Peu fréquenté", "", "", "", "Très fréquenté"),
          title = "Trafic maritime",
          opacity = 0.7
        )
    }
  })
}

shinyApp(ui, server)
