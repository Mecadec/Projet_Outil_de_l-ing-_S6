##############################################################################
#      DÉTECTION AUTOMATIQUE DU CHAMP « PORT / DESTINATION »                 #
##############################################################################

# vecteur de noms possibles
aliases <- c("Port", "Destination", "Dest", "DestinationPort", "destination", "port")

# lequel existe vraiment ?
port_field <- aliases[aliases %in% names(ais)][1]

if (is.na(port_field)) {
  stop("+++ Aucun champ port/destination trouvé dans vos données ! +++")
}

# ─── Comptage Top N ──────────────────────────────────────────────────────────
topN <- 15        # nombre de ports à afficher

ports <- ais %>% 
  filter(!is.na(.data[[port_field]]), .data[[port_field]] != "") %>% 
  count(!!sym(port_field), name = "visites", sort = TRUE) %>% 
  slice_head(n = topN)

print(ports)

# ─── Bar-plot ────────────────────────────────────────────────────────────────
g_ports <- ggplot(ports, aes(fct_reorder(.data[[port_field]], visites), visites)) +
  geom_col(fill = "#6A040F") +
  coord_flip() +
  scale_y_continuous(labels = scales::comma_format(big.mark = " ")) +
  labs(title = paste("Top", topN, "ports / destinations les plus visités"),
       x = "Port / Destination", y = "Nombre de messages AIS") +
  theme_minimal()

save_png(g_ports, "08_top_ports_barplot.png")
