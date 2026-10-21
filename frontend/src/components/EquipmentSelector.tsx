import React, { useState } from "react";
import { Check, X } from "lucide-react";

interface EquipmentSelectorProps {
  options: string[];
  selectedOptions: string[];
  onChange: (selected: string[]) => void;
}

const EquipmentSelector: React.FC<EquipmentSelectorProps> = ({
  options,
  selectedOptions,
  onChange,
}) => {
  const [searchTerm, setSearchTerm] = useState("");

  const handleToggleOption = (option: string) => {
    const isSelected = selectedOptions.includes(option);

    if (isSelected) {
      onChange(selectedOptions.filter((item) => item !== option));
    } else {
      onChange([...selectedOptions, option]);
    }
  };

  const handleRemoveOption = (option: string, e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(selectedOptions.filter((item) => item !== option));
  };

  const filteredOptions = options.filter((option) =>
    option.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 mb-4 min-h-12">
        {selectedOptions.length === 0 && (
          <span className="text-gray-500 text-sm italic">
            Aucun équipement sélectionné
          </span>
        )}

        {selectedOptions.map((option) => (
          <div
            key={option}
            className="bg-gray-800 text-white px-3 py-1 rounded-full flex items-center text-sm border border-amber-500/30"
          >
            <span>{option}</span>
            <button
              type="button"
              onClick={(e) => handleRemoveOption(option, e)}
              className="ml-2 text-gray-400 hover:text-white"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>

      <div className="relative">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Rechercher des équipements..."
          className="w-full bg-gray-800 border border-gray-700 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-transparent mb-2"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-2 max-h-60 overflow-y-auto p-2 rounded-lg bg-gray-900/50">
        {filteredOptions.map((option) => {
          const isSelected = selectedOptions.includes(option);

          return (
            <div
              key={option}
              onClick={() => handleToggleOption(option)}
              className={`
                cursor-pointer px-3 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors
                ${
                  isSelected
                    ? "bg-amber-500/20 text-amber-300 border border-amber-400/30"
                    : "bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700"
                }
              `}
            >
              <div
                className={`
                w-4 h-4 rounded border flex items-center justify-center
                ${
                  isSelected
                    ? "border-amber-400 bg-amber-400 text-black"
                    : "border-gray-600"
                }
              `}
              >
                {isSelected && <Check className="w-3 h-3" />}
              </div>
              <span>{option}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EquipmentSelector;
