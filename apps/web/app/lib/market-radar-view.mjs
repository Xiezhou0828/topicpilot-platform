export function rotationTone(change) {
  if (change === null || change === undefined) return "missing";
  if (change > 0) return "warming";
  if (change < 0) return "cooling";
  return "flat";
}

export function rotationLabel(change) {
  const tone = rotationTone(change);
  if (tone === "warming") return "升溫";
  if (tone === "cooling") return "降溫";
  if (tone === "flat") return "持平";
  return "資料不足";
}

export function countRatio(count, denominator) {
  if (count === null || count === undefined || denominator === null || denominator === undefined) return "—";
  return `${count} / ${denominator}`;
}

export function signedValue(value) {
  if (value === null || value === undefined) return "—";
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}
