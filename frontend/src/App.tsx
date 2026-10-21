import React, { useState } from 'react';
import Header from './components/Header';
import CarForm from './components/CarForm';
import PredictionResultDisplay from './components/PredictionResult';
import Background from './components/Background';
import { CarData, PredictionResult } from './types/CarData';
import { predictCarPrice } from './utils/api';

function App() {
  const [predictionResult, setPredictionResult] = useState<PredictionResult | null>(null);
  const [carDetails, setCarDetails] = useState<{
    marque: string;
    modele: string;
    anneeModele: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: CarData) => {
    try {
      setError(null);
      const result = await predictCarPrice(data);
      setPredictionResult(result);
      setCarDetails({
        marque: data.marque,
        modele: data.modele,
        anneeModele: data.anneeModele
      });
    } catch (err) {
      setError("Une erreur s'est produite lors de l'estimation. Veuillez réessayer.");
      console.error(err);
    }
  };

  const handleBack = () => {
    setPredictionResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen text-white relative">
      <Background />
      
      <div className="container mx-auto px-4 py-8">
        <Header />
        
        <main className="mt-8 mb-16">
          {error && (
            <div className="w-full max-w-4xl mx-auto mb-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-300">
              {error}
            </div>
          )}
          
          {predictionResult && carDetails ? (
            <PredictionResultDisplay 
              result={predictionResult} 
              onBack={handleBack}
              carDetails={carDetails}
            />
          ) : (
            <CarForm onSubmit={handleSubmit} />
          )}
        </main>
        
        <footer className="text-center text-gray-400 text-sm py-4">
          © {new Date().getFullYear()} PrixPro — Estimations professionnelles de véhicules
        </footer>
      </div>
    </div>
  );
}

export default App;