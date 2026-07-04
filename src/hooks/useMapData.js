import { useState, useEffect } from 'react'
import { getCountries } from '../services/DataService'

export function useMapData() {
  const [countries, setCountries] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getCountries()
      .then(setCountries)
      .catch(setError)
  }, [])

  return { countries, error }
}
