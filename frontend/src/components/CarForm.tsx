import React, { useState } from "react";
import { CarData } from "../types/CarData";
import EquipmentSelector from "./EquipmentSelector";
import { ChevronRight } from "lucide-react";

const INITIAL_CAR_DATA: CarData = {
  marque: "",
  modele: "",
  localisation: "",
  kilometrage: "15 000 - 19 999",
  anneeModele: new Date().getFullYear(),
  puissanceFiscale: Number(null),
  nombreDePortes: Number(null),
  etat: "",
  premiereMain: "Oui",
  equipements: [],
  boiteDeVitesses: "Automatique",
  typeDeCarburant: "Essence",
};

const EQUIPMENT_OPTIONS = [
  "ABS",
  "Airbags",
  "Caméra de recul",
  "CD/MP3/Bluetooth",
  "Climatisation",
  "ESP",
  "Jantes aluminium",
  "Limiteur de vitesse",
  "Ordinateur de bord",
  "Radar de recul",
  "Régulateur de vitesse",
  "Sièges cuir",
  "Système de navigation/GPS",
  "Toit ouvrant",
  "Verrouillage centralisé à distance",
  "Vitres électriques",
];

const LOCATIONS = [
  "Casablanca",
  "Rabat",
  "Tanger",
  "Marrakech",
  "Agadir",
  "Meknès",
  "Kénitra",
  "Fès",
  "Salé",
  "Oujda",
  "Tétouan",
  "Safi",
  "Dakhla",
  "Mohammedia",
  "Taza",
  "El Jadida",
  "Bouznika",
  "Khouribga",
  "Deroua",
  "Temara",
  "Nador",
  "Oued Amlil",
  "Berkane",
  "Guercif",
  "Laâyoune",
  "Boujdour",
  "Béni Mellal",
  "Ifrane",
  "Jamaat Shaim",
  "Ain Aouda",
  "Dar Bouazza",
  "Had Soualem",
  "autres",
];

const KILOMETRAGE_OPTIONS = [
  "0 - 4 999",
  "5 000 - 9 999",
  "10 000 - 14 999",
  "15 000 - 19 999",
  "20 000 - 24 999",
  "25 000 - 29 999",
  "30 000 - 49 999",
  "50 000 - 74 999",
  "75 000 - 99 999",
  "100 000 - 124 999",
  "125 000 - 149 999",
  "150 000 - 174 999",
  "175 000 - 199 999",
  "200 000 - 249 999",
  "250 000 - 299 999",
  "300 000 - 399 999",
  "400 000 - 499 999",
  "500 000+",
];

interface CarFormProps {
  onSubmit: (data: CarData) => void;
}

const CarForm: React.FC<CarFormProps> = ({ onSubmit }) => {
  const [carData, setCarData] = useState<CarData>(INITIAL_CAR_DATA);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setCarData((prev) => ({
      ...prev,
      [name]:
        name === "anneeModele" || name === "nombreDePortes"
          ? parseInt(value, 10)
          : value,
    }));
  };

  const handleEquipmentChange = (selectedEquipment: string[]) => {
    setCarData((prev) => ({
      ...prev,
      equipements: selectedEquipment,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(carData);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-4xl mx-auto bg-gradient-to-br from-gray-900/50 to-black/50 p-6 md:p-8 rounded-xl border border-gray-800/50 shadow-xl backdrop-blur-sm"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left column */}
        <div className="space-y-6">
          <div>
            <label className="block text-primary-300 mb-2 text-sm font-medium">
              Marque
            </label>
            <input
              type="text"
              name="marque"
              placeholder="Marque"
              value={carData.marque}
              onChange={handleChange}
              className="w-full bg-gray-800/50 border border-gray-700/50 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label className="block text-primary-300 mb-2 text-sm font-medium">
              Modèle
            </label>
            <input
              type="text"
              name="modele"
              placeholder="Modèle"
              value={carData.modele}
              onChange={handleChange}
              className="w-full bg-gray-800/50 border border-gray-700/50 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label className="block text-primary-300 mb-2 text-sm font-medium">
              Localisation
            </label>
            <select
              name="localisation"
              value={carData.localisation}
              onChange={handleChange}
              className="w-full bg-gray-800/50 border border-gray-700/50 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            >
              {LOCATIONS.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-primary-300 mb-2 text-sm font-medium">
              Kilométrage
            </label>
            <select
              name="kilometrage"
              value={carData.kilometrage}
              onChange={handleChange}
              className="w-full bg-gray-800/50 border border-gray-700/50 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            >
              {KILOMETRAGE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-primary-300 mb-2 text-sm font-medium">
              Année-Modèle
            </label>
            <input
              type="number"
              name="anneeModele"
              placeholder="Année Modèle"
              min="1980"
              max={new Date().getFullYear()}
              value={carData.anneeModele}
              onChange={handleChange}
              className="w-full bg-gray-800/50 border border-gray-700/50 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label className="block text-primary-300 mb-2 text-sm font-medium">
              Puissance fiscale
            </label>
            <input
              type="number"
              min={1}
              name="puissanceFiscale"
              placeholder="Puissance fiscale"
              value={carData.puissanceFiscale}
              onChange={handleChange}
              className="w-full bg-gray-800/50 border border-gray-700/50 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            />
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          <div>
            <label className="block text-primary-300 mb-2 text-sm font-medium">
              Nombre de portes
            </label>
            <input
              type="number"
              name="nombreDePortes"
              placeholder="Nombre de portes"
              min="1"
              max="5"
              value={carData.nombreDePortes}
              onChange={handleChange}
              className="w-full bg-gray-800/50 border border-gray-700/50 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label className="block text-primary-300 mb-2 text-sm font-medium">
              État
            </label>
            <select
              name="etat"
              value={carData.etat}
              onChange={handleChange}
              className="w-full bg-gray-800/50 border border-gray-700/50 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            >
              <option value="">Sélectionnez</option>
              <option value="Excellent">Excellent</option>
              <option value="Très bon">Très bon</option>
              <option value="Bon">Bon</option>
              <option value="Moyen">Moyen</option>
            </select>
          </div>

          <div>
            <label className="block text-primary-300 mb-2 text-sm font-medium">
              Première main
            </label>
            <select
              name="premiereMain"
              value={carData.premiereMain}
              onChange={handleChange}
              className="w-full bg-gray-800/50 border border-gray-700/50 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            >
              <option value="Oui">Oui</option>
              <option value="Non">Non</option>
            </select>
          </div>

          <div>
            <label className="block text-primary-300 mb-2 text-sm font-medium">
              Boite de vitesses
            </label>
            <select
              name="boiteDeVitesses"
              value={carData.boiteDeVitesses}
              onChange={handleChange}
              className="w-full bg-gray-800/50 border border-gray-700/50 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            >
              <option value="Automatique">Automatique</option>
              <option value="Manuelle">Manuelle</option>
            </select>
          </div>

          <div>
            <label className="block text-primary-300 mb-2 text-sm font-medium">
              Type de carburant
            </label>
            <select
              name="typeDeCarburant"
              value={carData.typeDeCarburant}
              onChange={handleChange}
              className="w-full bg-gray-800/50 border border-gray-700/50 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            >
              <option value="Essence">Essence</option>
              <option value="Diesel">Diesel</option>
              <option value="Hybride">Hybride</option>
              <option value="Électrique">Électrique</option>
            </select>
          </div>
        </div>
      </div>

      <div className="mt-8">
        <label className="block text-primary-300 mb-2 text-sm font-medium">
          Équipements
        </label>
        <EquipmentSelector
          options={EQUIPMENT_OPTIONS}
          selectedOptions={carData.equipements}
          onChange={handleEquipmentChange}
        />
      </div>

      <div className="mt-8 text-center">
        <button
          type="submit"
          className="bg-gradient-to-r from-primary-400 to-secondary-400 text-white font-medium px-6 py-3 rounded-lg hover:from-primary-500 hover:to-secondary-500 transition-all duration-300 flex items-center justify-center mx-auto group"
        >
          <span>Estimer le prix</span>
          <ChevronRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </form>
  );
};

export default CarForm;
