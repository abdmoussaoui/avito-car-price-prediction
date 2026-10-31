import axios from 'axios';
import type { CarData, CarOptions, FieldErrors, PredictionResult } from '../types/CarData';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

const fieldNames: Record<string, keyof CarData> = {
  Marque: 'marque', Modèle: 'modele', Localisation: 'localisation',
  Kilométrage: 'kilometrage', 'Année-Modèle': 'anneeModele',
  'Puissance fiscale': 'puissanceFiscale', 'Nombre de portes': 'nombreDePortes',
  État: 'etat', 'Première main': 'premiereMain', Équipements: 'equipements',
  'Boite de vitesses': 'boiteDeVitesses', 'Type de carburant': 'typeDeCarburant',
};

export class ApiError extends Error {
  constructor(message: string, public fields: FieldErrors = {}) { super(message); }
}

function parseError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (error.response?.status === 422 && Array.isArray(detail)) {
      const fields: FieldErrors = {};
      for (const item of detail) {
        const key = fieldNames[String(item.loc?.[1])];
        if (key) fields[key] = String(item.msg).replace(/^Value error, /, '');
      }
      return new ApiError('Vérifiez les champs indiqués pour obtenir votre estimation.', fields);
    }
    if (!error.response) {
      return new ApiError(error.code === 'ECONNABORTED'
        ? 'Le calcul prend plus de temps que prévu. Veuillez réessayer.'
        : 'Connexion au service impossible. Vérifiez que le backend est lancé sur le port 8000.');
    }
    if (typeof detail === 'string') return new ApiError(detail);
  }
  return error instanceof ApiError ? error : new ApiError('L’estimation est indisponible. Veuillez réessayer.');
}

export async function getCarOptions(signal?: AbortSignal): Promise<CarOptions> {
  try {
    return (await api.get<CarOptions>('/options', { signal })).data;
  } catch (error) { throw parseError(error); }
}

export async function predictCarPrice(car: CarData): Promise<PredictionResult> {
  try {
    const { data } = await api.post('/predict', {
      Marque: car.marque, Modèle: car.modele, Localisation: car.localisation,
      Kilométrage: car.kilometrage, 'Année-Modèle': car.anneeModele,
      'Puissance fiscale': `${car.puissanceFiscale} CV`,
      'Nombre de portes': car.nombreDePortes, État: car.etat,
      'Première main': car.premiereMain, Équipements: car.equipements,
      'Boite de vitesses': car.boiteDeVitesses, 'Type de carburant': car.typeDeCarburant,
    });
    if (typeof data.predicted_price !== 'number' || !Number.isFinite(data.predicted_price) || data.predicted_price <= 0) {
      throw new ApiError('Le service a renvoyé une estimation invalide. Veuillez réessayer.');
    }
    return { estimatedPrice: data.predicted_price };
  } catch (error) { throw parseError(error); }
}
