import { Check } from 'lucide-react';

interface Props {
  options: string[];
  selected: string[];
  onChange: (values: string[]) => void;
  disabled: boolean;
}

export default function EquipmentSelector({ options, selected, onChange, disabled }: Props) {
  return (
    <div className="equipment-grid" role="group" aria-label="Équipements du véhicule">
      {options.map(option => {
        const active = selected.includes(option);
        return (
          <button type="button" key={option} className={`equipment-chip ${active ? 'selected' : ''}`}
            aria-pressed={active} disabled={disabled}
            onClick={() => onChange(active ? selected.filter(value => value !== option) : [...selected, option])}>
            <span className="equipment-check" aria-hidden="true">{active && <Check size={11} />}</span>
            {option}
          </button>
        );
      })}
    </div>
  );
}
