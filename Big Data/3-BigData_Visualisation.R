library(shiny)         # Interface web
library(tidyverse)     # Manipulation de données
library(leaflet)       # Carte interactive
library(lubridate)     # Gestion des dates
library(leaflet.extras) # Extensions Leaflet (heatmap)

# Chargement des données
df <- read_csv("C:/Users/Gauth/OneDrive/Documents/GitHub/Projet_Outil_de_l-ing-_S6/Big Data/Data/After_Sort.csv") %>%
  mutate(
    BaseDateTime = suppressWarnings(ymd_hms(BaseDateTime)),
    VesselName = as.factor(VesselName)
  ) %>%
  arrange(VesselName, BaseDateTime)

# Interface utilisateur
ui <- fluidPage(
  titlePanel("Trajectoires bateaux"),
  sidebarLayout(
    sidebarPanel(
      selectInput("bateau", "Choisir un bateau :", choices = unique(df$VesselName)),
      checkboxInput("show_heatmap", "Afficher les routes fréquentées", value = FALSE),
      tableOutput("infos_bateau")  # Affichage des infos
    ),
    mainPanel(
      leafletOutput("map", height = "700px", width = "100%")
    )
  )
)

# Serveur
server <- function(input, output, session) {
  
  # Carte initiale vide
  output$map <- renderLeaflet({
    leaflet() %>% addTiles()
  })
  
  # Infos du bateau sélectionné (clé/valeur, types homogènes)
  output$infos_bateau <- renderTable({
    req(input$bateau)
    
    df %>%
      filter(VesselName == input$bateau) %>%
      select(MMSI, IMO, CallSign, VesselType, Length, Width, Draft, Cargo, TransceiverClass) %>%
      distinct() %>%
      mutate(across(everything(), as.character)) %>%
      pivot_longer(everything(), names_to = "Champ", values_to = "Valeur")
  }, striped = TRUE, bordered = TRUE, colnames = FALSE)
  
  # Affichage trajectoire
  observeEvent(input$bateau, {
    req(input$bateau)
    
    df_bateau <- df %>%
      filter(VesselName == input$bateau) %>%
      arrange(BaseDateTime) %>%
      mutate(time_diff = as.numeric(difftime(BaseDateTime, lag(BaseDateTime), units = "hours")))
    
    interpolate_points <- function(p1, p2, interval_mins = 15) {
      t_seq <- seq(p1$BaseDateTime, p2$BaseDateTime, by = paste(interval_mins, "mins"))
      t_seq <- t_seq[-c(1, length(t_seq))]
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
      traj_full <- append(traj_full, list(prev))
      if (!is.na(curr$time_diff) && curr$time_diff > 1) {
        interp <- interpolate_points(prev, curr)
        if (!is.null(interp)) {
          interp$VesselName <- prev$VesselName
          traj_full <- append(traj_full, list(interp))
        }
      }
    }
    
    traj_full <- bind_rows(traj_full, df_bateau[nrow(df_bateau), ]) %>%
      arrange(BaseDateTime)
    
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
  
  # Heatmap
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

# Lancer l'app
shinyApp(ui, server)
