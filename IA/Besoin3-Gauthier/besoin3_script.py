"""
Script Python pour la prédiction de trajectoires de navires.
Ce script reprend les étapes principales du notebook, en les organisant en fonctions.
Certaines fonctions sont des améliorations ou des variantes d'étapes précédentes (voir commentaires).
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
# Ajout TensorFlow
import tensorflow as tf
from tensorflow import keras

def load_and_prepare_data(csv_path):
    """Chargement et tri du jeu de données."""
    df = pd.read_csv(csv_path, parse_dates=["BaseDateTime"])
    df.sort_values("BaseDateTime", inplace=True)
    # Suppression des lignes avec LAT ou LON manquants
    df = df.dropna(subset=["LAT", "LON"])
    return df

def split_by_mmsi(df, n_train=97, n_test=30, n_val=22, seed=42):
    """Séparation en train/test/val par MMSI."""
    mmsi_uniques = df['MMSI'].dropna().unique()
    np.random.seed(seed)
    np.random.shuffle(mmsi_uniques)
    mmsi_train = mmsi_uniques[:n_train]
    mmsi_test = mmsi_uniques[n_train:n_train + n_test]
    mmsi_val = mmsi_uniques[n_train + n_test:n_train + n_test + n_val]
    df_train = df[df['MMSI'].isin(mmsi_train)]
    df_test = df[df['MMSI'].isin(mmsi_test)]
    df_val = df[df['MMSI'].isin(mmsi_val)]
    return df_train, df_test, df_val

def create_future_targets(df, horizon_minutes=[5,10,15]):
    """Ajoute les colonnes de cibles futures (amélioration : généralisable à plusieurs horizons)."""
    df = df.sort_values(["MMSI", "BaseDateTime"]).copy()
    for h in horizon_minutes:
        df[f'LAT_t+{h}'] = df.groupby('MMSI')['LAT'].shift(-h)
        df[f'LON_t+{h}'] = df.groupby('MMSI')['LON'].shift(-h)
    return df

def add_time_features(df):
    """Ajoute des features cycliques sur l'heure."""
    df = df.copy()
    df['hour'] = df['BaseDateTime'].dt.hour
    df['minute'] = df['BaseDateTime'].dt.minute
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['minute_sin'] = np.sin(2 * np.pi * df['minute'] / 60)
    df['minute_cos'] = np.cos(2 * np.pi * df['minute'] / 60)
    return df

def add_previous_features(df):
    """Ajoute la vitesse et le cap précédents comme features."""
    df = df.copy()
    df['SOG_prev'] = df.groupby('MMSI')['SOG'].shift(1)
    df['COG_prev'] = df.groupby('MMSI')['COG'].shift(1)
    df['LAT_prev'] = df.groupby('MMSI')['LAT'].shift(1)
    df['LON_prev'] = df.groupby('MMSI')['LON'].shift(1)
    return df

def add_immobile_feature(df, sog_threshold=0.5):
    """Ajoute une colonne binaire indiquant si le bateau est immobile."""
    df = df.copy()
    df['is_immobile'] = (df['SOG'] < sog_threshold).astype(int)
    return df

def prepare_features(df):
    """Ajoute toutes les features avancées."""
    df = add_time_features(df)
    df = add_previous_features(df)
    df = add_immobile_feature(df)
    return df

def train_regression(df_train_h, features, target_cols, epochs=50, batch_size=32):
    """Entraîne un réseau de neurones simple (Keras) avec normalisation."""
    scaler = StandardScaler()
    X = df_train_h[features].fillna(df_train_h[features].mean())
    X_scaled = scaler.fit_transform(X)
    y = df_train_h[target_cols].values

    # Modèle simple : 2 couches denses
    model = keras.Sequential([
        keras.layers.Input(shape=(X_scaled.shape[1],)),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dense(len(target_cols))  # sortie: LAT, LON
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X_scaled, y, epochs=epochs, batch_size=batch_size, verbose=0)
    return model, scaler

def predict_last_points(df_test_h, df_train_h, features, regs, scalers, horizons, sog_threshold=0.2):
    """
    Génère les prédictions pour le dernier point de chaque MMSI pour plusieurs horizons.
    Si le bateau est immobile, la prédiction reste au point d'origine.
    """
    last_points = df_test_h.sort_values("BaseDateTime").groupby("MMSI").tail(1).copy()
    X_last = last_points[features].fillna(df_train_h[features].mean())
    pred_dfs = []
    for h in horizons:
        X_last_scaled = scalers[h].transform(X_last)
        y_pred = regs[h](X_last_scaled)  # Correction ici : appel direct de la fonction
        # y_pred est déjà un numpy array
        df_pred = last_points.copy()
        # Correction : si immobile, garder la position d'origine
        immobile_mask = last_points['is_immobile'] == 1
        y_pred[immobile_mask.values, 0] = last_points.loc[immobile_mask, 'LAT'].values
        y_pred[immobile_mask.values, 1] = last_points.loc[immobile_mask, 'LON'].values
        df_pred['LAT'] = y_pred[:,0]
        df_pred['LON'] = y_pred[:,1]
        df_pred['BaseDateTime'] = df_pred['BaseDateTime'] + pd.Timedelta(minutes=h)
        df_pred['is_prediction'] = f"Prédiction +{h}min"
        print(f"\n--- Prédictions pour horizon +{h}min ---")
        print(df_pred[['MMSI', 'BaseDateTime', 'LAT', 'LON', 'is_prediction']])
        pred_dfs.append(df_pred)
    return last_points, pred_dfs

def plot_trajectories(df_test_h, last_points, pred_dfs, horizons):
    """Affiche les trajectoires réelles et les prédictions, chaque segment coloré selon l'horizon."""
    color_map = {
        f"Prédiction +{h}min": c for h, c in zip(horizons, ["#EF553B", "#00CC96", "#AB63FA"])
    }
    fig = go.Figure()
    # Trajectoires réelles
    for mmsi, group in df_test_h.groupby("MMSI"):
        group_sorted = group.sort_values("BaseDateTime")
        fig.add_trace(go.Scattermap(
            lat=group_sorted["LAT"],
            lon=group_sorted["LON"],
            mode="lines+markers",
            marker=dict(size=6, color="#636efa"),
            line=dict(color="#636efa", width=2),
            name=f"MMSI {mmsi} - Réel",
            legendgroup=f"{mmsi}_reel",
            showlegend=False
        ))
    # Segments de prédiction pour les n derniers points
    for mmsi, group in last_points.groupby("MMSI"):
        for idx, last_row in group.iterrows():
            lat0, lon0 = last_row["LAT"], last_row["LON"]
            for df_pred, h in zip(pred_dfs, horizons):
                label = f"Prédiction +{h}min"
                pred_row = df_pred.loc[idx]
                lat1, lon1 = pred_row["LAT"], pred_row["LON"]
                # Vérification NaN
                if pd.isna(lat0) or pd.isna(lon0) or pd.isna(lat1) or pd.isna(lon1):
                    continue  # Ignore ce segment si un point est NaN
                fig.add_trace(go.Scattermap(
                    lat=[float(lat0), float(lat1)],
                    lon=[float(lon0), float(lon1)],
                    mode="lines+markers",
                    marker=dict(size=8, color=color_map[label]),
                    line=dict(color=color_map[label], width=3),
                    name=label,
                    legendgroup=label,
                    showlegend=False
                ))
                fig.add_trace(go.Scattermap(
                    lat=[float(lat1)],
                    lon=[float(lon1)],
                    mode="markers",
                    marker=dict(size=12, color=color_map[label], symbol="star"),
                    name=f"{label} (point)",
                    legendgroup=label,
                    showlegend=False
                ))
    # Ajout d'une légende pour chaque horizon (une seule fois)
    for h in horizons:
        label = f"Prédiction +{h}min"
        fig.add_trace(go.Scattermap(
            lat=[None], lon=[None],
            mode="lines+markers",
            marker=dict(size=8, color=color_map[label]),
            line=dict(color=color_map[label], width=3),
            name=label,
            legendgroup=label,
            showlegend=True
        ))
    fig.add_trace(go.Scattermap(
        lat=[None], lon=[None],
        mode="lines+markers",
        marker=dict(size=6, color="#636efa"),
        line=dict(color="#636efa", width=2),
        name="Réel",
        legendgroup="Réel"
    ))
    fig.update_layout(
        map_style="open-street-map",
        map_zoom=4,
        map_center={"lat": df_test_h["LAT"].mean(), "lon": df_test_h["LON"].mean()},
        title="Trajectoires réelles et prédictions (+5min, +10min, +15min) pour chaque bateau (40 derniers points)",
        legend=dict(itemsizing="constant")
    )
    # fig.show()
    fig.write_html("map.html", auto_open=True)

def evaluate_model(df_test_h, pred_dfs, horizons):
    """Évalue le modèle en calculant l'erreur absolue moyenne (MAE) pour chaque horizon."""
    from sklearn.metrics import mean_absolute_error
    for h, df_pred in zip(horizons, pred_dfs):
        # Pour chaque horizon, on cherche la vérité terrain sur le dernier point de chaque MMSI
        lat_true = df_test_h.groupby("MMSI").tail(1)[f'LAT_t+{h}']
        lon_true = df_test_h.groupby("MMSI").tail(1)[f'LON_t+{h}']
        lat_pred = df_pred['LAT']
        lon_pred = df_pred['LON']
        # Supprimer les lignes où la vérité ou la prédiction est NaN
        mask = (~lat_true.isna()) & (~lon_true.isna()) & (~lat_pred.isna()) & (~lon_pred.isna())
        lat_true_valid = lat_true[mask]
        lon_true_valid = lon_true[mask]
        lat_pred_valid = lat_pred[mask]
        lon_pred_valid = lon_pred[mask]
        total = len(lat_true)
        valides = len(lat_true_valid)
        ignores = total - valides
        if valides == 0:
            print(f"\nMAE pour horizon +{h}min : Pas de données valides pour l'évaluation.")
            continue
        mae_lat = mean_absolute_error(lat_true_valid, lat_pred_valid)
        mae_lon = mean_absolute_error(lon_true_valid, lon_pred_valid)
        print(f"\nMAE pour horizon +{h}min :")
        print(f"  Latitude : {mae_lat:.6f}")
        print(f"  Longitude: {mae_lon:.6f}")
        print(f"  MMSI valides : {valides} / {total} (ignorés : {ignores})")
        # Affiche les MMSI ignorés si besoin
        if ignores > 0:
            mmsi_ignores = lat_true.index[~mask]
            print(f"  MMSI ignorés (pas de vérité terrain horizon +{h}min) : {list(mmsi_ignores)}")

if __name__ == "__main__":
    # Paramètres
    csv_path = "Besoin3-Gauthier/After_Sort.csv"
    horizons = [5, 10, 15]

    # Chargement et split
    df = load_and_prepare_data(csv_path)
    df = prepare_features(df)
    df_train, df_test, df_val = split_by_mmsi(df)
    df_train_targets = create_future_targets(df_train, horizons)
    df_test_targets = create_future_targets(df_test, horizons)
    # On garde jusqu'à 40 derniers points de chaque MMSI pour l'entraînement (même si moins de 40)
    df_train_h = df_train_targets.groupby("MMSI").apply(lambda g: g.tail(40)).reset_index(drop=True)
    df_train_h = df_train_h.dropna(subset=[f'LAT_t+{horizons[0]}', f'LON_t+{horizons[0]}'])
    df_test_h = df_test_targets.dropna(subset=[f'LAT_t+{horizons[0]}', f'LON_t+{horizons[0]}'])

    # Définir les nouvelles features
    features = [
        "LAT", "LON", "SOG", "COG", "Heading", "VesselType", "Length", "Draft",
        "hour_sin", "hour_cos", "minute_sin", "minute_cos",
        "SOG_prev", "COG_prev", "LAT_prev", "LON_prev",
        "is_immobile"
    ]

    # Entraînement des modèles pour chaque horizon (multi-horizon)
    regs = {}
    scalers = {}
    for h in horizons:
        train_h = df_train_h.dropna(subset=[f'LAT_t+{h}', f'LON_t+{h}'])
        reg, scaler = train_regression(train_h, features, [f'LAT_t+{h}', f'LON_t+{h}'])
        regs[h] = reg
        scalers[h] = scaler

    # Prédiction sur le dernier point de chaque MMSI
    # Adapter la prédiction pour Keras (model.predict)
    def keras_predict(model, X):
        # Keras retourne un array numpy
        return model.predict(X, verbose=0)

    # Remplacer la méthode de prédiction dans regs
    for h in horizons:
        # Remplacer la méthode predict par keras_predict partiellement appliquée
        model = regs[h]
        regs[h] = lambda X, model=model: keras_predict(model, X)

    last_points, pred_dfs = predict_last_points(df_test_h, df_train_h, features, regs, scalers, horizons)

    # Affichage récapitulatif dans la console
    for h, df_pred in zip(horizons, pred_dfs):
        print(f"\nRésumé des prédictions pour horizon +{h}min :")
        print(df_pred[['MMSI', 'BaseDateTime', 'LAT', 'LON', 'is_prediction']])

    # Évaluation du modèle
    evaluate_model(df_test_h, pred_dfs, horizons)

    # Visualisation avancée
    plot_trajectories(df_test_h, last_points, pred_dfs, horizons)

# RÉPONSE SYNTHÉTIQUE À LA QUESTION

# Oui, le script répond aux attentes du besoin client 3 :
# - Il entraîne un modèle (régression linéaire multivariée) pour prédire les positions futures (LAT, LON) à différents horizons temporels (5, 10, 15 min).
# - Les variables explicatives utilisées incluent : SOG, COG, Heading, VesselType, Length, Draft, BaseDateTime (via features cycliques), ainsi que des features avancées (valeurs précédentes, indicateur d'immobilité).
# - Les variables dépendantes prédites sont bien LAT et LON.
# - Le script affiche les prédictions et évalue la performance du modèle (MAE) pour chaque horizon.
# - L'ensemble du pipeline (préparation, entraînement, prédiction, évaluation, visualisation) est automatisé et exploite les données historiques du navire.
