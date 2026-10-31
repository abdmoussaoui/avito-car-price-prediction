"""Public request contract retaining the existing French JSON keys."""
import re
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from preprocessing.prediction_config import CONFIG_PREPROCESS

LEGACY_EQUIPMENT = [
    "Climatisation automatique", "Contrôle de traction", "Intérieur cuir sur mesure",
    "Jantes en alliage", "Système audio haut de gamme", "Toit en carbone",
]
EQUIPMENT = (CONFIG_PREPROCESS["safety_features"] + CONFIG_PREPROCESS["comfort_features"]
             + CONFIG_PREPROCESS["tech_features"])

class CarInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, allow_inf_nan=False)
    Marque: str = Field(min_length=1, max_length=100)
    Modèle: str = Field(min_length=1, max_length=100)
    Localisation: str = Field(min_length=1, max_length=100)
    Kilométrage: str = Field(min_length=1, max_length=40)
    Année_Modèle: int = Field(alias="Année-Modèle", ge=1980, le=date.today().year)
    Puissance_fiscale: str = Field(alias="Puissance fiscale", min_length=1, max_length=30)
    Nombre_de_portes: int = Field(alias="Nombre de portes", ge=1, le=7)
    État: Literal["Neuf", "Excellent", "Très bon", "Bon", "Correct", "Endommagé", "Pour Pièces", ""]
    Première_main: Literal["Oui", "Non"] = Field(alias="Première main")
    Équipements: list[str] = Field(max_length=30)
    Boite_de_vitesses: Literal["Automatique", "Manuelle"] = Field(alias="Boite de vitesses")
    Type_de_carburant: Literal["Diesel", "Essence", "Electrique", "Hybride", "LPG"] = Field(alias="Type de carburant")

    @field_validator("Kilométrage", mode="before")
    @classmethod
    def validate_mileage(cls, value):
        if isinstance(value, int) and not isinstance(value, bool):
            value = str(value)
        if not isinstance(value, str):
            raise ValueError("Saisissez un kilométrage valide en km.")
        value = value.strip().replace("\u202f", " ").replace("\u00a0", " ")
        if value in ("500 000+", "500000+", "Plus de 500 000"):
            return "Plus de 500 000"
        compact = value.replace(" ", "")
        if not re.fullmatch(r"\d{1,7}(-\d{1,7})?", compact):
            raise ValueError("Saisissez un nombre de km ou une plage comme 50 000 - 74 999.")
        bounds = [int(part) for part in compact.split("-")]
        if max(bounds) > 1_000_000 or bounds[0] > bounds[-1]:
            raise ValueError("Le kilométrage doit être compris entre 0 et 1 000 000 km.")
        return value

    @field_validator("Puissance_fiscale")
    @classmethod
    def validate_power(cls, value):
        if value == "Plus de 41 CV":
            return value
        match = re.fullmatch(r"(\d{1,2})\s*(?:CV)?", value, flags=re.IGNORECASE)
        if not match or not 1 <= int(match.group(1)) <= 41:
            raise ValueError("La puissance fiscale doit être comprise entre 1 et 41 CV.")
        return f"{int(match.group(1))} CV"

    @field_validator("Équipements")
    @classmethod
    def validate_equipment(cls, values):
        for value in values:
            if value not in EQUIPMENT + LEGACY_EQUIPMENT:
                raise ValueError(f"Équipement non reconnu : {value}.")
        return list(dict.fromkeys(values))

class PredictionResponse(BaseModel):
    predicted_price: float = Field(gt=0, allow_inf_nan=False)
    # Legacy fixed calculation retained for API compatibility, not displayed as a model output.
    estimated_tax: float = Field(ge=0, allow_inf_nan=False)
