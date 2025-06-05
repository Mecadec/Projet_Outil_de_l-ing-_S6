library(shiny)
library(tidyverse)
library(leaflet)
library(lubridate)
library(leaflet.extras)
library(geosphere)
library(dbscan)

# Chargement et préparation des données
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
      checkboxInput("show_ports", "Afficher les ports détectés", value = TRUE),
      tableOutput("infos_bateau")
    ),
    mainPanel(
      leafletOutput("map", height = "600px", width = "100%")
    )
  )
)

# Serveur
server <- function(input, output, session) {

  output$map <- renderLeaflet({
    leaflet() %>%
      addTiles() %>%
      setView(lng = mean(df$LON, na.rm = TRUE), lat = mean(df$LAT, na.rm = TRUE), zoom = 6)
  })

  output$infos_bateau <- renderTable({
    req(input$bateau)
    df %>%
      filter(VesselName == input$bateau) %>%
      select(MMSI, IMO, CallSign, VesselType, Length, Width, Draft, Cargo, TransceiverClass) %>%
      distinct() %>%
      mutate(across(everything(), as.character)) %>%
      pivot_longer(everything(), names_to = "Champ", values_to = "Valeur")
  }, striped = TRUE, bordered = TRUE, colnames = FALSE)

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

  observe({
    proxy <- leafletProxy("map")
    proxy %>% clearGroup("ports") %>% clearGroup("flux_ports")

    if (!input$show_ports) return()

    ports_points <- df %>%
      filter(Status == 5) %>%
      select(BaseDateTime, LAT, LON, MMSI, Cargo) %>%
      drop_na(LAT, LON)

    if(nrow(ports_points) == 0) return()

    clusters <- dbscan(ports_points %>% select(LAT, LON), eps = 0.045, minPts = 1)
    ports_points$cluster <- clusters$cluster

    ports_summary <- ports_points %>%
      group_by(cluster) %>%
      summarise(
        lat = mean(LAT),
        lon = mean(LON),
        nb_bateaux = n_distinct(MMSI),
        cargaison_freq = names(sort(table(Cargo), decreasing = TRUE))[1],
        .groups = "drop"
      ) %>%
      mutate(port_name = paste("Port", cluster))

    proxy %>%
      addMarkers(
        data = ports_summary,
        lng = ~lon,
        lat = ~lat,
        group = "ports",
        clusterOptions = markerClusterOptions(),
        label = ~paste0(
          port_name, "<br>",
          "Bateaux passés : ", nb_bateaux, "<br>",
          "Cargaison fréquente : ", cargaison_freq
        ) %>% lapply(htmltools::HTML)
      )

    traj_ports <- ports_points %>%
      arrange(MMSI, BaseDateTime) %>%
      group_by(MMSI) %>%
      mutate(next_cluster = lead(cluster)) %>%
      filter(!is.na(next_cluster) & cluster != next_cluster) %>%
      ungroup() %>%
      count(cluster, next_cluster, sort = TRUE)

    # Garder uniquement le flux sortant le plus fort par port
    traj_ports <- traj_ports %>%
      group_by(cluster) %>%
      slice_max(n, n = 1, with_ties = FALSE) %>%
      ungroup() %>%
      left_join(ports_summary %>% select(cluster, lat1 = lat, lon1 = lon), by = "cluster") %>%
      left_join(ports_summary %>% select(next_cluster = cluster, lat2 = lat, lon2 = lon), by = "next_cluster")
    

    proxy %>%
      addPolylines(
        data = traj_ports,
        lng = ~c(lon1, lon2),
        lat = ~c(lat1, lat2),
        group = "flux_ports",
        color = "blue",
        opacity = 0.3,
        weight = ~pmin(10, n / 5),
      )
    
  })

}

shinyApp(ui, server)
