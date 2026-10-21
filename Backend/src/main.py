import logging
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from models.predict import CarPricePredictor, CONFIG_PREPROCESS
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
logging.basicConfig(
    filename="api.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Car Price Prediction API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

# Updated Pydantic model for input validation
class CarInput(BaseModel):
    Marque: str
    Modèle: str
    Localisation: str
    Kilométrage: str
    Année_Modèle: int = Field(..., alias="Année-Modèle", ge=1980, le=2025)
    Puissance_fiscale: str = Field(..., alias="Puissance fiscale")
    Nombre_de_portes: int = Field(..., alias="Nombre de portes", ge=1)
    État: str
    Première_main: str = Field(..., alias="Première main")
    Équipements: List[str]
    Boite_de_vitesses: str = Field(..., alias="Boite de vitesses")
    Type_de_carburant: str = Field(..., alias="Type de carburant")

    @validator("État")
    def validate_état(cls, v):
        valid_states = ["Neuf", "Excellent", "Très bon", "Bon", "Correct", "Endommagé", "Pour Pièces", ""]
        if v not in valid_states:
            raise ValueError(f"État must be one of {valid_states}")
        return v

    @validator("Première_main")
    def validate_première_main(cls, v):
        if v not in ["Oui", "Non"]:
            raise ValueError("Première main must be 'Oui' or 'Non'")
        return v

    @validator("Boite_de_vitesses")
    def validate_boite_de_vitesses(cls, v):
        if v not in ["Automatique", "Manuelle"]:
            raise ValueError("Boite de vitesses must be 'Automatique' or 'Manuelle'")
        return v

    @validator("Type_de_carburant")
    def validate_type_de_carburant(cls, v):
        valid_fuels = ["Diesel", "Essence", "Electrique", "Hybride", "LPG"]
        if v not in valid_fuels:
            raise ValueError(f"Type de carburant must be one of {valid_fuels}")
        return v

    @validator("Équipements")
    def validate_équipements(cls, v):
        valid_equipments = (
            CONFIG_PREPROCESS["safety_features"] +
            CONFIG_PREPROCESS["comfort_features"] +
            CONFIG_PREPROCESS["tech_features"] +
            ["Climatisation automatique", "Contrôle de traction", "Intérieur cuir sur mesure", 
             "Jantes en alliage", "Système audio haut de gamme", "Toit en carbone"]
        )
        for equip in v:
            if equip not in valid_equipments:
                raise ValueError(f"Équipement '{equip}' must be one of {valid_equipments}")
        return v

# Pydantic model for prediction response
class PredictionResponse(BaseModel):
    predicted_price: float
    estimated_tax: float

# Pydantic model for recommendations response
class RecommendationResponse(BaseModel):
    recommendations: List[str]

# Initialize predictor
predictor = CarPricePredictor()

@app.post("/predict", response_model=PredictionResponse)
async def predict_price(car: CarInput):
    """Predict the price of a car based on its features and calculate tax."""
    try:
        print(f"Received request body: {car.dict(by_alias=True)}")
        # Convert Pydantic model to dict
        car_dict = car.dict(by_alias=True)
        # Predict price
        price = predictor.predict(car_dict)
        # Calculate tax (10% rate for luxury cars, as used in frontend)
        tax_rate = 0.10
        tax = price * tax_rate
        return {"predicted_price": price, "estimated_tax": tax}
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(car: CarInput):
    """Return recommendations for buying the car."""
    try:
        return {"recommendations": []}
    except Exception as e:
        logger.error(f"Failed to fetch recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recommendations: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}