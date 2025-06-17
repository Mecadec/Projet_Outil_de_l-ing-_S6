import pandas as pd # Pour la manipulation des données
from sklearn.preprocessing import StandardScaler, LabelEncoder # Pour la normalisation et l'encodage
from sklearn.cluster import KMeans # Pour le clustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score # Pour les métriques de clustering
from sklearn.decomposition import PCA # Pour la réduction de dimensionnalité
import plotly.express as px # Pour la visualisation sur carte
import joblib # Pour la sauvegarde des modèles
import matplotlib.pyplot as plt # Pour la visualisation des scores
import numpy as np # Pour la visualisation des scores
import argparse # Pour la gestion des arguments en ligne de commande

def load_data(file_path):
    """
    Charge les données à partir d'un fichier CSV.
    file_path : str, chemin vers le fichier CSV
    """
    df = pd.read_csv(file_path)
    return df

def predict_cluster(new_data_dict):
    """
    Prédit le cluster d'un nouveau navire à partir de ses caractéristiques.
    new_data_dict : dict avec les clés ['LAT', 'LON', 'SOG', 'COG', 'Length', 'Width', 'Draft', 'Heading', 'VesselType']
    """
    scaler = joblib.load("scaler_model.joblib")
    pca = joblib.load("pca_model.joblib")
    kmeans = joblib.load("kmeans_model.joblib")
    le = joblib.load("labelencoder_vesseltype.joblib")
    new_df = pd.DataFrame([new_data_dict])
    if 'VesselType' in new_df.columns:
        if new_df['VesselType'].iloc[0] not in le.classes_:
            raise ValueError(f"VesselType inconnu : {new_df['VesselType'].iloc[0]}. Valeurs connues : {list(le.classes_)}")
        new_df['VesselType'] = le.transform(new_df['VesselType'])
    # S'assurer que les colonnes sont dans le bon ordre et qu'il n'y a pas VesselType_original
    model_features = ['LAT', 'LON', 'SOG', 'COG', 'Length', 'Width', 'Draft', 'Heading', 'VesselType']
    X_new = scaler.transform(new_df[model_features])
    X_new_pca = pca.transform(X_new)
    cluster = kmeans.predict(X_new_pca)
    return cluster[0]


# 11. Prédiction du cluster pour un nouveau navire via les arguments en ligne de commande
argparse = argparse.ArgumentParser(description="Clustering des navires")
argparse.add_argument('--LON', type=int, help="Données du nouveau navire au format JSON")
argparse.add_argument('--LAT', type=int, help="Données du nouveau navire au format JSON")
argparse.add_argument('--SOG', type=float, help="Données du nouveau navire au format JSON")
argparse.add_argument('--COG', type=float, help="Données du nouveau navire au format JSON")
argparse.add_argument('--Length', type=int, help="Données du nouveau navire au format JSON")
argparse.add_argument('--Width', type=int, help="Données du nouveau navire au format JSON")
argparse.add_argument('--Draft', type=int, help="Données du nouveau navire au format JSON")
argparse.add_argument('--Heading', type=int, help="Données du nouveau navire au format JSON")
argparse.add_argument('--VesselType', type=int, help="Données du nouveau navire au format JSON")
args = argparse.parse_args()

if args.LON is not None and args.LAT is not None and args.SOG is not None and args.COG is not None and args.Length is not None and args.Width is not None and args.Draft is not None and args.Heading is not None and args.VesselType is not None:
    new_navire = {
        'LON': args.LON,
        'LAT': args.LAT,
        'SOG': args.SOG,
        'COG': args.COG,
        'Length': args.Length,
        'Width': args.Width,
        'Draft': args.Draft,
        'Heading': args.Heading,
        'VesselType': args.VesselType
    }
    print("Cluster prédit pour le nouveau navire :", predict_cluster(new_navire))

