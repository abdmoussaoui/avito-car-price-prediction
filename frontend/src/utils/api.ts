import axios from "axios";
import { CarData } from "../types/CarData";

const API_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const predictCarPrice = async (carData: CarData) => {
  try {
    const formattedData = {
      Marque: carData.marque,
      Modèle: carData.modele,
      Localisation: carData.localisation,
      Kilométrage: carData.kilometrage,
      "Année-Modèle": carData.anneeModele,
      "Puissance fiscale": `${carData.puissanceFiscale} CV`,
      "Nombre de portes": carData.nombreDePortes,
      État: carData.etat,
      "Première main": carData.premiereMain,
      Équipements: carData.equipements,
      "Boite de vitesses": carData.boiteDeVitesses,
      "Type de carburant": carData.typeDeCarburant,
    };

    console.log("✅ Données envoyées au backend:", formattedData);

    const response = await api.post("/predict", formattedData);
    return {
      estimatedPrice: response.data.predicted_price,
      priceRange: {
        min: response.data.predicted_price * 0.9,
        max: response.data.predicted_price * 1.1,
      },
      confidence: 0.95,
      estimatedTax: response.data.estimated_tax,
    };
  } catch (error) {
    console.error("Error predicting car price:", error);
    throw error;
  }
};

export const getRecommendations = async () => {
  try {
    const response = await api.get("/recommendations");
    return response.data.recommendations;
  } catch (error) {
    console.error("Error fetching recommendations:", error);
    throw error;
  }
};
