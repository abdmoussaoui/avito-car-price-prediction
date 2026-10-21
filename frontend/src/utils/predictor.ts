import { CarData, PredictionResult } from "../types/CarData";

// In a real application, this would be a complex model or API call
// For this demo, we'll use a simplified model with randomness
export const predictCarPrice = (carData: CarData): PredictionResult => {
  // Base price for a Rolls-Royce Wraith
  let basePrice = 4500000;

  // Model year adjustment
  const currentYear = new Date().getFullYear();
  const age = currentYear - carData.anneeModele;
  const yearMultiplier = Math.pow(0.92, age); // 8% depreciation per year

  // Mileage adjustment
  let mileageMultiplier = 1.0;
  const mileageRange = carData.kilometrage;

  if (mileageRange.includes("0 - 4 999")) {
    mileageMultiplier = 1.1;
  } else if (mileageRange.includes("5 000 - 9 999")) {
    mileageMultiplier = 1.05;
  } else if (mileageRange.includes("10 000 - 14 999")) {
    mileageMultiplier = 1.0;
  } else if (mileageRange.includes("15 000 - 19 999")) {
    mileageMultiplier = 0.95;
  } else if (mileageRange.includes("20 000 - 24 999")) {
    mileageMultiplier = 0.92;
  } else if (mileageRange.includes("25 000 - 29 999")) {
    mileageMultiplier = 0.9;
  } else if (mileageRange.includes("30 000 - 49 999")) {
    mileageMultiplier = 0.85;
  } else if (mileageRange.includes("50 000 - 74 999")) {
    mileageMultiplier = 0.8;
  } else if (mileageRange.includes("75 000 - 99 999")) {
    mileageMultiplier = 0.75;
  } else {
    mileageMultiplier = 0.7;
  }

  // Equipment adjustment - each luxury equipment adds value
  const equipmentBonus = 0.005 * carData.equipements.length;

  // First owner bonus
  const firstOwnerBonus = carData.premiereMain === "Oui" ? 0.05 : 0;

  // Calculate final price
  const calculatedPrice =
    basePrice *
    yearMultiplier *
    mileageMultiplier *
    (1 + equipmentBonus + firstOwnerBonus);

  // Add some randomness to simulate market variations (±5%)
  const randomFactor = 0.95 + Math.random() * 0.1;
  const finalPrice = calculatedPrice * randomFactor;

  // Calculate price range (±10%)
  const minPrice = finalPrice * 0.9;
  const maxPrice = finalPrice * 1.1;

  // Calculate confidence based on data completeness
  let confidence = 0.85; // Base confidence

  // Return the prediction
  return {
    estimatedPrice: Math.round(finalPrice),
    priceRange: {
      min: Math.round(minPrice),
      max: Math.round(maxPrice),
    },
    confidence,
  };
};
