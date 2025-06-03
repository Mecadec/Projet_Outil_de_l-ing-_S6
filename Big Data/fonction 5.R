##############################################################################
# 1. DATASET D’APPRENTISSAGE : filtrage, features numériquées                #
##############################################################################
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

#Split 70 / 30
idx   <- createDataPartition(ais_clf$VesselType, p = .7, list = FALSE)
train <- ais_clf[idx, ]
test  <- ais_clf[-idx, ]

#Modèle multinomial
fit_mn <- nnet::multinom(
  VesselType ~ Length + Width + Draft + SOG + Slenderness + BlockCoeff,
  data = train, trace = FALSE, maxit = 400
)

#Prédiction & métriques
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


##############################################################################
# 2. RÉGRESSION SOG CHEZ LES TANKERS (code 80)                               #
##############################################################################
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


if (!requireNamespace("rsample", quietly = TRUE)) {
  install.packages("rsample", repos = "https://cloud.r-project.org")
}
library(rsample)

# ─── Installation automatique si besoin ─────────────────────────────────────
if (!requireNamespace("randomForest", quietly = TRUE)) {
  install.packages("randomForest", repos = "https://cloud.r-project.org")
}
library(randomForest)

library(tidyverse)
if (!requireNamespace("yardstick", quietly = TRUE)) {
  install.packages("yardstick", repos = "https://cloud.r-project.org")
}
library(yardstick)     # métriques

# ─── 0. Jeu des tankers + features enrichies
tank <- ais %>% 
  filter(VesselType == 80,
         between(SOG, 0, 25),        # supprime extrêmes
         !is.na(Length), !is.na(Draft), !is.na(Width)) %>% 
  mutate(
    MMSI  = stringr::str_pad(MMSI, 9, pad = "0"),
    Density  = Draft / Width,
    Slender  = Length / Width
  )

# ─── 1. Validation croisée GROUPÉE (MMSI) – 5 plis × 3 répét.
set.seed(42)
cv <- group_vfold_cv(
  data  = tank,
  group = MMSI,
  v     = 5,
  repeats = 3               # 15 estimations distinctes
)

# ─── 2. Boucle d’entraînement / prédiction
results <- map_df(cv$splits, function(split) {
  train <- analysis(split)
  test  <- assessment(split)
  
  rf <- randomForest(
    SOG ~ Length + Draft + Width + Density + Slender,
    data = train,
    ntree = 400
  )
  
  tibble(
    rmse = rmse_vec(test$SOG, predict(rf, test)),
    mae  = mae_vec (test$SOG, predict(rf, test))
  )
})

# ─── 3. Métriques agrégées
summary_res <- results %>% summarise(across(everything(), list(mean = mean, sd = sd)))

print(summary_res)


