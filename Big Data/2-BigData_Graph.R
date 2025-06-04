##############################################################################
#  FONCTIONNALITÉ 2 — VISUALISATION DES DONNÉES SUR DES GRAPHIQUES          #
#             A3 Big-Data – AIS Gulf of Mexico – 2025                       #
##############################################################################

### 0. Librairies (à installer la 1re fois)
needed <- c("tidyverse", "scales")
to_install <- needed[!(needed %in% installed.packages()[,"Package"])]
if(length(to_install)) install.packages(to_install)
lapply(needed, library, character.only = TRUE)

### 1. Import & nettoyage minimal
ais <- read_delim(
  file       = "After_Sort.csv",   # <-- chemin vers votre CSV
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

### 2. GRAPHIQUES DEMANDÉS ################################################################
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


##############################################################################
# 2. AGRÉGATION « UN BATEAU = UNE LIGNE »  -----------------------------------
##############################################################################
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

##############################################################################
# 3. GRAPHIQUES « PAR NAVIRE » ----------------------------------------------
##############################################################################
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

##############################################################################
# 4. RÉCAPITULATIF -----------------------------------------------------------
##############################################################################
message("+++ RITE NAVIS COMPLETÉ +++\n",
        "Graphiques dans   : ", file.path(getwd(), "figures"), "\n",
        "Navires distincts : ", nrow(vessels), "\n",
        "Messages bruts    : ", nrow(ais))


##############################################################################
#  Histogramme – vitesse médiane par navire (messages SOG > 0)               #
##############################################################################

min_msgs <- 1000        # ← change le seuil si tu veux (ex. 30 ou 100)

vessels_speed <- ais %>% 
  filter(!is.na(SOG), SOG > 0) %>%                     # supprime SOG = 0
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

