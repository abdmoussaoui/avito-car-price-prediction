"""Original inference transformations; feature order and clipping are preserved."""
import logging
from typing import Dict, List, Union

import numpy as np
import pandas as pd

from preprocessing.prediction_config import CONFIG_PREPROCESS

logger = logging.getLogger(__name__)


class InferencePreprocessor:
    def __init__(self, scaler, mapping_df):
        self.scaler = scaler
        self.mapping_df = mapping_df

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

