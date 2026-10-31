export interface CarData {
  marque: string;
  modele: string;
  localisation: string;
  kilometrage: string;
  anneeModele: number;
  puissanceFiscale: number;
  nombreDePortes: number;
  etat: string;
  premiereMain: string;
  equipements: string[];
  boiteDeVitesses: string;
  typeDeCarburant: string;
}

export interface PredictionResult {
  estimatedPrice: number;
}

export interface CarOptions {
  brands: string[];
  models: Record<string, string[]>;
  locations: string[];
  equipment: string[];
  conditions: string[];
  fuels: string[];
  min_year: number;
  max_year: number;
  training_max_year: number;
}

export type FieldErrors = Partial<Record<keyof CarData, string>>;
