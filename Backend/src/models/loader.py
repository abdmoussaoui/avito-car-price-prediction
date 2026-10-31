"""Load trusted project artifacts once during application startup."""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import joblib
import pandas as pd

SRC_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = SRC_DIR.parent
CONFIG = {
    "scaler_path": SRC_DIR / "models_lib" / "scaler.pkl",
    "model_path": SRC_DIR / "models_lib" / "best_model.pkl",
    "mapping_path": BACKEND_DIR / "data" / "preprocessing" / "loc_marque_modele_mapping.csv",
    "log_path": BACKEND_DIR / "logs" / "prediction.log",
    "validation_data_path": BACKEND_DIR / "data" / "validation_data.csv",
}
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ModelArtifacts:
    model: Any
    scaler: Any
    mapping: pd.DataFrame

def load_artifacts() -> ModelArtifacts:
    for key in ("model_path", "scaler_path", "mapping_path"):
        if not CONFIG[key].is_file():
            raise RuntimeError(f"Required prediction artifact is missing: {CONFIG[key]}")
    artifacts = ModelArtifacts(
        model=joblib.load(CONFIG["model_path"]),
        scaler=joblib.load(CONFIG["scaler_path"]),
        mapping=pd.read_csv(CONFIG["mapping_path"]),
    )
    logger.info("Loaded original model, scaler and location/brand/model mapping")
    return artifacts
