import { ArrowUpRight, ChevronDown, Loader2 } from 'lucide-react';
import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import type { CarData, CarOptions, FieldErrors } from '../types/CarData';
import EquipmentSelector from './EquipmentSelector';

interface Props {
  car: CarData;
  options: CarOptions;
  errors: FieldErrors;
  loading: boolean;
  onChange: (data: CarData) => void;
  onSubmit: () => void;
}

function Field({ name, label, error, children }: {
  name: keyof CarData; label: string; error?: string; children: ReactNode;
}) {
  return <div className={`field ${error ? 'field-invalid' : ''}`}>
    <label htmlFor={name}>{label}</label>
    {children}
    {error && <span id={`${name}-error`} className="field-error">{error}</span>}
  </div>;
}

export default function CarForm({ car, options, errors, loading, onChange, onSubmit }: Props) {
  const equipmentRef = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    if (errors.equipements && equipmentRef.current) equipmentRef.current.open = true;
  }, [errors.equipements]);

  const set = (key: keyof CarData, value: string | number | string[]) => {
    onChange({ ...car, [key]: value, ...(key === 'marque' ? { modele: '' } : {}) });
  };
  const accessibility = (name: keyof CarData) => ({
    id: name, name, 'aria-invalid': Boolean(errors[name]),
    'aria-describedby': errors[name] ? `${name}-error` : undefined,
  });
  const select = (name: keyof CarData, values: string[], placeholder: string, disabled = false) => (
    <div className="select-wrap"><select {...accessibility(name)}
      value={String(car[name] || '')} disabled={disabled} required
      onChange={event => set(name, name === 'nombreDePortes' ? Number(event.target.value) : event.target.value)}>
      <option value="" disabled>{placeholder}</option>
      {values.map(value => <option key={value} value={value}>{value === 'Electrique' ? 'Électrique' : value === 'LPG' ? 'GPL (LPG)' : value}</option>)}
    </select><ChevronDown size={14} aria-hidden="true" /></div>
  );

  return (
    <form id="vehicle-form" onSubmit={event => { event.preventDefault(); onSubmit(); }} noValidate>
      <fieldset disabled={loading} className="form-fieldset">
        <section className="form-section" aria-labelledby="identity-heading">
          <h2 className="section-heading" id="identity-heading"><span>01</span> Le véhicule</h2>
          <div className="fields-grid">
            <Field name="marque" label="Marque" error={errors.marque}>{select('marque', options.brands, 'Sélectionner')}</Field>
            <Field name="modele" label="Modèle" error={errors.modele}>{select('modele', options.models[car.marque] || [], car.marque ? 'Sélectionner' : 'Choisir une marque d’abord', !car.marque)}</Field>
            <Field name="anneeModele" label="Année du modèle" error={errors.anneeModele}>
              <input {...accessibility('anneeModele')} type="number" inputMode="numeric" min={options.min_year} max={options.max_year} required
                value={car.anneeModele || ''} placeholder="2020" onChange={event => set('anneeModele', Number(event.target.value))} />
            </Field>
            <Field name="localisation" label="Ville" error={errors.localisation}>{select('localisation', options.locations, 'Sélectionner')}</Field>
          </div>
          {car.anneeModele > options.training_max_year && <p className="training-note">Le modèle traite les années après {options.training_max_year} comme {options.training_max_year}. L’estimation reste indicative.</p>}
        </section>

        <section className="form-section" aria-labelledby="spec-heading">
          <h2 className="section-heading" id="spec-heading"><span>02</span> La mécanique</h2>
          <div className="fields-grid">
            <Field name="kilometrage" label="Kilométrage" error={errors.kilometrage}>
              <div className="input-suffix"><input {...accessibility('kilometrage')} type="number" inputMode="numeric" min="0" max="1000000" required
                value={car.kilometrage} placeholder="85 000" onChange={event => set('kilometrage', event.target.value)} /><span>km</span></div>
            </Field>
            <Field name="puissanceFiscale" label="Puissance fiscale" error={errors.puissanceFiscale}>
              <div className="input-suffix"><input {...accessibility('puissanceFiscale')} type="number" inputMode="numeric" min="1" max="41" required
                value={car.puissanceFiscale || ''} placeholder="6" onChange={event => set('puissanceFiscale', Number(event.target.value))} /><span>CV</span></div>
            </Field>
            <Field name="typeDeCarburant" label="Carburant" error={errors.typeDeCarburant}>{select('typeDeCarburant', options.fuels, 'Sélectionner')}</Field>
            <Field name="boiteDeVitesses" label="Boîte de vitesses" error={errors.boiteDeVitesses}>{select('boiteDeVitesses', ['Manuelle', 'Automatique'], 'Sélectionner')}</Field>
          </div>
        </section>

        <section className="form-section condition-section" aria-labelledby="condition-heading">
          <h2 className="section-heading" id="condition-heading"><span>03</span> L’état & les options</h2>
          <div className="fields-grid">
            <Field name="etat" label="État général" error={errors.etat}>{select('etat', options.conditions, 'Sélectionner')}</Field>
            <Field name="nombreDePortes" label="Nombre de portes" error={errors.nombreDePortes}>{select('nombreDePortes', ['1', '2', '3', '4', '5', '6', '7'], 'Sélectionner')}</Field>
          </div>
          <div className="owner-row"><span id="owner-label">Première main</span>
            <div className="segmented" role="group" aria-labelledby="owner-label">
              {['Oui', 'Non'].map(value => <button type="button" key={value} aria-pressed={car.premiereMain === value}
                className={car.premiereMain === value ? 'active' : ''} onClick={() => set('premiereMain', value)}>{value}</button>)}
            </div>
          </div>
          <details className="equipment-disclosure" ref={equipmentRef}>
            <summary><span>Équipements <small>{car.equipements.length ? `${car.equipements.length} sélectionnés` : 'Facultatif'}</small></span><span className="disclosure-symbol" aria-hidden="true" /></summary>
            <EquipmentSelector options={options.equipment} selected={car.equipements} onChange={values => set('equipements', values)} disabled={loading} />
            {errors.equipements && <p className="field-error" role="alert">{errors.equipements}</p>}
          </details>
        </section>
        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? <><span>Estimation en cours</span><Loader2 className="spin" size={20} /></> : <><span>Estimer le prix</span><ArrowUpRight size={24} strokeWidth={1.5} /></>}
        </button>
        <p className="form-note">Estimation indicative à partir des annonces Avito Maroc.</p>
      </fieldset>
    </form>
  );
}
