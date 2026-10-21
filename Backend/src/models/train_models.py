import time
import joblib
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor
from scipy.stats import randint, uniform

# Configuration
CONFIG = {
    "log_path": Path("../../logs/training.log"),
    "model_save_path": Path("../models_lib/"),
    "data_path": Path("../../data/preprocessing/clean_data.csv"),
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

def load_data() -> pd.DataFrame:
    """Load the preprocessed dataset."""
    data_path = CONFIG["data_path"]
    try:
        if not data_path.exists():
            logger.error(f"Data file does not exist at {data_path}")
            raise FileNotFoundError(f"Data file does not exist at {data_path}")
        
        df = pd.read_csv(data_path)
        logger.info(f"Loaded dataset from {data_path}, shape: {df.shape}")
        logger.info(f"Columns in dataset: {df.columns.tolist()}")
        
        # Verify expected columns
        expected_cols = [
            "Kilométrage", "Année-Modèle", "Puissance fiscale", "Nombre de portes",
            "État", "Première main", "Safety_Score", "Comfort_Score", "Tech_Score",
            "Loc_Marque_Modèle_encoded", "Prix",
            "Boite de vitesses_Automatique", "Boite de vitesses_Manuelle",
            "Type de carburant_Diesel", "Type de carburant_Electrique",
            "Type de carburant_Essence", "Type de carburant_Hybride", "Type de carburant_LPG"
        ]
        missing_cols = [col for col in expected_cols if col not in df.columns]
        extra_cols = [col for col in df.columns if col not in expected_cols]
        if missing_cols:
            logger.warning(f"Missing expected columns: {missing_cols}")
        if extra_cols:
            logger.info(f"Extra columns found: {extra_cols}")
        
        # Subsample for faster tuning (optional, comment out for full dataset)
        df = df.sample(frac=0.5, random_state=42)
        logger.info(f"Subsampled dataset shape: {df.shape}")
        
        # Handle missing values
        if df.isnull().any().any():
            logger.warning("Dataset contains missing values, dropping rows with NaN")
            df = df.dropna()
            logger.info(f"Shape after dropping NaN: {df.shape}")
        
        return df
    except FileNotFoundError as err:
        logger.error(f"Data file not found: {err}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"Data file is empty: {data_path}")
        raise
    except Exception as err:
        logger.error(f"Error loading data: {err}")
        raise

def evaluate_model(
    model,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    model_name: str,
) -> Tuple:
    """Train and evaluate a model, returning metrics in original price scale."""
    start_time = time.time()
    model.fit(X_train, y_train)
    training_time = time.time() - start_time
    logger.info(f"{model_name} trained in {training_time:.2f} seconds")

    y_train_pred_log = model.predict(X_train)
    y_test_pred_log = model.predict(X_test)

    y_train_pred = np.expm1(y_train_pred_log)
    y_test_pred = np.expm1(y_test_pred_log)
    y_train_actual = np.expm1(y_train)
    y_test_actual = np.expm1(y_test)

    train_mse = mean_squared_error(y_train_actual, y_train_pred)
    test_mse = mean_squared_error(y_test_actual, y_test_pred)
    train_r2 = r2_score(y_train_actual, y_train_pred)
    test_r2 = r2_score(y_test_actual, y_test_pred)

    logger.info(
        f"{model_name} - Train MSE (original scale): {train_mse:.4f}, "
        f"Test MSE (original scale): {test_mse:.4f}"
    )
    logger.info(
        f"{model_name} - Train R2 (original scale): {train_r2:.4f}, "
        f"Test R2 (original scale): {test_r2:.4f}"
    )

    return model, train_mse, test_mse, train_r2, test_r2

def tune_model(model, param_dist: Dict, X_train: pd.DataFrame, y_train: pd.Series, model_name: str):
    """Perform hyperparameter tuning using RandomizedSearchCV."""
    logger.info(f"Starting hyperparameter tuning for {model_name}...")
    start_time = time.time()
    random_search = RandomizedSearchCV(
        model,
        param_distributions=param_dist,
        n_iter=10,
        cv=3,
        scoring="neg_mean_squared_error",
        n_jobs=4,  # Limit to 4 cores to avoid overload
        verbose=2,
        random_state=42,
    )
    random_search.fit(X_train, y_train)
    tuning_time = time.time() - start_time
    logger.info(f"{model_name} tuning completed in {tuning_time:.2f} seconds")
    logger.info(f"{model_name} best params: {random_search.best_params_}")
    return random_search.best_estimator_

def get_feature_importance(model, feature_names: list, model_name: str) -> None:
    """Extract and log feature importance for tree-based models."""
    try:
        importances = model.feature_importances_
        feature_importance = pd.Series(importances, index=feature_names).sort_values(
            ascending=False
        )
        logger.info(f"{model_name} Feature Importance:")
        logger.info(feature_importance.to_string())
    except AttributeError:
        logger.info(f"{model_name} does not support feature importance")

def main():
    """Main function to train, tune, evaluate, and select the best model."""
    try:
        print("Starting training script...")
        logger.info("Starting training script...")

        model_save_path = CONFIG["model_save_path"]
        model_save_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Model save directory created/verified at: {model_save_path}")

        df = load_data()

        target = "Prix"
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
        categorical_cols = [
            "Boite de vitesses_Automatique", "Boite de vitesses_Manuelle",
            "Type de carburant_Diesel", "Type de carburant_Electrique",
            "Type de carburant_Essence", "Type de carburant_Hybride", "Type de carburant_LPG"
        ]
        features = numerical_cols + categorical_cols

        # Verify all features exist
        missing_cols = [col for col in features if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns in dataset: {missing_cols}")
            raise ValueError(f"Missing columns in dataset: {missing_cols}")

        X = df[features]
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        logger.info(f"Training set shape: {X_train.shape}, Test set shape: {X_test.shape}")

        models = {
            "Linear Regression": (LinearRegression(), {}),
            "Random Forest": (
                RandomForestRegressor(random_state=42),
                {
                    "n_estimators": randint(100, 200),
                    "max_depth": [10, 20],
                    "min_samples_split": randint(2, 5),
                },
            ),
        }

        try:
            from lightgbm import LGBMRegressor
            models["LightGBM"] = (
                LGBMRegressor(random_state=42),
                {
                    "n_estimators": randint(100, 200),
                    "max_depth": [10, 20],
                    "learning_rate": uniform(0.05, 0.15),
                },
            )
        except ImportError:
            logger.warning("LightGBM not installed, skipping LightGBM model.")

        results = {}

        for model_name, (model, param_dist) in models.items():
            logger.info(f"Training {model_name}...")
            if param_dist:
                tuned_model = tune_model(model, param_dist, X_train, y_train, model_name)
            else:
                tuned_model = model

            trained_model, train_mse, test_mse, train_r2, test_r2 = evaluate_model(
                tuned_model, X_train, X_test, y_train, y_test, model_name
            )

            results[model_name] = {
                "model": trained_model,
                "train_mse": train_mse,
                "test_mse": test_mse,
                "train_r2": train_r2,
                "test_r2": test_r2,
            }

            get_feature_importance(trained_model, features, model_name)

            model_path = model_save_path / f"{model_name.lower().replace(' ', '_')}_model.pkl"
            logger.info(f"Saving {model_name} model to: {model_path}")
            joblib.dump(trained_model, model_path)
            logger.info(f"{model_name} model saved successfully")

        best_model_name = min(results, key=lambda x: results[x]["test_mse"])
        best_model = results[best_model_name]["model"]
        logger.info(f"Best model: {best_model_name}")
        logger.info(f"Best model Test MSE: {results[best_model_name]['test_mse']:.4f}")
        logger.info(f"Best model Test R2: {results[best_model_name]['test_r2']:.4f}")

        best_model_path = model_save_path / "best_model.pkl"
        logger.info(f"Saving best model to: {best_model_path}")
        joblib.dump(best_model, best_model_path)
        logger.info(f"Best model saved successfully")

    except Exception as err:
        logger.error(f"Training failed: {str(err)}")
        raise

if __name__ == "__main__":
    main()