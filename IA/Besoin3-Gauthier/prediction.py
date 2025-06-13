import argparse
import os
import gc
from pathlib import Path
import pandas as pd
import numpy as np
import tensorflow as tf
import joblib

# Configuration
SEQUENCE_LENGTH = 10
FEATURE_COLS = ["LAT", "LON", "SOG", "COG", "Heading"]
STANDARD_FEATURES = ["LAT", "LON"]
MINMAX_FEATURES = ["SOG", "COG", "Heading"]
BATCH_SIZE = 32  # Taille des lots pour le traitement

def load_data_in_chunks(csv_path, chunk_size=10000):
    """Charge les données par morceaux pour économiser la RAM"""
    required_cols = ["MMSI", "BaseDateTime"] + FEATURE_COLS
    
    for chunk in pd.read_csv(csv_path, chunksize=chunk_size, usecols=required_cols):
        chunk["BaseDateTime"] = pd.to_datetime(chunk["BaseDateTime"])
        chunk = chunk.dropna(subset=["MMSI", "BaseDateTime"] + FEATURE_COLS)
        yield chunk

def create_sequences_for_mmsi(group_data, seq_len):
    """Crée des séquences pour un seul MMSI"""
    sequences = []
    timestamps = []
    
    if len(group_data) < seq_len:
        return [], []
    
    for i in range(0, len(group_data) - seq_len + 1, seq_len):
        if i + seq_len <= len(group_data):
            seq = group_data[FEATURE_COLS].iloc[i:i+seq_len].values
            sequences.append(seq)
            timestamps.append(group_data["BaseDateTime"].iloc[i+seq_len-1])
    
    return sequences, timestamps

def normalize_batch(batch_data, scaler_std_path, scaler_mm_path):
    """Normalise un lot de données"""
    try:
        scaler_std = joblib.load(scaler_std_path)
        scaler_mm = joblib.load(scaler_mm_path)
    except FileNotFoundError as e:
        print(f"[ERREUR] Fichier de scaler introuvable : {e}")
        return None  # Retourne None si les fichiers de scaler sont manquants
    
    data_norm = batch_data.copy()
    
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

def predict_batch(model, batch_data, scaler_std_path, scaler_mm_path):
    """Fait des prédictions sur un lot"""
    batch_norm = normalize_batch(batch_data, scaler_std_path, scaler_mm_path)
    if batch_norm is None:
        print("[ERREUR] Normalisation échouée, prédictions ignorées")
        return []  # Retourne une liste vide si la normalisation échoue
    
    predictions = model.predict(batch_norm, batch_size=BATCH_SIZE, verbose=0)
    scaler_std = joblib.load(scaler_std_path)
    return scaler_std.inverse_transform(predictions)

def main():
    parser = argparse.ArgumentParser(description="Prédiction de positions futures des navires")
    parser.add_argument('--input', required=True, help="Fichier CSV d'entrée")
    parser.add_argument('--models-dir', required=True, help="Dossier contenant les modèles")
    parser.add_argument('--output', required=True, help="Fichier CSV de sortie")
    parser.add_argument('--max-sequences-per-mmsi', type=int, default=100,
                       help="Nombre maximum de séquences par MMSI")
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    results = []
    first_save = True  # Pour gérer l'en-tête du CSV
    
    # Charge les modèles une seule fois avec les bonnes métriques
    models = {}
    custom_objects = {
        'loss': tf.keras.losses.MeanSquaredError(),
        'mse': tf.keras.losses.MeanSquaredError(),
        'mae': tf.keras.losses.MeanAbsoluteError(),
    }
    
    for model_file in os.listdir(models_dir):
        if model_file.startswith('lstm_') and model_file.endswith('.h5'):
            horizon = model_file.replace('lstm_', '').replace('min.h5', '')
            model_path = models_dir / model_file
            try:
                models[horizon] = tf.keras.models.load_model(
                    model_path,
                    custom_objects=custom_objects,
                    compile=False  # Important: on ne recompile pas
                )
                # Recompile avec les bonnes métriques
                models[horizon].compile(
                    optimizer='adam',
                    loss='mse',
                    metrics=['mae']
                )
                print(f"[INFO] Modèle chargé: {model_file}")
            except Exception as e:
                print(f"[ERREUR] Impossible de charger {model_file}: {e}")
                continue  # Continue avec les autres modèles

    if not models:
        print("[ERREUR] Aucun modèle n'a pu être chargé")
        return

    # Traitement par chunks pour économiser la RAM
    for chunk_idx, chunk in enumerate(load_data_in_chunks(args.input)):
        print(f"\n[INFO] Traitement du chunk {chunk_idx+1}")
        
        for mmsi, group in chunk.groupby("MMSI"):
            sequences, timestamps = create_sequences_for_mmsi(
                group.sort_values("BaseDateTime"), SEQUENCE_LENGTH
            )
            
            if not sequences:
                continue
                
            # Limite le nombre de séquences par MMSI
            if len(sequences) > args.max_sequences_per_mmsi:
                indices = np.linspace(0, len(sequences)-1, args.max_sequences_per_mmsi, dtype=int)
                sequences = [sequences[i] for i in indices]
                timestamps = [timestamps[i] for i in indices]
            
            sequences = np.array(sequences)
            
            # Prédiction pour chaque horizon
            for horizon, model in models.items():
                try:
                    predictions = predict_batch(
                        model, 
                        sequences,
                        models_dir / f"std_scaler_{horizon}min.pkl",
                        models_dir / f"mm_scaler_{horizon}min.pkl"
                    )
                    
                    # Stockage des résultats
                    for i, (pred, timestamp) in enumerate(zip(predictions, timestamps)):
                        results.append({
                            'MMSI': mmsi,
                            'BaseDateTime': timestamp,
                            'Horizon_min': horizon,
                            'Predicted_LAT': pred[0],
                            'Predicted_LON': pred[1],
                            'Sequence_ID': i
                        })
                except Exception as e:
                    print(f"[ERREUR] Échec de prédiction pour l'horizon {horizon} : {e}")
                    continue  # Continue avec les autres horizons
            
            # Nettoyage mémoire
            del sequences
            gc.collect()
        
        # Sauvegarde intermédiaire modifiée
        if len(results) > 50000:
            try:
                df_to_save = pd.DataFrame(results)
                if first_save:
                    # Première sauvegarde : créer le fichier avec en-tête
                    df_to_save.to_csv(args.output, index=False, mode='w')
                    first_save = False
                else:
                    # Sauvegardes suivantes : ajouter sans en-tête
                    df_to_save.to_csv(args.output, index=False, mode='a', header=False)
                print(f"[INFO] Sauvegarde intermédiaire : {len(results)} prédictions ajoutées")
                results = []  # Vider la liste après sauvegarde
            except Exception as e:
                print(f"[ERREUR] Échec de la sauvegarde intermédiaire : {e}")
    
    # Sauvegarde finale modifiée
    if results:
        try:
            df_to_save = pd.DataFrame(results)
            if first_save:
                # Si c'est la première et unique sauvegarde
                df_to_save.to_csv(args.output, index=False, mode='w')
            else:
                # Sinon ajouter à la suite
                df_to_save.to_csv(args.output, index=False, mode='a', header=False)
            print(f"[INFO] Sauvegarde finale : {len(results)} prédictions ajoutées")
        except Exception as e:
            print(f"[ERREUR] Échec de la sauvegarde finale : {e}")
    
    # Vérification finale
    try:
        if os.path.exists(args.output):
            final_count = len(pd.read_csv(args.output))
            print(f"\n[INFO] Fichier de prédictions créé avec succès : {args.output}")
            print(f"[INFO] Nombre total de prédictions : {final_count}")
        else:
            print("\n[ERREUR] Le fichier de sortie n'a pas été créé correctement")
    except Exception as e:
        print(f"\n[ERREUR] Impossible de vérifier le fichier de sortie : {e}")

if __name__ == "__main__":
    main()
