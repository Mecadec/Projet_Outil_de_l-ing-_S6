#!/usr/bin/env python3.12
# -*- coding: utf-8 -*-

import sys
import joblib
import numpy as np
import pandas as pd
import random
import time
from datetime import datetime
from typing import Dict, List, Tuple, Union, Any
from pathlib import Path

# Vérification des versions des dépendances
try:
    import sklearn
    from sklearn.pipeline import Pipeline
    from sklearn.compose import ColumnTransformer
    from catboost import CatBoostClassifier
    
    if sklearn.__version__ != '1.5.0':
        print("ATTENTION: Ce script a été testé avec scikit-learn 1.5.0. "
              f"Version détectée: {sklearn.__version__}")
        
except ImportError as e:
    print("ERREUR: Certaines dépendances ne sont pas installées. "
          "Veuillez exécuter: pip install -r requirements.txt")
    print(f"Détail de l'erreur: {str(e)}")
    sys.exit(1)

# Configuration du logger
class Logger:
    """Redirige la sortie standard vers un fichier et la console."""
    def __init__(self, filename: str = 'prediction_output.txt'):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', encoding='utf-8')
    
    def write(self, message: str) -> None:
        self.terminal.write(message)
        self.log.write(message)
    
    def flush(self) -> None:
        self.terminal.flush()
        self.log.flush()
    
    def __enter__(self):
        sys.stdout = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log.close()
        sys.stdout = self.terminal

# Configuration des chemins
MODEL_PATH = Path('models', 'model_vesseltypeHGB.pkl')
DATA_PATH = Path('After_Sort_sans_l&w_vide.csv')

# Configuration des colonnes
EXPECTED_COLUMNS = [
    'SOG', 'COG', 'Heading', 'Length', 'Width', 
    'Draft', 'Latitude', 'Longitude', 'log_SOG', 'lw_ratio'
]

# Fonction principale
def main() -> None:
    """Fonction principale du script de prédiction."""
    # Initialisation du logger
    with Logger() as logger:
        try:
            print("=== DÉBUT DU SCRIPT ===\n")
            print("=== PRÉDICTION AVEC PIPELINE ===\n")
            
            # Initialisation du générateur aléatoire
            seed = int(time.time())
            random.seed(seed)
            np.random.seed(seed)
            print(f"Graine aléatoire utilisée: {seed}\n")

            # Générer une graine aléatoire basée sur le temps actuel
            random_seed = int(time.time()) % 10000
            random.seed(random_seed)
            np.random.seed(random_seed)
            print(f"Graine aléatoire utilisée: {random_seed}\n")

            # Chemins des fichiers
            base_dir = Path(__file__).parent
            model_path = MODEL_PATH
            csv_path = DATA_PATH

            # 1. Charger le modèle
            print("1. Chargement du modèle...")
            try:
                model_dict = joblib.load(model_path)
                print(f"   Type du modèle chargé: {type(model_dict)}")
                
                # Vérifier que c'est bien un dictionnaire avec une clé 'model' qui est un Pipeline
                if not isinstance(model_dict, dict) or 'model' not in model_dict:
                    print("   ERREUR: Le modèle n'est pas dans le format attendu (dictionnaire avec clé 'model')")
                    exit(1)
                
                model = model_dict['model']
                print(f"   Type du modèle interne: {type(model)}")
                
                # Vérifier que c'est bien un Pipeline
                if not isinstance(model, Pipeline):
                    print("   ERREUR: Le modèle n'est pas un Pipeline scikit-learn")
                    exit(1)
                
                # Afficher les étapes du pipeline et les caractéristiques attendues
                print("\n2. Inspection du pipeline:")
                for i, (name, step) in enumerate(model.steps, 1):
                    print(f"   {i}. {name}: {type(step).__name__}")
                    
                    # Afficher les détails du préprocesseur ColumnTransformer s'il existe
                    if name == 'prep' and hasattr(step, 'transformers'):
                        print("      Transformers:")
                        for (trans_name, trans, columns) in step.transformers:
                            print(f"      - {trans_name}: {type(trans).__name__} sur les colonnes: {columns}")
                    
                    # Afficher les caractéristiques attendues si disponibles
                    if hasattr(step, 'get_feature_names_out'):
                        try:
                            features = step.get_feature_names_out()
                            print(f"      Caractéristiques de sortie: {len(features)} features")
                            print(f"      Exemple de features: {features[:5]}..." if len(features) > 5 else f"      Features: {features}")
                        except Exception as e:
                            print(f"      Impossible d'obtenir les noms des features: {e}")
            
                # Charger les données
                print("\n3. Chargement des données...")
                df = pd.read_csv(csv_path, nrows=100)  # Charger seulement 100 lignes pour le test
                print(f"   {len(df)} lignes chargées")
                
                # Vérifier les colonnes requises
                required_columns = ['MMSI', 'VesselName', 'VesselType', 'SOG', 'COG', 'Length', 'Width', 'Draft']
                missing = [col for col in required_columns if col not in df.columns]
                if missing:
                    print(f"   ERREUR: Colonnes manquantes: {', '.join(missing)}")
                    exit(1)
                
                # Nettoyer les données
                print("\n4. Nettoyage des données...")
                df_clean = df.dropna(subset=required_columns).copy()
                for col in ['SOG', 'COG', 'Length', 'Width', 'Draft', 'VesselType']:
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                
                # Filtrer les types de navires valides (60-90)
                df_clean = df_clean[(df_clean['VesselType'] >= 60) & (df_clean['VesselType'] <= 90)]
                
                if df_clean.empty:
                    print("   ERREUR: Aucune donnée valide après nettoyage")
                    exit(1)
                
                print(f"   {len(df_clean)} lignes après nettoyage")
                
                # Sélectionner 5 navires au hasard
                print("\n5. Sélection des navires pour la prédiction...")
                sample = df_clean.sample(min(5, len(df_clean)))
                
                # Colonnes attendues par le modèle (avec les noms du fichier CSV)
                # Le modèle attend 'Latitude' et 'Longitude' mais notre fichier utilise 'LAT' et 'LON'
                expected_features = EXPECTED_COLUMNS
                
                print("\n   Colonnes attendues par le modèle:", ', '.join(expected_features))
                
                # Créer une copie des données pour la prédiction
                X_pred = sample.copy()
                
                # Renommer les colonnes LAT/LON en Latitude/Longitude si nécessaire
                if 'LAT' in X_pred.columns and 'Latitude' not in X_pred.columns:
                    X_pred['Latitude'] = X_pred['LAT']
                if 'LON' in X_pred.columns and 'Longitude' not in X_pred.columns:
                    X_pred['Longitude'] = X_pred['LON']
                
                # Vérifier et créer les colonnes manquantes
                missing_cols = [col for col in expected_features if col not in X_pred.columns]
                if missing_cols:
                    print(f"   ATTENTION: Colonnes manquantes: {', '.join(missing_cols)}")
                    
                    # Essayer de créer les colonnes manquantes si possible
                    if 'log_SOG' in missing_cols and 'SOG' in X_pred.columns:
                        print("   Création de log_SOG = log(SOG + 1)")
                        X_pred['log_SOG'] = np.log1p(X_pred['SOG'].abs())
                        missing_cols.remove('log_SOG')
                        
                    if 'lw_ratio' in missing_cols and 'Length' in X_pred.columns and 'Width' in X_pred.columns:
                        print("   Création de lw_ratio = Length / (Width + 1e-6)")
                        X_pred['lw_ratio'] = X_pred['Length'] / (X_pred['Width'] + 1e-6)
                        missing_cols.remove('lw_ratio')
                        
                    # Vérifier les alias pour les coordonnées
                    if 'LAT' not in X_pred.columns and 'Latitude' in X_pred.columns:
                        X_pred['LAT'] = X_pred['Latitude']
                        if 'LAT' in missing_cols:
                            missing_cols.remove('LAT')
                            
                    if 'LON' not in X_pred.columns and 'Longitude' in X_pred.columns:
                        X_pred['LON'] = X_pred['Longitude']
                        if 'LON' in missing_cols:
                            missing_cols.remove('LON')
            
                # Vérifier à nouveau les colonnes manquantes
                if missing_cols:
                    print(f"   ERREUR: Impossible de créer les colonnes manquantes: {', '.join(missing_cols)}")
                    print(f"   Colonnes disponibles: {', '.join(X_pred.columns)}")
                    exit(1)
                # Sélectionner uniquement les colonnes attendues dans le bon ordre
                features = [col for col in expected_features if col in X_pred.columns]
                print(f"   Colonnes utilisées pour la prédiction: {', '.join(features)}")
                
                # Vérifier que nous avons toutes les colonnes nécessaires
                if len(features) != len(expected_features):
                    print(f"   ERREUR: Nombre de caractéristiques incorrect. Attendu: {len(expected_features)}, Trouvé: {len(features)}")
                    print(f"   Colonnes manquantes: {[col for col in expected_features if col not in features]}")
                    exit(1)
                    
                # Préparer les données d'entrée en conservant le DataFrame
                X_pred = X_pred[features].copy()
                print(f"   Forme des données d'entrée: {X_pred.shape}")
                
                # Afficher un aperçu des données
                print("\n   Aperçu des données d'entrée:")
                for i, col in enumerate(features):
                    print(f"   {i+1}. {col}: {X_pred.iloc[0, i]:.2f}" if pd.api.types.is_numeric_dtype(X_pred[col]) else f"   {i+1}. {col}: {X_pred.iloc[0, i]}")
                
                # Convertir les types de données si nécessaire
                for col in X_pred.select_dtypes(include=['object']).columns:
                    try:
                        X_pred[col] = pd.to_numeric(X_pred[col])
                    except ValueError:
                        print(f"   Impossible de convertir la colonne {col} en numérique")
                
                print("\n6. Données pour la prédiction:")
                for i, (_, row) in enumerate(sample.iterrows(), 1):
                    print(f"\n   Navire {i}:")
                    print(f"   MMSI: {row['MMSI']}")
                    print(f"   Nom: {row['VesselName']}")
                    print(f"   Type réel: {int(row['VesselType'])}")
                    print(f"   Caractéristiques: SOG={row['SOG']}, COG={row['COG']}, "
                          f"Longueur={row['Length']}, Largeur={row['Width']}, Tirant={row['Draft']}")
            
                # Faire les prédictions
                print("\n7. Prédictions en cours...")
                print(f"   Forme des données d'entrée: {X_pred.shape}")
                try:
                    # Afficher les types de données
                    print("   Types de données d'entrée:")
                    print(X_pred.dtypes)
                    
                    # Vérifier la présence de valeurs manquantes
                    if X_pred.isnull().any().any():
                        print("   ATTENTION: Valeurs manquantes détectées dans les données d'entrée")
                        print(X_pred.isnull().sum())
                    
                    # Faire la prédiction avec le modèle
                    print("   Début de la prédiction...")
                    y_pred = model.predict(X_pred)
                    print("   Prédiction terminée")
                    
                    # Afficher les probabilités si disponibles
                    y_proba = None
                    if hasattr(model, 'predict_proba'):
                        print("   Calcul des probabilités...")
                        y_proba = model.predict_proba(X_pred)
                        print("   Probabilités des classes calculées")
                    else:
                        print("   Le modèle ne fournit pas de probabilités")
                    
                    print("\n8. Résultats des prédictions:")
                    print("   " + "-"*90)
                    print(f"   {'MMSI':<15} {'Nom':<20} {'Type réel':<10} {'Type prédit':<12} "
                          f"{'Confiance':<10} {'Caractéristiques'}")
                    print("   " + "-"*90)
                    
                    for i, (_, row) in enumerate(sample.iterrows()):
                        pred = int(y_pred[i])
                        conf = f"{np.max(y_proba[i])*100:.1f}%" if y_proba is not None else "N/A"
                        
                        print(f"   {row['MMSI']:<15} {str(row['VesselName'])[:18]:<20} "
                              f"{int(row['VesselType']):<10} {pred:<12} {conf:<10} "
                              f"SOG={row['SOG']:.1f}, L={row['Length']:.1f}, l={row['Width']:.1f}")
            
                except Exception as e:
                    print(f"   ERREUR lors de la prédiction: {e}")
                    import traceback
                    traceback.print_exc()
            
            except Exception as e:
                print(f"\nERREUR: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        
        except Exception as e:
            print(f"\nERREUR CRITIQUE: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
