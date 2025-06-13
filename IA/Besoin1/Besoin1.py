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

# 1. Chargement et préparation des données
df = pd.read_csv('Besoin1/After_Sort.csv')
colonnes = ['LAT', 'LON', 'SOG', 'COG', 'Length', 'Width', 'Draft', 'Heading', 'VesselType']
df = df[colonnes]
df['VesselType_original'] = df['VesselType']  # Sauvegarde la valeur originale pour affichage
df = df.dropna()  # Suppression des lignes incomplètes

# 2. Encodage de la variable catégorielle VesselType
if 'VesselType' in df.columns:
    le = LabelEncoder()
    df['VesselType'] = le.fit_transform(df['VesselType'])

# 3. Préparation du DataFrame pour le modèle (on retire VesselType_original)
model_features = ['LAT', 'LON', 'SOG', 'COG', 'Length', 'Width', 'Draft', 'Heading', 'VesselType']
df_model = df[model_features]

# 4. Normalisation des données
scaler = StandardScaler()
X = scaler.fit_transform(df_model)

# 5. Réduction de dimensionnalité avec PCA
pca = PCA(n_components=5)
X_pca = pca.fit_transform(X)
print("Forme des données après PCA :", X_pca.shape)
print("Variance totale expliquée par PCA :", pca.explained_variance_ratio_.sum())

# 5. Recherche du nombre optimal de clusters
calcul_scores = input("Voulez-vous calculer les scores de clustering pour chaque nombre de clusters ? (oui/non) : ").strip().lower()
if calcul_scores == "oui":
    range_n_clusters = range(2, 11)
    silhouette_scores, calinski_scores, davies_scores = [], [], []
    score_sample_size = 50000
    for n in range_n_clusters:
        print(f"Calcul des scores pour {n} clusters...")
        kmeans_tmp = KMeans(n_clusters=n, random_state=42)
        labels_tmp = kmeans_tmp.fit_predict(X_pca)
        # Sous-échantillonnage pour accélérer le calcul des scores
        if len(X_pca) > score_sample_size:
            idx = pd.Series(range(len(X_pca))).sample(n=score_sample_size, random_state=42).values
            X_score = X_pca[idx]
            labels_score = [labels_tmp[i] for i in idx]
        else:
            X_score = X_pca
            labels_score = labels_tmp
        if len(set(labels_score)) < 2:
            silhouette_scores.append(np.nan)
            calinski_scores.append(np.nan)
            davies_scores.append(np.nan)
        else:
            silhouette_scores.append(silhouette_score(X_score, labels_score))
            calinski_scores.append(calinski_harabasz_score(X_score, labels_score))
            davies_scores.append(davies_bouldin_score(X_score, labels_score))
    # Affichage des scores
    fig, axs = plt.subplots(1, 3, figsize=(18, 5))
    axs[0].plot(range_n_clusters, silhouette_scores, marker='o', color='skyblue')
    axs[0].set_xlabel("Nombre de clusters")
    axs[0].set_ylabel("Silhouette Score")
    axs[0].set_title("Silhouette Score")
    axs[0].grid(True)
    axs[1].plot(range_n_clusters, calinski_scores, marker='o', color='orange')
    axs[1].set_xlabel("Nombre de clusters")
    axs[1].set_ylabel("Calinski-Harabasz Index")
    axs[1].set_title("Calinski-Harabasz Index")
    axs[1].grid(True)
    axs[2].plot(range_n_clusters, davies_scores, marker='o', color='green')
    axs[2].set_xlabel("Nombre de clusters")
    axs[2].set_ylabel("Davies-Bouldin Index")
    axs[2].set_title("Davies-Bouldin Index")
    axs[2].grid(True)
    plt.suptitle("Scores de clustering en fonction du nombre de clusters", fontsize=16)
    plt.tight_layout(rect=[0, 0.08, 1, 0.95])
    plt.show()

# 6. Clustering principal (nombre de clusters fixé à 3)
n_clusters = 3
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
labels = kmeans.fit_predict(X_pca)
df['cluster'] = labels  # Ajoute la colonne cluster à df (qui contient aussi VesselType_original)

# 7. Évaluation des clusters (sous-échantillonnage si trop gros)
score_full_size = 10000
if len(X_pca) > score_full_size:
    idx_full = pd.Series(range(len(X_pca))).sample(n=score_full_size).values
    X_pca_score = X_pca[idx_full]
    labels_score = [labels[i] for i in idx_full]
else:
    X_pca_score = X_pca
    labels_score = labels

sil_score = silhouette_score(X_pca_score, labels_score)
calinski_score = calinski_harabasz_score(X_pca_score, labels_score)
davies_score = davies_bouldin_score(X_pca_score, labels_score)

print("\n--- Scores de réussite du clustering (toute la base) ---")
print(f"Silhouette Score : {sil_score:.3f}")
print(f"Calinski-Harabasz Index : {calinski_score:.3f}")
print(f"Davies-Bouldin Index : {davies_score:.3f}")

# 8. Visualisation sur carte (échantillon pour performance)
try:
    df_visu = df.sample(n=10000) if len(df) > 5000 else df
    import plotly.io as pio
    pio.renderers.default = "browser"  # Ouvre la carte dans le navigateur par défaut
    fig = px.scatter_mapbox(
        df_visu,
        lat="LAT",
        lon="LON",
        color="cluster",
        hover_data=["SOG", "COG", "Length", "Width", "Draft", "Heading", "VesselType", "VesselType_original"],
        zoom=4,
        mapbox_style="carto-positron",
        title="Clustering des navires sur la carte (toute la base)",
    )
    fig.show()
except Exception as e:
    print("Erreur lors de la visualisation Plotly :", e)

# 9. Sauvegarde des modèles

joblib.dump(kmeans, "Besoin1/kmeans_model.joblib")
joblib.dump(scaler, "Besoin1/scaler_model.joblib")
joblib.dump(le, "Besoin1/labelencoder_vesseltype.joblib")
joblib.dump(pca, "Besoin1/pca_model.joblib")
print("\nModèle et scaler sauvegardés.")

# 10. Fonction de prédiction pour un nouveau navire
def predict_cluster(new_data_dict):
    """
    Prédit le cluster d'un nouveau navire à partir de ses caractéristiques.
    new_data_dict : dict avec les clés ['LAT', 'LON', 'SOG', 'COG', 'Length', 'Width', 'Draft', 'Heading', 'VesselType']
    """
    scaler = joblib.load("Besoin1/scaler_model.joblib")
    pca = joblib.load("Besoin1/pca_model.joblib")
    kmeans = joblib.load("Besoin1/kmeans_model.joblib")
    le = joblib.load("Besoin1/labelencoder_vesseltype.joblib")
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

# Pour lancer la prédiction avec argparse en ligne de commande :
# 