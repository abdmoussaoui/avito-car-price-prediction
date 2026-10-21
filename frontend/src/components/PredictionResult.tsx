import React, { useEffect, useState } from "react";
import { PredictionResult } from "../types/CarData";
import { formatPrice } from "../utils/formatters";
import {
  ArrowLeftCircle,
  TrendingUp,
  BarChart4,
  Calculator,
  ExternalLink,
} from "lucide-react";
import { getRecommendations } from "../utils/api";

interface PredictionResultProps {
  result: PredictionResult;
  onBack: () => void;
  carDetails: {
    marque: string;
    modele: string;
    anneeModele: number;
  };
}

const PredictionResultDisplay: React.FC<PredictionResultProps> = ({
  result,
  onBack,
  carDetails,
}) => {
  const [animatedPrice, setAnimatedPrice] = useState(0);
  const [recommendations, setRecommendations] = useState<string[]>([]);

  useEffect(() => {
    const duration = 2000;
    const steps = 40;
    const increment = result.estimatedPrice / steps;
    const stepTime = duration / steps;

    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= result.estimatedPrice) {
        current = result.estimatedPrice;
        clearInterval(timer);
      }
      setAnimatedPrice(current);
    }, stepTime);

    // Fetch recommendations
    getRecommendations().then(setRecommendations).catch(console.error);

    return () => clearInterval(timer);
  }, [result.estimatedPrice]);

  return (
    <div className="w-full max-w-4xl mx-auto bg-gradient-to-br from-gray-900 to-black p-6 md:p-8 rounded-xl border border-gray-800 shadow-xl">
      <div className="flex flex-col items-center">
        <h2 className="text-2xl font-bold text-primary-300 mb-4 text-center">
          Estimation de prix pour {carDetails.marque} {carDetails.modele}{" "}
          {carDetails.anneeModele}
        </h2>

        <div className="w-full py-8 flex flex-col items-center recommendation-container">
          <div className="text-4xl md:text-6xl font-bold text-white mb-2 flex items-center">
            <span className="mr-3">MAD</span>
            <span className="bg-gradient-to-r from-primary-300 to-secondary-300 bg-clip-text text-transparent">
              {formatPrice(animatedPrice)}
            </span>
          </div>

          <div className="text-gray-400 mt-2 text-center">
            Fourchette de prix estimée:
            <span className="text-primary-300 font-medium ml-2">
              MAD {formatPrice(result.priceRange.min)} -{" "}
              {formatPrice(result.priceRange.max)}
            </span>
          </div>

          {/* <div className="mt-4 text-gray-400">
            <div className="flex items-center">
              <Calculator className="w-5 h-5 mr-2 text-secondary-300" />
              Taxe estimée:
              <span className="text-secondary-300 font-medium ml-2">
                MAD {formatPrice(result.estimatedTax)}
              </span>
            </div>
          </div> */}

          <div className="bg-gray-800/50 rounded-lg p-4 mt-8 w-full max-w-md recommendation">
            <div className="flex items-center mb-4">
              <div className="bg-primary-500/20 p-2 rounded-full mr-4">
                <ExternalLink className="text-primary-400 w-6 h-6" />
              </div>
              <h3 className="text-white font-medium">
                Recommandations d'achat
              </h3>
            </div>
            {/* <ul className="text-gray-400 text-sm space-y-2">
              {recommendations.map((rec, index) => (
                <li key={index} className="flex items-center">
                  <span className="w-2 h-2 bg-secondary-400 rounded-full mr-2"></span>
                  {rec}
                </li>
              ))}
            </ul> */}
            <iframe src="https://www.avito.ma/fr/maroc/voitures_d_occasion-%C3%A0_vendre"></iframe>
          </div>
        </div>

        <button
          onClick={onBack}
          className="mt-8 flex items-center text-primary-300 hover:text-primary-400 transition-colors"
        >
          <ArrowLeftCircle className="mr-2 w-5 h-5" />
          Retour au formulaire
        </button>
      </div>
    </div>
  );
};

export default PredictionResultDisplay;
