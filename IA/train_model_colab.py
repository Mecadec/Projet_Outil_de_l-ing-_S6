from __future__ import annotations
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import joblib
from google.colab import drive
import os
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split

# Montage du Google Drive
try:
    drive.mount('/content/drive')
    print("Google Drive monté avec succès")
except Exception as e:
    print(f"Erreur lors du montage de Google Drive: {e}")

# Configuration des chemins
PROJECT_PATH = '/content/drive/MyDrive/MonProjet'
DATA_PATH = os.path.join(PROJECT_PATH, 'data')
MODELS_PATH = os.path.join(PROJECT_PATH, 'models')
SCALERS_PATH = os.path.join(PROJECT_PATH, 'scalers')

# Chemin vers la base de données

AFTERSORT_PATH = os.path.join(DATA_PATH, 'After_Sort.csv')

# Création des dossiers s'ils n'existent pas
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(MODELS_PATH, exist_ok=True)
os.makedirs(SCALERS_PATH, exist_ok=True)

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# Configurations rapides
HORIZONS_MIN = [5, 10, 15]
SEQUENCE_LENGTH = 10        # séquence raccourcie
BATCH_SIZE = 64             # batch plus grand pour accélérer
EPOCHS = 20                 # moins d'époques

FEATURE_COLS = ["LAT", "LON", "SOG", "COG", "Heading"]
STANDARD_FEATURES = ["LAT", "LON"]
MINMAX_FEATURES = ["SOG", "COG", "Heading"]

def prepare_features(df: pd.DataFrame):
    df_clean = df.dropna(subset=FEATURE_COLS)
    df_norm = df.copy()

    scaler_std = StandardScaler()
    scaler_mm = MinMaxScaler()

    if STANDARD_FEATURES:
        df_norm.loc[df_clean.index, STANDARD_FEATURES] = scaler_std.fit_transform(df_clean[STANDARD_FEATURES])
    if MINMAX_FEATURES:
        df_norm.loc[df_clean.index, MINMAX_FEATURES] = scaler_mm.fit_transform(df_clean[MINMAX_FEATURES])

    return df_norm, scaler_std, scaler_mm

def create_sequences_and_targets(df, horizon_min, seq_len):
    seqs, targs, mmsis = [], [], []

    for mmsi, grp in df.groupby("MMSI"):
        grp = grp.dropna(subset=["BaseDateTime"] + FEATURE_COLS).sort_values("BaseDateTime").reset_index(drop=True)
        times = grp["BaseDateTime"]
        vals = grp[FEATURE_COLS].values
        lat_vals, lon_vals = grp["LAT"].values, grp["LON"].values

        for i in range(len(grp) - seq_len):
            base_time = times.iloc[i + seq_len - 1]
            target_time = base_time + pd.Timedelta(minutes=horizon_min)
            pos = times.searchsorted(target_time)

            if pos < len(times) and abs((times.iloc[pos] - base_time) - pd.Timedelta(minutes=horizon_min)) <= pd.Timedelta(minutes=2):
                seqs.append(vals[i:i + seq_len])
                targs.append([lat_vals[pos], lon_vals[pos]])
                mmsis.append(mmsi)

    return np.array(seqs), np.array(targs), mmsis

def split_by_mmsi(seqs, targs, mmsis, test_size=0.2):
    uniq = np.unique(mmsis)
    train_m, test_m = train_test_split(uniq, test_size=test_size, random_state=42)
    train_idx = [i for i, m in enumerate(mmsis) if m in train_m]
    test_idx = [i for i, m in enumerate(mmsis) if m in test_m]

    return seqs[train_idx], seqs[test_idx], targs[train_idx], targs[test_idx]

def build_simple_model(input_shape):
    model = Sequential([
        LSTM(32, input_shape=input_shape),
        Dense(16, activation='relu'),
        Dense(2)
    ])
    model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])
    return model

def train_horizon(df, horizon, max_samples=None):
    print(f"\n>> Horizon {horizon} min")

    df_norm, s_std, s_mm = prepare_features(df)
    X, y, mmsis = create_sequences_and_targets(df_norm, horizon, SEQUENCE_LENGTH)

    if len(X) == 0:
        print("[WARN] Aucun échantillon généré pour cet horizon.")
        return

    X_train, X_test, y_train, y_test = split_by_mmsi(X, y, mmsis)

    if max_samples and len(X_train) > max_samples:
        idx = np.random.choice(len(X_train), max_samples, replace=False)
        X_train, y_train = X_train[idx], y_train[idx]

    print(f"Train {len(X_train)} | Test {len(X_test)}")

    # Sauvegarde des scalers
    scaler_std_path = os.path.join(SCALERS_PATH, f'scaler_std_{horizon}min.joblib')
    scaler_mm_path = os.path.join(SCALERS_PATH, f'scaler_mm_{horizon}min.joblib')
    joblib.dump(s_std, scaler_std_path)
    joblib.dump(s_mm, scaler_mm_path)

    # Construction et entraînement du modèle
    model = build_simple_model((SEQUENCE_LENGTH, len(FEATURE_COLS)))
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=[
            EarlyStopping(patience=5, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.1, patience=3)
        ]
    )

    # Sauvegarde du modèle
    model_path = os.path.join(MODELS_PATH, f'model_{horizon}min.h5')
    model.save(model_path)
    print(f"Modèle sauvegardé à {model_path}")

def main():
    # Lecture des données depuis AfterSort.csv
    print(f"Chargement des données depuis {AFTERSORT_PATH}")
    df = pd.read_csv(AFTERSORT_PATH)
    df["BaseDateTime"] = pd.to_datetime(df["BaseDateTime"], format="%Y-%m-%d %H:%M:%S")  # Format de date à ajuster selon vos données

    # Entraînement pour chaque horizon
    for horizon in HORIZONS_MIN:
        train_horizon(df, horizon)

if __name__ == "__main__":
    main()
