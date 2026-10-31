export const formatPrice = (price: number): string => {
  return new Intl.NumberFormat('fr-MA', { maximumFractionDigits: 0 }).format(price);
};
