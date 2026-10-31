"""Thin routes: validate input, invoke the service, return a stable contract."""
import logging
import math
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Request
from api.schemas import CarInput, EQUIPMENT, PredictionResponse
from models.predict import CarPricePredictor
from preprocessing.prediction_config import CONFIG_PREPROCESS

router = APIRouter()
logger = logging.getLogger(__name__)

def get_predictor(request: Request) -> CarPricePredictor:
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(503, "Le service d’estimation est temporairement indisponible.")
    return predictor

@router.post("/predict", response_model=PredictionResponse)
def predict_price(car: CarInput, predictor: CarPricePredictor = Depends(get_predictor)):
    try:
        price = float(predictor.predict(car.model_dump(by_alias=True)))
        if not math.isfinite(price) or price <= 0:
            raise ValueError("Model returned an invalid price")
        return {"predicted_price": price, "estimated_tax": price * 0.10}
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(500, "L’estimation n’a pas pu aboutir. Réessayez dans un instant.") from exc

@router.get("/options")
def get_options(predictor: CarPricePredictor = Depends(get_predictor)):
    mapping = predictor.mapping_df
    models = {
        str(brand): sorted(group["Modèle"].dropna().unique().tolist(), key=str.casefold)
        for brand, group in mapping.groupby("Marque")
    }
    return {
        "brands": sorted(models, key=str.casefold), "models": models,
        "locations": sorted(mapping["Localisation"].dropna().unique().tolist(), key=str.casefold),
        "equipment": EQUIPMENT,
        "conditions": list(CONFIG_PREPROCESS["status_mapping"]),
        "fuels": ["Diesel", "Essence", "Electrique", "Hybride", "LPG"],
        "min_year": 1980, "max_year": date.today().year, "training_max_year": 2025,
    }

@router.get("/health")
def health_check(predictor: CarPricePredictor = Depends(get_predictor)):
    return {"status": "healthy"}

@router.get("/recommendations", deprecated=True)
def get_recommendations():
    """Compatibility endpoint; the model does not produce recommendations."""
    return {"recommendations": []}
