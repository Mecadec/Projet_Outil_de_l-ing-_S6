import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import plotly.express as px
import joblib


# Charger les données
df = pd.read_csv('Besoin1/After_Sort_sans_l&w_vide.csv')

# Sélection des colonnes pertinentes
colonnes = ['LAT', 'LON', 'SOG', 'COG', 'Heading', 'VesselType']
df = df[colonnes]

# Suppression des lignes contenant des valeurs manquantes
df = df.dropna()

# Encodage de la variable catégorielle 'VesselType' si elle est utilisée
if 'VesselType' in df.columns:
    le = LabelEncoder()
    df['VesselType'] = le.fit_transform(df['VesselType'])

# Normalisation des données
scaler = StandardScaler()
X = scaler.fit_transform(df)

print("Aperçu des données après sélection et nettoyage :")
print(df.head())

print("\nNombre de valeurs manquantes :", df.isnull().sum().sum())

print("\nForme des données normalisées :", X.shape)
print("Aperçu des données normalisées :")
print(X[:5])

# --- Clustering sur un échantillon pour accélérer ---
sample_size = 20000
if len(X) > sample_size:
    X_sample = X[:sample_size]
    df_sample_cluster = df.iloc[:sample_size].copy()
else:
    X_sample = X
    df_sample_cluster = df.copy()

n_clusters = 4  # Choix optimal basé sur les courbes de métriques
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
labels = kmeans.fit_predict(X_sample)

# Ajout des labels au DataFrame d'échantillon
df_sample_cluster['cluster'] = labels

print("\nRépartition des navires par cluster (échantillon) :")
print(df_sample_cluster['cluster'].value_counts())

# Évaluation des clusters sur l'échantillon
sil_score = silhouette_score(X_sample, labels)
calinski_score = calinski_harabasz_score(X_sample, labels)
davies_score = davies_bouldin_score(X_sample, labels)

print(f"\nSilhouette Score : {sil_score:.3f}")
print(f"Calinski-Harabasz Index : {calinski_score:.3f}")
print(f"Davies-Bouldin Index : {davies_score:.3f}")

# Visualisation sur carte (échantillon pour éviter les bugs de performance)
try:
    df_visu = df_sample_cluster.sample(n=4, random_state=42) if len(df_sample_cluster) > 5000 else df_sample_cluster
    fig = px.scatter_mapbox(
        df_visu,
        lat="LAT",
        lon="LON",
        color="cluster",
        hover_data=["SOG", "COG", "Heading", "VesselType"],
        zoom=4,
        mapbox_style="carto-positron",
        title="Clustering des navires sur la carte (échantillon)"
    )
    fig.show()
except Exception as e:
    print("Erreur lors de la visualisation Plotly :", e)

# Sauvegarde du modèle et du scaler
joblib.dump(kmeans, "Besoin1/kmeans_model.joblib")
joblib.dump(scaler, "Besoin1/scaler_model.joblib")
print("\nModèle et scaler sauvegardés.")

# Script pour prédire le cluster d'un nouveau navire
def predict_cluster(new_data_dict):
    """
    new_data_dict : dict avec les clés ['LAT', 'LON', 'SOG', 'COG', 'Heading', 'VesselType']
    """
    # Charger scaler et modèle
    scaler = joblib.load("Besoin1/scaler_model.joblib")
    kmeans = joblib.load("Besoin1/kmeans_model.joblib")
    # Transformer les données en DataFrame
    new_df = pd.DataFrame([new_data_dict])
    # Encoder VesselType si besoin
    if 'VesselType' in new_df.columns:
        le = LabelEncoder()
        # Adapter l'encodage à votre cas réel (ici, simple fit sur l'ensemble des types connus)
        new_df['VesselType'] = le.fit(df['VesselType']).transform(new_df['VesselType'])
    # Normaliser
    X_new = scaler.transform(new_df)
    # Prédire
    cluster = kmeans.predict(X_new)
    return cluster[0]

# Exemple d'utilisation :
exemple_navire = {'LAT': 29.0, 'LON': -89.0, 'SOG': 10.0, 'COG': 200.0, 'Heading': 200, 'VesselType': 60}
print("Cluster prédit :", predict_cluster(exemple_navire))

# Merci de valider cette étape avant de passer à l'évaluation des clusters (métriques).

# --- Application du modèle à toute la base ---
# Prédire le cluster pour chaque navire de la base complète
df['cluster'] = kmeans.predict(X)

print("\nRépartition des clusters sur toute la base :")
print(df['cluster'].value_counts())

print("\nCaractéristiques moyennes par cluster (sur toute la base) :")
print(df.groupby('cluster')[['LAT', 'LON', 'SOG', 'COG', 'Heading', 'VesselType']].mean())