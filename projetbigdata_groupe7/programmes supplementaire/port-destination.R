ports_geo <- tibble::tribble(
  ~port,            ~lat,     ~lon,
  "Houston",        29.7499, -95.3584,
  "Corpus Christi", 27.8128, -97.4072,
  "South Louisiana",30.0500, -90.5000,
  "New Orleans",    29.9445, -90.0618,
  "Tampa Bay",      27.9499, -82.4453,
  "Mobile",         30.7122, -88.0433,
  "Beaumont",       30.0683, -94.0844,
  "Port Arthur",    29.8683, -93.8900,
  "Veracruz",       19.1903, -96.1533,
  "Altamira",       22.3910, -97.9250
)

library(tidyverse)
library(geosphere)        # distHaversine()

# ­── A. associer chaque LON/LAT au port le plus proche  --------------------
ais_port <- ais %>%
  filter(!is.na(LAT), !is.na(LON)) %>%
  rowwise() %>%
  mutate(
    # index du port le plus proche
    port_idx  = which.min(
      distHaversine(
        c(LON, LAT),
        ports_geo[, c("lon", "lat")]
      )
    ),
    dist_km   = distHaversine(
      c(LON, LAT),
      ports_geo[port_idx, c("lon", "lat")]
    ) / 1000,
    port_name = ifelse(dist_km <= 15,
                       ports_geo$port[port_idx],
                       NA_character_)
  ) %>%
  ungroup()

# ­── B. Top N ports (messages à ≤ 15 km) -----------------------------------
topN <- 10
ports <- ais_port %>%
  filter(!is.na(port_name)) %>%
  count(port_name, sort = TRUE) %>%
  slice_head(n = topN)

print(ports)

# ­── C. Bar-plot -----------------------------------------------------------
g_ports <- ggplot(ports,
                  aes(fct_reorder(port_name, n), n)) +
  geom_col(fill = "#6A040F") +
  coord_flip() +
  scale_y_continuous(labels = scales::comma_format(big.mark = " ")) +
  labs(title = paste("Top", topN, "ports (messages ≤ 15 km)"),
       x = "Port", y = "Nombre de messages AIS") +
  theme_minimal()

save_png(g_ports, "08_top_ports_barplot.png")
