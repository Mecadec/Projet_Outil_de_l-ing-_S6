import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import plotly.express as px
import joblib

# Charger les données
df = pd.read_csv('After_Sort_sans_l&w_vide.csv')

colonnes = ['BaseDateTime','LAT', 'LON', 'SOG', 'COG', 'Heading', 'VesselType']
df = df[colonnes]