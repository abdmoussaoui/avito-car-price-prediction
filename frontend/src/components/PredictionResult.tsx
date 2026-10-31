import { ArrowUpRight } from 'lucide-react';
import type { CarData, PredictionResult } from '../types/CarData';
import { formatPrice } from '../utils/formatters';

interface Props {
  result: PredictionResult | null;
  submittedCar: CarData | null;
  loading: boolean;
  onReset: () => void;
}

export default function PredictionResultDisplay({ result, submittedCar, loading, onReset }: Props) {
  return (
    <div className="valuation-content" aria-live="polite" aria-atomic="true" aria-busy={loading}>
      {loading ? <div className="loading-state">
        <p>Une valeur se dessine.</p><div className="loading-track"><span /></div>
      </div> : result && submittedCar ? <div className="result-reveal">
        <p className="result-vehicle">{submittedCar.marque} {submittedCar.modele}<span>/</span>{submittedCar.anneeModele}</p>
        <div className="result-price">{formatPrice(result.estimatedPrice)}<span>MAD</span></div>
        <p className="result-label">Valeur estimée <span>·</span> {submittedCar.localisation}</p>
        <button className="reset-button" onClick={onReset}>Nouvelle estimation <ArrowUpRight size={18} /></button>
      </div> : <p className="story-description">Estimez votre voiture d’occasion au Maroc.</p>}
    </div>
  );
}
