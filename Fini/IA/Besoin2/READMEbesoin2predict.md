# Prédiction de Types de Navires avec l'IA

Ce projet permet de prédire le type de navire en fonction de ses caractéristiques physiques et de ses données de navigation, en utilisant un modèle d'apprentissage automatique pré-entraîné.

## Fonctionnalités

- Prédiction du type de navire basée sur des données AIS (Automatic Identification System)
- Affichage des résultats avec niveau de confiance
- Sélection aléatoire de navires pour la prédiction
- Gestion robuste des données manquantes

## Prérequis

- Python 3.10
- Bibliothèques Python listées dans `requirements.txt`

## Installation

1. Cloner le dépôt :
   ```bash
   git clone [URL_DU_DEPOT]
   cd Projet_Outil_de_l-ing-_S6/IA
   ```

2. Créer et activer un environnement virtuel :
   ```bash
   py -3.10 -m venv venv
   .\venv\Scripts\activate
   ```

3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

1. Placer votre fichier de données AIS (format CSV) dans le dossier du projet
2. Modifier si nécessaire les chemins dans le script `predict_with_pipeline.py`
3. Exécuter le script :
   ```bash
   py -3.10 predict_with_pipeline.py
   ```

## Structure des données

Le modèle attend un fichier CSV avec au moins les colonnes suivantes :
- `MMSI` : Identifiant unique du navire
- `VesselName` : Nom du navire
- `VesselType` : Type de navire (valeur cible)
- `SOG` : Vitesse sur le fond (Speed Over Ground)
- `COG` : Route sur le fond (Course Over Ground)
- `Length` : Longueur du navire
- `Width` : Largeur du navire
- `Draft` : Tirant d'eau
- `LAT` : Latitude
- `LON` : Longitude

## Fichiers

- `predict_with_pipeline.py` : Script principal de prédiction
- `model_vesseltypeHGB.pkl` : Modèle pré-entraîné
- `prediction_output.txt` : Fichier de sortie des prédictions
- `After_Sort_sans_l&w_vide.csv` : Exemple de jeu de données d'entrée

## Avertissements

- Le modèle a été entraîné avec scikit-learn 1.6.1
- Des avertissements peuvent apparaître si vous utilisez une version différente
- Les prédictions sont basées sur les données disponibles et peuvent ne pas être précises à 100%

## Auteur

Pol Nerisson


