import { useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';
import Header from './components/Header';
import CarForm from './components/CarForm';
import PredictionResultDisplay from './components/PredictionResult';
import type { CarData, CarOptions, FieldErrors, PredictionResult } from './types/CarData';
import { ApiError, getCarOptions, predictCarPrice } from './utils/api';

const emptyCar = (): CarData => ({
  marque: '', modele: '', localisation: '', kilometrage: '', anneeModele: 0,
  puissanceFiscale: 0, nombreDePortes: 0, etat: '', premiereMain: 'Oui',
  equipements: [], boiteDeVitesses: '', typeDeCarburant: '',
});

function validate(car: CarData, options: CarOptions): FieldErrors {
  const errors: FieldErrors = {};
  if (!options.brands.includes(car.marque)) errors.marque = 'Sélectionnez une marque.';
  if (!options.models[car.marque]?.includes(car.modele)) errors.modele = 'Sélectionnez un modèle.';
  if (!options.locations.includes(car.localisation)) errors.localisation = 'Sélectionnez votre ville.';
  if (!Number.isInteger(car.anneeModele) || car.anneeModele < options.min_year || car.anneeModele > options.max_year)
    errors.anneeModele = `Choisissez une année entre ${options.min_year} et ${options.max_year}.`;
  if (!/^\d+$/.test(car.kilometrage) || Number(car.kilometrage) > 1000000) errors.kilometrage = 'Saisissez un kilométrage entre 0 et 1 000 000 km.';
  if (!Number.isInteger(car.puissanceFiscale) || car.puissanceFiscale < 1 || car.puissanceFiscale > 41) errors.puissanceFiscale = 'Saisissez une puissance de 1 à 41 CV.';
  if (!Number.isInteger(car.nombreDePortes) || car.nombreDePortes < 1 || car.nombreDePortes > 7) errors.nombreDePortes = 'Sélectionnez le nombre de portes.';
  if (!options.conditions.includes(car.etat)) errors.etat = 'Sélectionnez l’état du véhicule.';
  if (!options.fuels.includes(car.typeDeCarburant)) errors.typeDeCarburant = 'Sélectionnez un carburant.';
  if (!['Manuelle', 'Automatique'].includes(car.boiteDeVitesses)) errors.boiteDeVitesses = 'Sélectionnez une transmission.';
  return errors;
}

export default function App() {
  const [car, setCar] = useState<CarData>(emptyCar);
  const [options, setOptions] = useState<CarOptions | null>(null);
  const [optionsError, setOptionsError] = useState('');
  const [retry, setRetry] = useState(0);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [submittedCar, setSubmittedCar] = useState<CarData | null>(null);
  const submitting = useRef(false);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    setOptionsError('');
    getCarOptions(controller.signal).then(setOptions).catch(err => {
      if (!controller.signal.aborted) setOptionsError(err.message);
    });
    return () => controller.abort();
  }, [retry]);

  const handleChange = (next: CarData) => {
    setCar(next);
    setErrors(previous => {
      const remaining = { ...previous };
      for (const key of Object.keys(next) as (keyof CarData)[]) {
        if (next[key] !== car[key]) delete remaining[key];
      }
      return remaining;
    });
    setResult(null);
    setError('');
  };

  const handleSubmit = async () => {
    if (!options || submitting.current) return;
    const validation = validate(car, options);
    setErrors(validation);
    if (Object.keys(validation).length) {
      setError('Quelques précisions et votre estimation est prête. Vérifiez les champs indiqués.');
      document.getElementById(Object.keys(validation)[0])?.focus();
      return;
    }
    submitting.current = true;
    setLoading(true);
    setResult(null);
    setError('');
    try {
      const prediction = await predictCarPrice(car);
      setSubmittedCar({ ...car, equipements: [...car.equipements] });
      setResult(prediction);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue. Réessayez.');
      if (err instanceof ApiError) {
        setErrors(err.fields);
        const field = Object.keys(err.fields)[0];
        if (field) document.getElementById(field)?.focus();
      }
    } finally { setLoading(false); submitting.current = false; }
  };

  const reset = () => {
    setCar(emptyCar()); setResult(null); setSubmittedCar(null); setErrors({}); setError('');
    document.getElementById('estimation')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    document.getElementById('marque')?.focus({ preventScroll: true });
  };

  useEffect(() => {
    if ((loading || result) && window.innerWidth < 1000) {
      resultRef.current?.scrollIntoView({
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
        block: 'center',
      });
    }
  }, [loading, result]);

  return (
    <div className="app-shell">
      <Header />
      <main className="estimator-layout">
        <section className={`story-panel ${result ? 'is-valued' : ''}`} aria-label="Estimation automobile">
          <div className="story-copy">
            <h1>Votre auto.<br /><em>Sa valeur.</em></h1>
            <div className="result-anchor" ref={resultRef}>
              <PredictionResultDisplay result={result} submittedCar={submittedCar} loading={loading} onReset={reset} />
            </div>
          </div>
          <div className="automotive-image">
            <img src="/images/clio-atlas.webp" alt="Visuel d’ambiance : une Renault Clio sur une route au Maroc." fetchPriority="high" width="1536" height="1024" />
          </div>
        </section>
        <section className="form-panel" id="estimation" aria-label="Caractéristiques de votre véhicule">
            {error && <div className="error-banner" role="alert"><p>{error}</p></div>}
            {options ? <CarForm car={car} options={options} errors={errors} loading={loading} onChange={handleChange} onSubmit={handleSubmit} />
              : <div className="options-state" role={optionsError ? 'alert' : 'status'}>
                {optionsError ? <><h2>Connexion indisponible.</h2><p>{optionsError}</p><button className="secondary-button" onClick={() => setRetry(value => value + 1)}>Réessayer</button></>
                  : <><Loader2 className="spin" size={24} /><p>Chargement du formulaire…</p></>}
              </div>}
        </section>
      </main>
    </div>
  );
}
