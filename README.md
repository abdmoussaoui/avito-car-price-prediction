# AutoValeur · Estimation automobile au Maroc

Une application à page unique pour estimer le prix d’une voiture d’occasion en MAD à partir du modèle existant, entraîné sur les annonces Avito Maroc. Interface React / TypeScript, API FastAPI et modèle Random Forest sauvegardé.

## Lancement sous Windows

Prérequis : Python **3.11**, Node.js et npm. Ouvrez deux terminaux PowerShell dans le dossier du projet.

### Backend — terminal 1

Lors de la première installation :

```powershell
cd Backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Pour chaque lancement, depuis `Backend` :

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir src --reload --port 8000
```

API : http://localhost:8000/docs · Santé : http://localhost:8000/health

### Frontend — terminal 2

```powershell
cd frontend
npm install
npm run dev
```

Ouvrez http://localhost:5173. L’installation des dépendances n’est nécessaire qu’au premier lancement ou lorsque les dépendances changent. Gardez les deux terminaux ouverts. `Ctrl+C` arrête chaque serveur.

Aucune variable d’environnement ni service supplémentaire n’est requis. Le frontend utilise `http://localhost:8000` par défaut. Facultativement, `VITE_API_URL` dans `frontend/.env.local` peut définir une autre adresse API. Les origines frontend autorisées sont `http://localhost:5173` et `http://127.0.0.1:5173` ; gardez ce port pour le développement local.

Si le port 8000 est occupé, arrêtez l’ancienne instance du backend avant d’en lancer une autre. Si une erreur mentionne `pydantic_core._pydantic_core`, réinstallez les dépendances avec le Python de votre environnement :

```powershell
.\.venv\Scripts\python.exe -m pip install --force-reinstall -r requirements.txt
```

Les anciens fichiers Docker ne constituent pas le workflow local documenté ; ils nécessitent une configuration séparée.

## Prédiction réelle

La page charge les marques, modèles et villes depuis le mapping original via `GET /options`. Elle envoie les caractéristiques à `POST /predict` avec les clés françaises historiques. Le résultat affiché est exclusivement `predicted_price`, en dirhams : aucune fourchette, confiance ou recommandation artificielle n’est ajoutée. Le champ historique `estimated_tax` est conservé dans l’API pour compatibilité, mais ne constitue pas une sortie du modèle et n’est pas affiché.

Les fichiers requis, déjà présents dans le projet local, sont :

- `Backend/src/models_lib/best_model.pkl`
- `Backend/src/models_lib/scaler.pkl`
- `Backend/data/preprocessing/loc_marque_modele_mapping.csv`

Les fichiers `.pkl` sont ignorés par Git : une nouvelle copie du dépôt doit recevoir les artefacts originaux. Aucun réentraînement n’est lancé au démarrage.

Les transformations originales sont préservées, notamment le clipping du kilométrage entre 1 000 et 600 000 km, de l’année entre 1980 et 2025 et de la puissance entre 1 et 41 CV. Une année plus récente peut être saisie, mais reste traitée selon les limites originales du modèle ; la page le signale. Une combinaison ville / marque / modèle absente du mapping utilise la moyenne globale, comme auparavant.

## Architecture

```text
Backend/src/
  main.py                         Application, cycle de vie et CORS
  api/routes.py                   Routes HTTP
  api/schemas.py                  Validation des entrées et sorties
  models/loader.py                Chargement des artefacts originaux
  models/predict.py               Prédiction et évaluation existantes
  preprocessing/inference.py      Transformations originales de prédiction
  preprocessing/prediction_config.py  Définitions des caractéristiques
  preprocessing/preprocess_car_data.py  Pipeline original du dataset, inchangé
```

Les données brutes, données nettoyées, modèles sauvegardés et scripts d’entraînement sont conservés. Les métriques historiques restent dans `Backend/logs/training.log` : le meilleur modèle Random Forest y possède un R² de test de **0,7930**. Ce score global historique n’est pas une confiance par prédiction. Le fichier facultatif `Backend/data/validation_data.csv` n’est pas fourni ; son absence est journalisée et le calcul d’évaluation facultatif est ignoré sans empêcher les prédictions.

