import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Union
from sklearn.metrics import r2_score

BASE_DIR_1 = Path(__file__).resolve().parent.parent  # goes from models/predict.py → src/
BASE_DIR_2 = Path(__file__).resolve().parent.parent.parent  # goes from models/predict.py → src/ root

# Configuration
CONFIG = {
    "scaler_path": BASE_DIR_1 / "models_lib" / "scaler.pkl",
    "model_path": BASE_DIR_1 / "models_lib" / "best_model.pkl",
    "mapping_path": BASE_DIR_2 / "data" / "preprocessing" / "loc_marque_modele_mapping.csv",
    "log_path": BASE_DIR_2 / "logs" / "prediction.log",
    "validation_data_path": BASE_DIR_2 / "data" / "validation_data.csv",  # Placeholder for validation data
}

# Setup logging
CONFIG["log_path"].parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=CONFIG["log_path"],
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Load mappings and configurations from preprocessing
CONFIG_PREPROCESS = {
    "cities_mapping": {
        "فاس": "Fès",
        "أكادير": "Agadir",
        "مراكش": "Marrakech",
        "القنيطرة": "Kénitra",
        "الدار البيضاء": "Casablanca",
        "Agadir Melloul": "Agadir",
    },
    "status_mapping": {
        "Neuf": 5,
        "Excellent": 4,
        "Très bon": 3,
        "Bon": 2,
        "Correct": 1,
        "Endommagé": 0,
        "Pour Pièces": -1,
    },
    "safety_features": [
        "ABS",
        "Airbags",
        "ESP",
        "Caméra de recul",
        "Radar de recul",
        "Régulateur de vitesse",
        "Limiteur de vitesse",
    ],
    "comfort_features": [
        "Climatisation",
        "Sièges cuir",
        "Toit ouvrant",
        "Vitres électriques",
        "Verrouillage centralisé à distance",
    ],
    "tech_features": [
        "CD/MP3/Bluetooth",
        "Système de navigation/GPS",
        "Ordinateur de bord",
        "Jantes aluminium",
    ],
}

class CarPricePredictor:
    """Class to handle car price predictions using a trained model."""

    def __init__(self):
        """Initialize the predictor by loading the model, scaler, and mappings, and compute R² score."""
        try:
            self.model = joblib.load(CONFIG["model_path"])
            logger.info(f"Loaded model from {CONFIG['model_path']}")
        except Exception as err:
            logger.error(f"Error loading model: {err}")
            raise

        try:
            self.scaler = joblib.load(CONFIG["scaler_path"])
            logger.info(f"Loaded scaler from {CONFIG['scaler_path']}")
        except Exception as err:
            logger.error(f"Error loading scaler: {err}")
            raise

        try:
            self.mapping_df = pd.read_csv(CONFIG["mapping_path"])
            logger.info(f"Loaded mapping from {CONFIG['mapping_path']}")
        except Exception as err:
            logger.error(f"Error loading mapping: {err}")
            raise

        # Compute and log R² score using validation data
        self._compute_r2_score()

    def _compute_r2_score(self):
        """Compute and log the R² score using validation data."""
        try:
            # Load validation data (assumes it has 'features' and 'target' columns)
            validation_data = pd.read_csv(CONFIG["validation_data_path"])
            if validation_data.empty:
                logger.warning("Validation data is empty, skipping R² score calculation")
                return

            # Prepare features (assuming validation_data has the same structure as input_data)
            X_val = self.preprocess_input(validation_data.iloc[0].to_dict())
            y_val = validation_data["target"].values  # Replace 'target' with your actual target column name

            # Make predictions
            y_pred_log = self.model.predict(X_val)
            y_pred = np.expm1(y_pred_log)  # Inverse transform log scale to original scale
            y_val = np.expm1(y_val)  # Inverse transform if target was log-scaled during training

            # Calculate R² score
            r2 = r2_score(y_val, y_pred)
            logger.info(f"R² Score on validation data: {r2:.4f}")
        except Exception as err:
            logger.error(f"Error computing R² score: {err}")

    def preprocess_input(self, input_data: Dict[str, Union[str, int, float, List[str]]]) -> pd.DataFrame:
        """Preprocess the input data to match the training format.

        Args:
            input_data (Dict): Input data for a car, e.g., {"Marque": "Toyota", "Modèle": "Corolla", ...}

        Returns:
            pd.DataFrame: Preprocessed features ready for prediction.
        """
        # Convert input to DataFrame
        df = pd.DataFrame([input_data])
        logger.info("Starting preprocessing of input data")

        # Standardize location
        df["Localisation"] = df["Localisation"].replace(CONFIG_PREPROCESS["cities_mapping"])

        # Encode État
        df["État"] = df["État"].map(CONFIG_PREPROCESS["status_mapping"]).fillna(4)

        # Encode Première main
        df["Première main"] = df["Première main"].map({"Oui": 1, "Non": 0}).fillna(1)

        # Process Kilométrage (if it's a range or string)
        if isinstance(df["Kilométrage"].iloc[0], str):
            if "Plus de 500 000" in df["Kilométrage"].iloc[0]:
                df["Kilométrage"] = 600000
            elif "-" in df["Kilométrage"].iloc[0]:
                km = [int(k.strip().replace(" ", "")) for k in df["Kilométrage"].iloc[0].split("-")]
                df["Kilométrage"] = np.mean(km)
            else:
                df["Kilométrage"] = int(df["Kilométrage"].iloc[0].strip().replace(" ", ""))
        df["Kilométrage"] = df["Kilométrage"].clip(lower=1000, upper=600000)

        # Process Année-Modèle
        df["Année-Modèle"] = pd.to_numeric(
            df["Année-Modèle"].astype(str).str.replace("1980 ou plus ancien", "1980"),
            errors="coerce",
        ).clip(lower=1980, upper=2025)

        # Process Puissance fiscale
        df["Puissance fiscale"] = (
            df["Puissance fiscale"]
            .astype(str)
            .str.replace("Plus de 41 CV", "41 CV")
            .str.replace("CV", "")
            .str.replace(r"\s+", "", regex=True)
        )
        df["Puissance fiscale"] = pd.to_numeric(df["Puissance fiscale"], errors="coerce").clip(
            lower=1, upper=41
        )

        # Process Nombre de portes
        df["Nombre de portes"] = pd.to_numeric(df["Nombre de portes"], errors="coerce")

        # Process Équipements to compute scores
        df["Équipements"] = df["Équipements"].fillna("")
        if isinstance(df["Équipements"].iloc[0], list):
            df["Équipements"] = df["Équipements"].apply(lambda x: ",".join(x))

        df["Safety_Score"] = df["Équipements"].apply(
            lambda x: sum(1 for feat in CONFIG_PREPROCESS["safety_features"] if feat in x)
        )
        df["Comfort_Score"] = df["Équipements"].apply(
            lambda x: sum(1 for feat in CONFIG_PREPROCESS["comfort_features"] if feat in x)
        )
        df["Tech_Score"] = df["Équipements"].apply(
            lambda x: sum(1 for feat in CONFIG_PREPROCESS["tech_features"] if feat in x)
        )

        # Target encoding for Loc_Marque_Modèle
        mapping = self.mapping_df[
            (self.mapping_df["Localisation"] == df["Localisation"].iloc[0])
            & (self.mapping_df["Marque"] == df["Marque"].iloc[0])
            & (self.mapping_df["Modèle"] == df["Modèle"].iloc[0])
        ]
        if not mapping.empty:
            df["Loc_Marque_Modèle_encoded"] = mapping["mean"].iloc[0]
        else:
            # Fallback to global mean if no mapping found
            df["Loc_Marque_Modèle_encoded"] = self.mapping_df["mean"].mean()
            logger.warning(
                f"No mapping found for {df['Localisation'].iloc[0]}, {df['Marque'].iloc[0]}, "
                f"{df['Modèle'].iloc[0]}. Using global mean for Loc_Marque_Modèle_encoded."
            )

        # One-hot encode categorical variables
        low_cardinality_cols = ["Boite de vitesses", "Type de carburant"]
        for column in low_cardinality_cols:
            encoded_cols = pd.get_dummies(df[column], prefix=column, dtype=int)
            df = pd.concat([df, encoded_cols], axis=1)
            df = df.drop(columns=[column])

        # Ensure all expected categorical columns are present in the correct order
        expected_cat_cols = [
            "Boite de vitesses_Automatique",
            "Boite de vitesses_Manuelle",
            "Type de carburant_Diesel",
            "Type de carburant_Electrique",
            "Type de carburant_Essence",
            "Type de carburant_Hybride",
            "Type de carburant_LPG",
        ]
        for col in expected_cat_cols:
            if col not in df.columns:
                df[col] = 0

        # Select features in the order expected by the model
        numerical_cols = [
            "Kilométrage",
            "Année-Modèle",
            "Puissance fiscale",
            "Nombre de portes",
            "État",
            "Première main",
            "Safety_Score",
            "Comfort_Score",
            "Tech_Score",
            "Loc_Marque_Modèle_encoded",
        ]
        features = numerical_cols + expected_cat_cols
        df = df[features]

        # Scale numerical features
        df[numerical_cols] = self.scaler.transform(df[numerical_cols])
        logger.info("Input data preprocessing completed")
        return df

    def predict(self, input_data: Dict[str, Union[str, int, float, List[str]]]) -> float:
        """Predict the car price based on input data.

        Args:
            input_data (Dict): Input data for a car, e.g., {"Marque": "Toyota", "Modèle": "Corolla", ...}

        Returns:
            float: Predicted car price in original scale (Dirhams).
        """
        try:
            # Preprocess the input
            X = self.preprocess_input(input_data)

            # Make prediction (in log scale)
            log_price = self.model.predict(X)[0]
            logger.info(f"Predicted log price: {log_price}")

            # Inverse transform to original scale
            price = np.expm1(log_price)
            logger.info(f"Predicted price: {price:.2f} DH")
            return price

        except Exception as err:
            logger.error(f"Prediction failed: {str(err)}")
            raise

def main():
    """Predict the price of a car using the trained model."""
    # Example input data for a car
    car_input = {
        "Marque": "Dacia",
        "Modèle": "logan",
        "Localisation": "Casablanca",
        "Kilométrage": "0 - 4 999",
        "Année-Modèle": 2025,
        "Puissance fiscale": "6 CV",
        "Nombre de portes": 3,
        "État": "Excellent",
        "Première main": "Oui",
        "Équipements": [
            "ABS",
            "Airbags",
            "CD/MP3/Bluetooth",
            "Caméra de recul",
            "Climatisation automatique",
            "ESP",
            "Jantes aluminium",
            "Limiteur de vitesse",
            "Radar de recul",
            "Régulateur de vitesse",
            "Système de navigation/GPS",
            "Verrouillage centralisé à distance",  
            "Vitres électriques"
        ],
        "Boite de vitesses": "Automatique",
        "Type de carburant": "Essence",
    }

    try:
        print("Initializing predictor...")
        predictor = CarPricePredictor()
        print("Predicting car price...")
        predicted_price = predictor.predict(car_input)
        print(f"Predicted car price: {predicted_price:.2f} DH")
    except Exception as err:
        print(f"Error during prediction: {err}")

if __name__ == "__main__":
    main()