export function formatTemp(anomaly) {
  const sign = anomaly >= 0 ? '+' : ''
  return `${sign}${anomaly.toFixed(1)}°C`
}

export function formatYear(year) {
  return Math.round(year).toString()
}
