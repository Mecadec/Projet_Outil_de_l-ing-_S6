import argparse
import os
import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
from pathlib import Path

# Configurations (doivent correspondre à l'entraînement)
SEQUENCE_LENGTH = 10  # Réduit pour limiter la mémoire et correspondre à l'entraînement
FEATURE_COLS = ["LAT", "LON", "SOG", "COG", "Heading"]
STANDARD_FEATURES = ["LAT", "LON"]
MINMAX_FEATURES = ["SOG", "COG", "Heading"]
MAX_PRED_SAMPLES = 2000  # Limite stricte pour éviter de saturer la RAM

def load_and_prepare_data(csv_path):
    """Charge et prépare les données comme lors de l'entraînement"""
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
    """Crée des séquences pour la prédiction"""
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
    """Normalise les features avec les scalers sauvegardés"""
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
    """Dénormalise les prédictions LAT/LON"""
    try:
        scaler_std = joblib.load(scaler_std_path)
        return scaler_std.inverse_transform(predictions)
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la dénormalisation: {e}")
        return predictions

def predict_with_lstm_model(model_path, scaler_std_path, scaler_mm_path, X_sequences):
    """Fait des prédictions avec un modèle LSTM"""
    try:
        custom_objects_list = [
            {
                'mse': tf.keras.losses.MeanSquaredError(),
                'mae': tf.keras.metrics.MeanAbsoluteError(),
                'MeanSquaredError': tf.keras.losses.MeanSquaredError(),
                'MeanAbsoluteError': tf.keras.metrics.MeanAbsoluteError()
            },
            {
                'mse': 'mse',
                'mae': 'mae'
            },
            None
        ]

        model = None
        for i, custom_objects in enumerate(custom_objects_list):
            try:
                if custom_objects:
                    model = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
                else:
                    model = tf.keras.models.load_model(model_path)
                print(f"[INFO] Modèle chargé avec succès (méthode {i+1}): {model_path}")
                break
            except Exception as e:
                print(f"[WARN] Tentative {i+1} échouée: {str(e)[:100]}...")
                continue

        if model is None:
            raise Exception("Impossible de charger le modèle avec toutes les méthodes")

        print(f"[INFO] Architecture: {model.input_shape} -> {model.output_shape}")

        X_normalized = normalize_features(X_sequences, scaler_std_path, scaler_mm_path)
        if X_normalized is None:
            return None

        predictions = model.predict(X_normalized, batch_size=32, verbose=0)
        predictions_denorm = denormalize_predictions(predictions, scaler_std_path)

        print(f"[INFO] Prédictions effectuées: {len(predictions)} échantillons")
        print(f"[INFO] Exemple de prédictions (LAT, LON): {predictions_denorm[:3]}")

        return predictions_denorm

    except Exception as e:
        print(f"[ERREUR] Erreur lors de la prédiction: {e}")
        return None

def save_predictions_to_csv(preds, timestamps, mmsis, output_path):
    """Sauvegarde les prédictions dans un CSV"""
    df_out = pd.DataFrame({
        "MMSI": mmsis,
        "timestamp": timestamps,
        "pred_LAT": preds[:, 0],
        "pred_LON": preds[:, 1],
    })

    df_out.to_csv(output_path, index=False)
    print(f"[INFO] Prédictions sauvegardées dans {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Prédiction de positions futures des navires")
    parser.add_argument('--input', default="db/After_Sort.csv", help="Fichier CSV d'entrée")
    parser.add_argument('--models-dir', required=True, help="Dossier contenant les modèles et scalers")
    parser.add_argument('--output', required=True, help="Fichier CSV de sortie pour les prédictions")
    parser.add_argument('--max-pred-samples', type=int, default=5000, help="Nombre max de séquences à prédire (pour limiter la mémoire)")
    args = parser.parse_args()

    data = load_and_prepare_data(args.input)
    if data is None:
        return

    X_sequences, mmsis, timestamps = create_sequences_for_prediction(data, SEQUENCE_LENGTH)
    if len(X_sequences) == 0:
        print("[ERREUR] Aucune séquence créée. Vérifiez que vous avez assez de données par navire.")
        return

    # Limite mémoire : sous-échantillonnage si trop de séquences
    max_samples = args.max_pred_samples if args.max_pred_samples else MAX_PRED_SAMPLES
    if len(X_sequences) > max_samples:
        print(f"[WARN] Trop de séquences ({len(X_sequences)}). Seules les {max_samples} premières seront utilisées pour éviter un crash mémoire.")
        X_sequences = X_sequences[:max_samples]
        mmsis = mmsis[:max_samples]
        timestamps = timestamps[:max_samples]

    print(f"[INFO] {len(X_sequences)} séquences utilisées pour la prédiction")

    models_dir = Path(args.models_dir)
    all_results = []

    for model_file in os.listdir(models_dir):
        if model_file.startswith('lstm_') and model_file.endswith('.h5'):
            horizon = model_file.replace('lstm_', '').replace('min.h5', '')
            model_path = models_dir / model_file
            scaler_std_path = models_dir / f"std_{horizon}min.pkl"
            scaler_mm_path = models_dir / f"mm_{horizon}min.pkl"

            if not all([model_path.exists(), scaler_std_path.exists(), scaler_mm_path.exists()]):
                print(f"[WARN] Fichiers manquants pour horizon {horizon}min")
                continue

            print(f"\n[INFO] Prédiction pour horizon {horizon} minutes...")
            preds = predict_with_lstm_model(str(model_path), str(scaler_std_path), str(scaler_mm_path), X_sequences)
            if preds is None:
                print(f"[WARN] Prédiction échouée pour l'horizon {horizon}min")
                continue

            for i, (mmsi, timestamp, pred) in enumerate(zip(mmsis, timestamps, preds)):
                all_results.append({
                    'MMSI': mmsi,
                    'BaseDateTime': timestamp,
                    'Horizon_min': horizon,
                    'Predicted_LAT': pred[0],
                    'Predicted_LON': pred[1],
                    'Sequence_ID': i
                })

    if all_results:
        df_results = pd.DataFrame(all_results)
        df_results.to_csv(args.output, index=False)
        print(f"\n[INFO] Prédictions sauvegardées dans {args.output}")
    else:
        print("\n[ERREUR] Aucune prédiction générée.")

if __name__ == "__main__":
    main()
