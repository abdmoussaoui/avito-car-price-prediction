"""Inference service using the existing trained model and saved scaler."""
import logging
from typing import Dict, List, Union

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from models.loader import CONFIG, load_artifacts
from preprocessing.inference import InferencePreprocessor
from preprocessing.prediction_config import CONFIG_PREPROCESS

logger = logging.getLogger(__name__)


class CarPricePredictor:
    def __init__(self):
        artifacts = load_artifacts()
        self.model = artifacts.model
        self.scaler = artifacts.scaler
        self.mapping_df = artifacts.mapping
        self.preprocessor = InferencePreprocessor(self.scaler, self.mapping_df)
        self._compute_r2_score()

    def preprocess_input(self, input_data):
        return self.preprocessor.preprocess_input(input_data)

    def _compute_r2_score(self):
        """Compute and log the R² score using validation data."""
        if not CONFIG["validation_data_path"].is_file():
            logger.info("Optional validation dataset is absent; historical training metrics are unchanged")
            return
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
