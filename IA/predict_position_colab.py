import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
from google.colab import drive
import os
from sklearn.preprocessing import StandardScaler, MinMaxScaler

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

# Configurations (doivent correspondre à l'entraînement)
SEQUENCE_LENGTH = 10
FEATURE_COLS = ["LAT", "LON", "SOG", "COG", "Heading"]
STANDARD_FEATURES = ["LAT", "LON"]
MINMAX_FEATURES = ["SOG", "COG", "Heading"]
MAX_PRED_SAMPLES = 2000

def load_and_prepare_data(csv_path):
    required_cols = ["MMSI", "BaseDateTime"] + FEATURE_COLS
    try:
        data = pd.read_csv(csv_path, low_memory=False)
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            print(f"[ERREUR] Colonnes manquantes: {missing_cols}")
            return None

        data = data[required_cols].copy()
        data["BaseDateTime"] = pd.to_datetime(data["BaseDateTime"], errors="coerce")
        data["MMSI"] = pd.to_numeric(data["MMSI"], errors="coerce")
        for col in FEATURE_COLS:
            data[col] = pd.to_numeric(data[col], errors="coerce")
        data = data.dropna(subset=["MMSI", "BaseDateTime"] + FEATURE_COLS)

        print(f"[INFO] Données chargées: {len(data)} lignes, {data['MMSI'].nunique()} navires")
        return data

    except Exception as e:
        print(f"[ERREUR] Erreur lors du chargement: {e}")
        return None

def create_sequences_for_prediction(df, seq_len):
    sequences = []
    mmsis = []
    timestamps = []

    for mmsi, group in df.groupby("MMSI"):
        group = group.sort_values("BaseDateTime").reset_index(drop=True)
        if len(group) < seq_len:
            continue
        for i in range(len(group) - seq_len + 1):
            seq_data = group[FEATURE_COLS].iloc[i:i+seq_len].values
            sequences.append(seq_data)
            mmsis.append(mmsi)
            timestamps.append(group["BaseDateTime"].iloc[i+seq_len-1])

    return np.array(sequences), mmsis, timestamps

def normalize_features(data, scaler_std_path, scaler_mm_path):
    try:
        scaler_std = joblib.load(scaler_std_path)
        scaler_mm = joblib.load(scaler_mm_path)
        data_norm = data.copy()

        if STANDARD_FEATURES:
            std_indices = [FEATURE_COLS.index(col) for col in STANDARD_FEATURES]
            data_norm[:, :, std_indices] = scaler_std.transform(
                data_norm[:, :, std_indices].reshape(-1, len(STANDARD_FEATURES))
            ).reshape(data_norm.shape[0], data_norm.shape[1], len(STANDARD_FEATURES))

        if MINMAX_FEATURES:
            mm_indices = [FEATURE_COLS.index(col) for col in MINMAX_FEATURES]
            data_norm[:, :, mm_indices] = scaler_mm.transform(
                data_norm[:, :, mm_indices].reshape(-1, len(MINMAX_FEATURES))
            ).reshape(data_norm.shape[0], data_norm.shape[1], len(MINMAX_FEATURES))

        return data_norm

    except Exception as e:
        print(f"[ERREUR] Erreur lors de la normalisation: {e}")
        return None

def denormalize_predictions(predictions, scaler_std_path):
    try:
        scaler_std = joblib.load(scaler_std_path)
        return scaler_std.inverse_transform(predictions)
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la dénormalisation: {e}")
        return predictions

def predict_with_lstm_model(model_path, scaler_std_path, scaler_mm_path, X_sequences):
    try:
        # Charger le modèle
        model = tf.keras.models.load_model(model_path)
        
        # Normaliser les données
        X_norm = normalize_features(X_sequences, scaler_std_path, scaler_mm_path)
        
        # Faire les prédictions
        predictions = model.predict(X_norm)
        
        # Dénormaliser les prédictions
        pred_denorm = denormalize_predictions(predictions, scaler_std_path)
        
        return pred_denorm
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la prédiction: {e}")
        return None

def save_predictions_to_csv(preds, timestamps, mmsis, output_path):
    if preds is None:
        print("[ERREUR] Aucune prédiction à sauvegarder")
        return

    results = pd.DataFrame({
        'MMSI': mmsis,
        'Timestamp': timestamps,
        'Predicted_LAT': preds[:, 0],
        'Predicted_LON': preds[:, 1]
    })

    results.to_csv(output_path, index=False)
    print(f"Prédictions sauvegardées dans {output_path}")

def main():
    # Lecture des données depuis AfterSort.csv
    print(f"Chargement des données depuis {AFTERSORT_PATH}")
    df = load_and_prepare_data(AFTERSORT_PATH)
    
    if df is None:
        print("Erreur lors du chargement des données")
        return

    # Création des séquences
    X_sequences, mmsis, timestamps = create_sequences_for_prediction(df, SEQUENCE_LENGTH)
    
    if len(X_sequences) == 0:
        print("Aucune séquence créée")
        return

    # Faire les prédictions pour chaque horizon
    for horizon in [5, 10, 15]:
        print(f"\nPrédiction pour horizon {horizon} minutes")
        
        # Chemins des modèles et scalers
        model_path = os.path.join(MODELS_PATH, f'model_{horizon}min.h5')
        scaler_std_path = os.path.join(SCALERS_PATH, f'scaler_std_{horizon}min.joblib')
        scaler_mm_path = os.path.join(SCALERS_PATH, f'scaler_mm_{horizon}min.joblib')

        # Faire les prédictions
        predictions = predict_with_lstm_model(model_path, scaler_std_path, scaler_mm_path, X_sequences)
        
        # Sauvegarder les résultats
        output_path = os.path.join(DATA_PATH, f'predictions_{horizon}min.csv')
        save_predictions_to_csv(predictions, timestamps, mmsis, output_path)

if __name__ == "__main__":
    main()
