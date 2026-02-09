export function getDiscountedPrice(price: number, discountPercent?: number | null) {
  if (!discountPercent || discountPercent <= 0) {
    return price;
  }
  const multiplier = Math.max(0, 100 - discountPercent) / 100;
  return Math.round(price * multiplier);
}

export function formatPrice(price: number) {
  return price.toLocaleString("ru-RU");
}
