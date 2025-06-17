
library(tidyverse)
if (!requireNamespace("caret", quietly = TRUE)) {
  install.packages("caret", repos = "https://cloud.r-project.org")
}
library(caret) # split & évaluation
library(nnet)         # multinomial logistic

set.seed(42)

ais_clf <- ais %>%                            # <-- table nettoyée
  filter(VesselType %in% c(60, 70, 80),       # 3 classes
         !is.na(Length), !is.na(Width), !is.na(Draft),
         !is.na(SOG), SOG >= 0, SOG <= 50) %>%
  mutate(VesselType = factor(VesselType),         # cible catégorielle
         Slenderness = Length / Width,            # feature de forme
         BlockCoeff  = Draft / Length)            # proxy portance

# ─── Split 70 / 30
idx   <- createDataPartition(ais_clf$VesselType, p = .7, list = FALSE)
train <- ais_clf[idx, ]
test  <- ais_clf[-idx, ]

# ─── Modèle multinomial
fit_mn <- nnet::multinom(
  VesselType ~ Length + Width + Draft + SOG + Slenderness + BlockCoeff,
  data = train, trace = FALSE, maxit = 400
)

# ─── Prédiction & métriques
pred  <- predict(fit_mn, newdata = test)
conf  <- caret::confusionMatrix(pred, test$VesselType)

print(conf$table)      # matrice de confusion
print(conf$overall)    # Accuracy, Kappa

# ─── Importance (poids absolus normalisés)
coef_tbl <- broom::tidy(fit_mn) %>% 
  group_by(y.level) %>% 
  mutate(abs_weight = abs(estimate) / max(abs(estimate))) %>% 
  arrange(y.level, -abs_weight)

print(coef_tbl)



tank <- ais %>% 
  filter(VesselType == 80,
         !is.na(SOG), SOG >= 0, SOG <= 50,
         !is.na(Length), !is.na(Draft))

set.seed(42)
idx2 <- createDataPartition(tank$SOG, p = .7, list = FALSE)
train2 <- tank[idx2, ]
test2  <- tank[-idx2, ]

lm_tank <- lm(SOG ~ Length + Draft, data = train2)
pred2   <- predict(lm_tank, newdata = test2)

# ─── RMSE & MAE
rmse <- sqrt(mean((pred2 - test2$SOG)^2))
mae  <- mean(abs(pred2 - test2$SOG))

cat("\n+++ Tanker Speed Model +++\n",
    "RMSE :", round(rmse, 2), "kn\n",
    "MAE  :", round(mae,  2), "kn\n")


ais_msg <- ais %>%
  filter(
    !is.na(VesselType),
    !is.na(Length), !is.na(Width), !is.na(Draft),
    !is.na(SOG),          SOG > 0,  SOG < 50,        # messages « en route »
    !is.na(LAT), !is.na(LON)
  ) %>%
  mutate(
    # recodage méga-classes
    vt_num = as.numeric(as.character(VesselType)),
    VesselType = case_when(
      between(vt_num, 60, 69) ~ "Passenger",
      between(vt_num, 70, 79) ~ "Cargo",
      between(vt_num, 80, 89) ~ "Tanker",
      TRUE                    ~ NA_character_
    ),
    # code Cargo numérique (NA si non numérique)
    Cargo = ifelse(grepl("^[0-9]+$", Cargo), as.integer(Cargo), NA_integer_)
  ) %>%
  drop_na(VesselType, Cargo) %>%     # on ne garde que les lignes complètes
  mutate(VesselType = factor(VesselType))


set.seed(42)
idx <- createDataPartition(ais_msg$VesselType, p = 0.7, list = FALSE)
train <- ais_msg[idx, ]
test  <- ais_msg[-idx, ]


fit_mn <- nnet::multinom(
  VesselType ~ LAT + LON + Cargo,
  data  = train,
  trace = FALSE,
  maxit = 400
)


pred <- predict(fit_mn, newdata = test)
conf <- caret::confusionMatrix(
  factor(pred, levels = levels(test$VesselType)),
  test$VesselType
)

print(conf$table)      # matrice de confusion
print(conf$overall)    # Accuracy, Kappa, etc.

# importance (poids normalisés)
coef_tbl <- broom::tidy(fit_mn) %>%
  group_by(y.level) %>%
  mutate(abs_weight = abs(estimate) / max(abs(estimate))) %>%
  arrange(y.level, -abs_weight)

print(coef_tbl)


set.seed(set.seed(as.numeric(Sys.time()))   # graine = timestamp → presque unique
)

# 1. Pré‐filtre : messages utiles
ais_moving <- ais %>% 
  filter(!is.na(LAT), !is.na(LON),
         !is.na(SOG), SOG > 1) %>%          # >1 kn = en route
  mutate(MMSI = stringr::str_pad(MMSI, 9, pad = "0")) %>% 
  arrange(MMSI, BaseDateTime)

# 2. Construit les paires + calcule Δt et distance
pairs <- ais_moving %>% 
  group_by(MMSI) %>% 
  mutate(
    lat_next = lead(LAT), lon_next = lead(LON),
    t_next   = lead(BaseDateTime),
    dt_min   = as.numeric(difftime(t_next, BaseDateTime, units = "mins")),
    dist_nm  = distHaversine(cbind(LON, LAT),
                             cbind(lon_next, lat_next))/1852
  ) %>% 
  ungroup() %>% 
  filter(!is.na(dt_min), dt_min > 0, dt_min <= 30)   # ≤ 30 min

# 3. MMSI éligibles : au moins 1 paire
eligible <- unique(pairs$MMSI)
n_avail  <- length(eligible)

if (n_avail < 1) { stop("Aucun navire ne possède 2 points à moins de 30 min !") }

sample_ids <- if (n_avail >= 10) sample(eligible, 10) else eligible

# 4. Sélectionne pour chaque MMSI la paire la plus courte
compare_tbl <- pairs %>% 
  filter(MMSI %in% sample_ids) %>% 
  group_by(MMSI) %>% 
  slice_min(dt_min, n = 1, with_ties = FALSE) %>% 
  ungroup() %>% 
  mutate(
    speed_calc = (dist_nm / (dt_min/60)),      # nœuds
    diff_kn    = round(speed_calc - SOG, 2)
  ) %>% 
  transmute(
    MMSI,
    time_start = BaseDateTime,
    time_end   = t_next,
    SOG_reported = round(SOG, 2),
    speed_calc   = round(speed_calc, 2),
    diff_kn
  )

# 5. Sortie
if(nrow(compare_tbl) < 10){
  message("Seulement ", nrow(compare_tbl),
          " navires éligibles (≤30 min) trouvés.")
}
print(compare_tbl)

