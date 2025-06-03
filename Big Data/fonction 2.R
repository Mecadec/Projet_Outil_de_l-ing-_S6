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
  file       = "vessel-total-clean.csv",   # <-- chemin vers votre CSV
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

## 2.1 Répartition des bateaux par type  ----
g_type <- ais |>
  filter(!is.na(VesselType)) |>
  count(VesselType, sort = TRUE) |>
  mutate(VesselType = fct_reorder(VesselType, n)) |>
  ggplot(aes(VesselType, n)) +
  geom_col(fill = "#6A040F") +
  coord_flip() +
  labs(title = "Répartition des bateaux par type",
       x = "Type de bateau", y = "Nombre d’enregistrements") +
  theme_minimal()

save_png(g_type, "01_vessel_type_bar.png")

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
