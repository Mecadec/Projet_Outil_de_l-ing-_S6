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

# Configuration rapide pour le modèle
TIME_HORIZONS = [5, 10, 15]
SEQ_LENGTH = 20          # Longueur de séquence
BATCH_SIZE = 64          # Taille des lots
EPOCH_COUNT = 30         # Nombre d'époques

FEATURE_COLUMNS = ["LAT", "LON", "SOG", "COG", "Heading"]
STANDARDIZED_COLUMNS = ["LAT", "LON"]
NORMALIZED_COLUMNS = ["SOG", "COG", "Heading"]

def normalize_features(dataframe: pd.DataFrame):
    cleaned_df = dataframe.dropna(subset=FEATURE_COLUMNS)
    normalized_df = dataframe.copy()

    std_scaler = StandardScaler()
    mm_scaler = MinMaxScaler()

    if STANDARDIZED_COLUMNS:
        normalized_df.loc[cleaned_df.index, STANDARDIZED_COLUMNS] = std_scaler.fit_transform(cleaned_df[STANDARDIZED_COLUMNS])
    if NORMALIZED_COLUMNS:
        normalized_df.loc[cleaned_df.index, NORMALIZED_COLUMNS] = mm_scaler.fit_transform(cleaned_df[NORMALIZED_COLUMNS])

    return normalized_df, std_scaler, mm_scaler

def generate_sequences_and_targets(dataframe, horizon_minutes, sequence_length):
    sequences, targets, vessel_ids = [], [], []

    for vessel_id, group in dataframe.groupby("MMSI"):
        group = group.dropna(subset=["BaseDateTime"] + FEATURE_COLUMNS).sort_values("BaseDateTime").reset_index(drop=True)
        timestamps = group["BaseDateTime"]
        feature_values = group[FEATURE_COLUMNS].values
        latitudes, longitudes = group["LAT"].values, group["LON"].values

        for idx in range(len(group) - sequence_length):
            current_time = timestamps.iloc[idx + sequence_length - 1]
            target_time = current_time + pd.Timedelta(minutes=horizon_minutes)
            target_idx = timestamps.searchsorted(target_time)

            if target_idx < len(timestamps) and abs((timestamps.iloc[target_idx] - current_time) - pd.Timedelta(minutes=horizon_minutes)) <= pd.Timedelta(minutes=2):
                sequences.append(feature_values[idx:idx + sequence_length])
                targets.append([latitudes[target_idx], longitudes[target_idx]])
                vessel_ids.append(vessel_id)

    return np.array(sequences), np.array(targets), vessel_ids

def split_data_by_vessel(sequences, targets, vessel_ids, test_ratio=0.2):
    unique_vessels = np.unique(vessel_ids)
    train_vessels, test_vessels = train_test_split(unique_vessels, test_size=test_ratio, random_state=42)
    train_indices = [i for i, vessel in enumerate(vessel_ids) if vessel in train_vessels]
    test_indices = [i for i, vessel in enumerate(vessel_ids) if vessel in test_vessels]

    return sequences[train_indices], sequences[test_indices], targets[train_indices], targets[test_indices]

def create_model(input_shape):
    model = Sequential([
        LSTM(32, input_shape=input_shape),
        Dense(16, activation='relu'),
        Dense(2)
    ])
    model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])
    return model

def train_for_horizon(dataframe, horizon, output_dir, max_training_samples=None):
    print(f"\n>> Training for {horizon}-minute horizon")

    normalized_df, std_scaler, mm_scaler = normalize_features(dataframe)
    X, y, vessel_ids = generate_sequences_and_targets(normalized_df, horizon, SEQ_LENGTH)

    if len(X) == 0:
        print("[WARNING] No samples generated for this horizon.")
        return

    X_train, X_test, y_train, y_test = split_data_by_vessel(X, y, vessel_ids)

    if max_training_samples and len(X_train) > max_training_samples:
        sampled_indices = np.random.choice(len(X_train), max_training_samples, replace=False)
        X_train, y_train = X_train[sampled_indices], y_train[sampled_indices]

    print(f"Training samples: {len(X_train)} | Testing samples: {len(X_test)}")

    model = create_model((SEQ_LENGTH, len(FEATURE_COLUMNS)))
    callbacks = [
        EarlyStopping(patience=3, restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(patience=2, factor=0.5, min_lr=1e-6, verbose=1)
    ]

    model.fit(X_train, y_train, validation_data=(X_test, y_test),
              epochs=EPOCH_COUNT, batch_size=BATCH_SIZE, callbacks=callbacks, verbose=1)

    predictions = model.predict(X_test, batch_size=BATCH_SIZE)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    print(f"Results for {horizon}-minute horizon: MAE={mae:.2f}, RMSE={rmse:.2f} meters")

    model.save(output_dir / f"lstm_{horizon}min.h5")
    joblib.dump(std_scaler, output_dir / f"std_scaler_{horizon}min.pkl")
    joblib.dump(mm_scaler, output_dir / f"mm_scaler_{horizon}min.pkl")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="db/After_Sort.csv")
    parser.add_argument("--output-dir", default="models_lstm")
    parser.add_argument("--max-samples", type=int, default=10000)
    args = parser.parse_args()

    dataframe = pd.read_csv(args.csv, low_memory=False)
    dataframe["BaseDateTime"] = pd.to_datetime(dataframe["BaseDateTime"], errors="coerce")
    dataframe["MMSI"] = pd.to_numeric(dataframe["MMSI"], errors="coerce")
    dataframe = dataframe.dropna(subset=["MMSI", "BaseDateTime"])

    # Vérification stricte des colonnes nécessaires
    missing_columns = [col for col in FEATURE_COLUMNS if col not in dataframe.columns]
    if missing_columns:
        print(f"[ERROR] Missing columns in the CSV file: {missing_columns}")
        print("Check the input file and FEATURE_COLUMNS variable.")
        exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    print(f"[INFO] {dataframe.shape[0]} rows, {dataframe['MMSI'].nunique()} unique MMSI")
    for horizon in TIME_HORIZONS:
        train_for_horizon(dataframe, horizon, output_dir, args.max_samples)

if __name__ == "__main__":
    main()
