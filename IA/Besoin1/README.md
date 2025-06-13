# Besoin 1: Clustering des Navires

## Description
Ce projet implémente un système de clustering pour regrouper automatiquement les navires selon des schémas de navigation similaires. L'objectif est d'identifier des comportements typiques, détecter des anomalies ou optimiser les itinéraires.

## Fonctionnalités
1. **Préparation des données** : Nettoyage, encodage des variables catégorielles et normalisation.
2. **Clustering** : Utilisation de l'algorithme KMeans pour regrouper les navires.
3. **Évaluation des clusters** : Calcul des métriques de clustering (Silhouette Score, Calinski-Harabasz Index, Davies-Bouldin Index).
4. **Visualisation** : Affichage des clusters sur une carte interactive.
5. **Prédiction** : Script pour prédire le cluster d'un nouveau navire à partir de ses caractéristiques.

## Structure du projet
- **Besoin1.py** : Script principal contenant les fonctions de clustering et de prédiction.
- **Besoin.ipynb** : Notebook interactif pour l'exploration des données et le développement.
- **Modèles sauvegardés** :
  - `scaler_model.joblib` : Modèle de normalisation.
  - `pca_model.joblib` : Modèle de réduction de dimensionnalité.
  - `kmeans_model.joblib` : Modèle de clustering.
  - `labelencoder_vesseltype.joblib` : Encodeur pour la variable `VesselType`.

## Utilisation
### Exécution du script principal
Pour prédire le cluster d'un nouveau navire, utilisez la commande suivante :
```bash
python Besoin1.py --LON <longitude> --LAT <latitude> --SOG <speed_over_ground> --COG <course_over_ground> --Length <length> --Width <width> --Draft <draft> --Heading <heading> --VesselType <vessel_type>
```

### Exemple :
```bash
python Besoin1.py --LON 10 --LAT 20 --SOG 5.0 --COG 180.0 --Length 100 --Width 20 --Draft 5 --Heading 90 --VesselType 60
```

### Notebook interactif
Le fichier `Besoin.ipynb` contient les étapes détaillées pour :
- Charger et préparer les données.
- Effectuer le clustering.
- Visualiser les résultats.

## Prérequis
- Python 3.8+
- Bibliothèques nécessaires :
  - `pandas`
  - `numpy`
  - `scikit-learn`
  - `plotly`
  - `matplotlib`
  - `joblib`

## Résultats
Les clusters obtenus permettent de regrouper les navires selon leurs caractéristiques de navigation. Ces résultats peuvent être utilisés pour :
- Optimiser les itinéraires.
- Identifier des anomalies.
- Étudier les comportements typiques des navires.

## Auteur
Projet réalisé par Gauth dans le cadre du module **Outil de l'ingénieur S6**.

## Licence
Ce projet est sous licence MIT. Vous êtes libre de l'utiliser et de le