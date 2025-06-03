##############################################################################
# INSTALL & LOAD – tidyverse + ggcorrplot + vcd pour mosaicplots
##############################################################################
libs <- c("tidyverse", "ggcorrplot", "vcd")
to_install <- libs[!(libs %in% installed.packages()[,"Package"])]
if(length(to_install)) install.packages(to_install, repos = "https://cloud.r-project.org")
lapply(libs, library, character.only = TRUE)

options(scipen = 999)        # adieu notation scientifique
##############################################################################
# CORRELATION MATRIX – Heat-map
##############################################################################
num_vars <- ais %>% 
  select(where(is.numeric)) %>%        # ne garde que numériques
  select(-LAT, -LON)                  # option : retirer coords pures
corr_mat <- cor(num_vars, use = "pairwise.complete.obs")

g_corr <- ggcorrplot::ggcorrplot(
  corr_mat,
  lab   = TRUE,
  type  = "lower",
  tl.cex = 8,
  lab_size = 3
) +
  ggtitle("Matrice de corrélation (numeriques)") +
  theme_minimal()

save_png(g_corr, "11_corr_matrix.png")

g_len_speed <- ais %>% 
  filter(!is.na(Length), !is.na(SOG)) %>% 
  ggplot(aes(Length, SOG)) +
  geom_point(alpha = .3) +
  geom_smooth(method = "lm", se = FALSE, linewidth = .8) +
  labs(title = "Relation Longueur (m) vs Vitesse (kn)",
       x = "Longueur (m)", y = "SOG (kn)") +
  theme_minimal()

save_png(g_len_speed, "12_scatter_length_sog.png")
g_speed_type <- ais %>% 
  filter(!is.na(SOG), !is.na(VesselType), SOG >= 0, SOG <= 50) %>% 
  ggplot(aes(VesselType, SOG)) +
  geom_boxplot(outlier.alpha = .2, fill = "#F48C06") +
  coord_flip() +
  labs(title = "Distribution SOG par type de navire",
       x = "Type", y = "Vitesse (kn)") +
  theme_minimal()

save_png(g_speed_type, "13_boxplot_sog_type.png")


ais_mod <- ais %>%                       # nettoyage minimum
  filter(!is.na(Length), 
         !is.na(SOG),
         SOG >= 0, SOG <= 50,           # borne anti-outliers
         !is.na(VesselType))


# 1. Régression séparée par groupe
model_by_type <- ais_mod %>% 
  group_by(VesselType) %>% 
  nest() %>% 
  mutate(
    lm_fit = map(data, ~ lm(SOG ~ Length, data = .x)),
    coeff  = map(lm_fit, broom::tidy),
    glance = map(lm_fit, broom::glance)
  )

# 2. Tableau des pentes (utile pour PPT)
coeff_table <- model_by_type %>% 
  unnest(coeff) %>% 
  filter(term == "Length") %>% 
  select(VesselType, estimate, std.error, p.value) %>% 
  arrange(desc(abs(estimate)))

print(coeff_table)

g_len_speed_type <- ggplot(ais_mod, aes(Length, SOG)) +
  # 1⟡ nuage en gris discret, très léger
  geom_point(alpha = .15, size = .6, colour = "grey65") +
  # 2⟡ lignes LM épaisses et très colorées
  geom_smooth(aes(colour = VesselType),
              method = "lm",
              se = FALSE,
              linewidth = 1.6,        # épaisseur accentuée
              alpha = 1) +
  # 3⟡ palette contrastée prête pour datashow
  scale_colour_brewer(palette = "Dark2") +  # ou "Set2", "Paired"
  labs(title = "Vitesse ~ Longueur : régression par type de navire",
       x = "Longueur (m)", y = "SOG (kn)",
       colour = "Type") +
  theme_minimal(base_size = 11) +
  theme(legend.position = "right")

save_png(g_len_speed_type, "12b_scatter_length_sog_byType.png")
##############################################################################
#  CROSS-TAB  &  CHI-SQUARE TEST  &  MOSAICPLOT
##############################################################################
tbl_vtype_tx <- ais %>% 
  filter(!is.na(VesselType), !is.na(TransceiverClass)) %>% 
  count(VesselType, TransceiverClass) %>% 
  pivot_wider(names_from = TransceiverClass, values_from = n, values_fill = 0) %>% 
  column_to_rownames("VesselType") %>% 
  as.matrix()

# 3.1 Test d'indépendance χ²
chi_res <- chisq.test(tbl_vtype_tx)
print(chi_res)

if(!dir.exists("figures")) dir.create("figures")   # au cas où

png(file = file.path("figures", "14_mosaic_vtype_tx.png"),
    width = 900, height = 600)

vcd::mosaic(tbl_vtype_tx,
            shade     = TRUE,
            labeling  = vcd::labeling_values,
            legend    = TRUE,
            main      = "Mosaic-plot : VesselType × TransceiverClass")

dev.off()   # ← indispensable pour flusher l’image sur disque

message("+++ RITE III TERMINÉ +++",
        "\nCorr matrix   : 11_corr_matrix.png",
        "\nScatter       : 12_scatter_length_sog.png",
        "\nBoxplot       : 13_boxplot_sog_type.png",
        "\nMosaic & chi² : 14_mosaic_vtype_tx.png")
