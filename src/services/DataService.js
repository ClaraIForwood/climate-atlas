let _countries = null

export async function getCountries() {
  if (_countries) return _countries
  const res = await fetch(`${import.meta.env.BASE_URL}data/countries.geojson`)
  if (!res.ok) throw new Error(`Failed to fetch countries: ${res.status}`)
  _countries = await res.json()
  return _countries
}

export async function getMeta() {
  const res = await fetch(`${import.meta.env.BASE_URL}data/meta.json`)
  if (!res.ok) throw new Error(`Failed to fetch meta: ${res.status}`)
  return res.json()
}
