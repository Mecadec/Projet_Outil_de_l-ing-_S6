from __future__ import annotations
import argparse
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Configurations rapides
HORIZONS_MIN = [5, 10, 15]
SEQUENCE_LENGTH = 10        # séquence raccourcie
BATCH_SIZE = 64             # batch plus grand pour accélérer
EPOCHS = 20                 # moins d’époques

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

            if pos < len(times) and abs((times.iloc[pos] - base_time) - pd.Timedelta(minutes=horizon_min)) <= pd.Timedelta(minutes=10):
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

def train_horizon(df, horizon, models_dir, max_samples=None):
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

    model = build_simple_model((SEQUENCE_LENGTH, len(FEATURE_COLS)))
    callbacks = [
        EarlyStopping(patience=3, restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(patience=2, factor=0.5, min_lr=1e-6, verbose=1)
    ]

    model.fit(X_train, y_train, validation_data=(X_test, y_test),
              epochs=EPOCHS, batch_size=BATCH_SIZE, callbacks=callbacks, verbose=1)

    preds = model.predict(X_test, batch_size=BATCH_SIZE)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    print(f"Résultat {horizon}min: MAE={mae:.2f}, RMSE={rmse:.2f} mètres")

    model.save(models_dir / f"lstm_{horizon}min.h5")
    joblib.dump(s_std, models_dir / f"std_{horizon}min.pkl")
    joblib.dump(s_mm, models_dir / f"mm_{horizon}min.pkl")

def main():
    ap = argparse.ArgumentParser()
<<<<<<< Updated upstream:IA/train_model.py
<<<<<<< Updated upstream:IA/train_model.py
    ap.add_argument("--csv", default="db/After_Sort.csv")  # <-- modifié ici
    ap.add_argument("--models-dir", default="models_lstm_fast")
    ap.add_argument("--max-samples", type=int, default=10000)
    args = ap.parse_args()

=======
    ap.add_argument("--csv", required=True)
    ap.add_argument("--models-dir", default="models")
    ap.add_argument("--max-samples", type=int, default=10000)
    args = ap.parse_args()
=======
    ap.add_argument("--csv", required=True)
    ap.add_argument("--models-dir", default="models")
    ap.add_argument("--max-samples", type=int, default=10000)
    args = ap.parse_args()

    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
        except RuntimeError as e:
            print(e)
    print(f"[INFO] GPU(s) détecté(s): {len(gpus)}")
>>>>>>> Stashed changes:IA/besoin4/train_model.py

    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
        except RuntimeError as e:
            print(e)
    print(f"[INFO] GPU(s) détecté(s): {len(gpus)}")

>>>>>>> Stashed changes:IA/besoin4/train_model.py
    df = pd.read_csv(args.csv, low_memory=False)
    df["BaseDateTime"] = pd.to_datetime(df["BaseDateTime"], errors="coerce")
    df["MMSI"] = pd.to_numeric(df["MMSI"], errors="coerce")
    df = df.dropna(subset=["MMSI", "BaseDateTime"])

    # Vérification stricte des colonnes nécessaires
    missing_cols = [col for col in FEATURE_COLS if col not in df.columns]
    if missing_cols:
        print(f"[ERREUR] Les colonnes suivantes sont manquantes dans le CSV : {missing_cols}")
        print("Vérifiez le fichier d'entrée et la variable FEATURE_COLS.")
        exit(1)

    models_dir = Path(args.models_dir)
    models_dir.mkdir(exist_ok=True, parents=True)

    print(f"[INFO] {df.shape[0]} lignes, {df['MMSI'].nunique()} MMSI")
    for h in HORIZONS_MIN:
        train_horizon(df, h, models_dir, args.max_samples)

if __name__ == "__main__":
    main()
