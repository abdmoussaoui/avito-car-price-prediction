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
  priceRange: {
    min: number;
    max: number;
  };
  confidence: number;
  estimatedTax: number;
}
