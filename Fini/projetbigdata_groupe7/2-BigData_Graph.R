
### 0. Librairies (à installer la 1re fois)
needed <- c("tidyverse", "scales")
to_install <- needed[!(needed %in% installed.packages()[,"Package"])]
if(length(to_install)) install.packages(to_install)
lapply(needed, library, character.only = TRUE)

### 1. Import & nettoyage minimal
ais <- read_delim(
  file       = "After_Sort_sans_l&w_vide.csv",   # <-- chemin vers votre CSV
  delim      = ",",
  na         = c("\\N", "", "NA"),
  trim_ws    = TRUE,
  show_col_types = FALSE,
  col_types  = cols(
    id              = col_integer(),
    MMSI            = col_double(),
    BaseDateTime    = col_datetime(format = "%Y-%m-%d %H:%M:%S"),
    LAT             = col_double(),
    LON             = col_double(),
    SOG             = col_double(),   # Speed-Over-Ground
    COG             = col_double(),   # Course-Over-Ground
    Heading         = col_double(),
    VesselName      = col_character(),
    IMO             = col_character(),
    CallSign        = col_character(),
    VesselType      = col_character(),
    Status          = col_character(),
    Length          = col_double(),
    Width           = col_double(),
    Draft           = col_double(),
    Cargo           = col_character(),
    TransceiverClass= col_character()
  )
) |>
  distinct()                       # élimine les doublons exacts

# Création d’un dossier « figures » pour les sorties
if(!dir.exists("figures")) dir.create("figures")
save_png <- function(plot, name, w = 8, h = 5){
  ggsave(file.path("figures", name), plot, width = w, height = h, dpi = 300)
}


## 2.1  Répartition des bateaux par méga-type  -------------------------------
g_type <- ais %>% 
  filter(!is.na(VesselType)) %>% 
  mutate(
    # Convertit en numérique puis classe
    v_num  = as.numeric(VesselType),
    MegaType = case_when(
      between(v_num, 60, 69) ~ "Passenger",
      between(v_num, 70, 79) ~ "Cargo",
      between(v_num, 80, 89) ~ "Tanker",
      TRUE                   ~ "Other"          # sécurité, jamais compté ici
    )
  ) %>% 
  filter(MegaType != "Other") %>%              # garde nos 3 catégories
  count(MegaType, sort = TRUE) %>% 
  mutate(MegaType = fct_reorder(MegaType, n)) %>% 
  ggplot(aes(MegaType, n)) +
  geom_col(fill = "#6A040F") +
  coord_flip() +
  labs(title = "Répartition des bateaux par type (3 classes)",
       x = "Méga-type", y = "Nombre de navires") +
  theme_minimal()

save_png(g_type, "01_vessel_megatype_bar.png")


## 2.2 Histogramme des vitesses (SOG) ----
g_sog <- ggplot(ais, aes(SOG)) +
  geom_histogram(bins = 60, fill = "#E85D04") +
  labs(title = "Distribution de la vitesse (SOG)",
       x = "Vitesse (nœuds)", y = "Effectif") +
  theme_minimal()

save_png(g_sog, "02_hist_sog.png")

## 2.3 Histogramme du tirant d’eau (Draft) ----
g_draft <- ais |>
  filter(!is.na(Draft) & Draft > 0) |>
  ggplot(aes(Draft)) +
  geom_histogram(bins = 40, fill = "#FFBA08") +
  labs(title = "Distribution du tirant d’eau",
       x = "Tirant d’eau (m)", y = "Effectif") +
  theme_minimal()

save_png(g_draft, "03_hist_draft.png")

## 2.4 Répartition des classes de transpondeur ----
g_tx <- ais |>
  filter(!is.na(TransceiverClass)) |>
  count(TransceiverClass) |>
  mutate(TransceiverClass = fct_reorder(TransceiverClass, n)) |>
  ggplot(aes(TransceiverClass, n)) +
  geom_col(fill = "#9D0208") +
  labs(title = "Classes de transpondeur AIS",
       x = "Classe", y = "Nombre d’enregistrements") +
  theme_minimal()

save_png(g_tx, "04_transceiver_class_bar.png")

### 3. Récapitulatif console
message("+++ RITE TERMINÉ +++\n",
        "Graphiques écrits dans :  ", file.path(getwd(), "figures"), "\n",
        "Total d’enregistrements : ", nrow(ais))


mod_stat <- function(x) {        # mode statistique
  ux <- na.omit(unique(x))
  ux[which.max(tabulate(match(x, ux)))]
}

vessels <- ais %>% 
  mutate(MMSI = stringr::str_pad(MMSI, 9, pad = "0")) %>% 
  group_by(MMSI) %>% 
  summarise(
    VesselType       = mod_stat(VesselType),
    TransceiverClass = mod_stat(TransceiverClass),
    Length           = median(Length, na.rm = TRUE),
    Width            = median(Width , na.rm = TRUE),
    Draft            = median(Draft, na.rm = TRUE),
    SOG_median       = median(SOG  , na.rm = TRUE),
    .groups = "drop"
  )

## 3.1  Répartition des navires par méga-type  -------------------------------
g_type <- vessels %>% 
  filter(!is.na(VesselType)) %>% 
  mutate(
    v_num    = as.numeric(as.character(VesselType)),   # cast sûr
    MegaType = case_when(
      between(v_num, 60, 69) ~ "Passenger",
      between(v_num, 70, 79) ~ "Cargo",
      between(v_num, 80, 89) ~ "Tanker",
      TRUE                   ~ NA_character_           # ignore le reste
    )
  ) %>% 
  drop_na(MegaType) %>% 
  count(MegaType, sort = TRUE) %>% 
  mutate(MegaType = fct_reorder(MegaType, n)) %>% 
  ggplot(aes(MegaType, n)) +
  geom_col(fill = "#6A040F") +
  coord_flip() +
  labs(title = "Nombre de navires par type (Passenger / Cargo / Tanker)",
       x = "Méga-type", y = "Nombre de navires") +
  theme_minimal()

save_png(g_type, "01b_vessel_megatype_bar.png")

## 3.2 Histogramme de la VITESSE médiane par navire
g_sog <- vessels %>% 
  filter(!is.na(SOG_median), SOG_median >= 0) %>% 
  ggplot(aes(SOG_median)) +
  geom_histogram(bins = 40, fill = "#E85D04") +
  labs(title = "Distribution de la vitesse médiane par navire",
       x = "Vitesse médiane (nœuds)", y = "Nombre de navires") +
  theme_minimal()

save_png(g_sog, "02b_hist_sog_vessel.png")

## 3.3 Histogramme du TIRANT d’EAU (Draft) médian par navire
g_draft <- vessels %>% 
  filter(!is.na(Draft) & Draft > 0) %>% 
  ggplot(aes(Draft)) +
  geom_histogram(bins = 30, fill = "#FFBA08") +
  labs(title = "Distribution du tirant d’eau médian par navire",
       x = "Tirant d’eau (m)", y = "Nombre de navires") +
  theme_minimal()

save_png(g_draft, "03b_hist_draft_vessel.png")

## 3.4 Répartition des classes de transpondeur (par navire)
g_tx <- vessels %>% 
  filter(!is.na(TransceiverClass)) %>% 
  count(TransceiverClass, sort = TRUE) %>% 
  mutate(TransceiverClass = fct_reorder(TransceiverClass, n)) %>% 
  ggplot(aes(TransceiverClass, n)) +
  geom_col(fill = "#9D0208") +
  labs(title = "Classe de transpondeur – comptage par navire",
       x = "Classe", y = "Nombre de navires") +
  theme_minimal()

save_png(g_tx, "04b_transceiver_class_bar.png")


message("+++ FIN +++\n",
        "Graphiques dans   : ", file.path(getwd(), "figures"), "\n",
        "Navires distincts : ", nrow(vessels), "\n",
        "Messages bruts    : ", nrow(ais))


min_msgs <- 1000        # ← change le seuil si tu veux (ex. 30 ou 100)

vessels_speed <- ais %>% 
  filter(!is.na(SOG), SOG > 1, SOG < 50) %>%                     # supprime SOG = 0
  mutate(MMSI = stringr::str_pad(MMSI, 9, pad = "0")) %>% 
  group_by(MMSI) %>% 
  summarise(
    n_messages = n(),
    sog_median = median(SOG),                          # vitesse médiane
    .groups = "drop"
  )                      # garde les navires
# assez observés

g_hist_med <- ggplot(vessels_speed, aes(sog_median)) +
  geom_histogram(bins = 40, fill = "#E85D04") +
  labs(title = paste0("Vitesse médiane par navire "),
       x = "Vitesse médiane (nœuds)", y = "Nombre de navires") +
  theme_minimal()

save_png(g_hist_med, "05b_hist_speed_median_vessel.png")

# - liste de ports
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