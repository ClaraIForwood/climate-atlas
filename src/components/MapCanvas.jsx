import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import useClimateStore from '../store/useClimateStore'
import { useMapData } from '../hooks/useMapData'
import { formatTemp } from '../utils/formatters'

const MAP_STYLE = 'https://tiles.openfreemap.org/styles/dark'
const FALLBACK_STYLE = 'https://tiles.openfreemap.org/styles/liberty'

const GRID_YEARS = [2030, 2040, 2050, 2060, 2070, 2080]

function snapToGridYear(year) {
  return GRID_YEARS.reduce((a, b) =>
    Math.abs(b - year) < Math.abs(a - year) ? b : a
  )
}

function enrichCountries(countries) {
  return {
    ...countries,
    features: countries.features.map((f) => {
      const v = f.properties.vulnerability ?? 0.5
      const r = f.properties.readiness ?? 0.5
      return {
        ...f,
        properties: {
          ...f.properties,
          score_v:     Math.round((1 - v) * 1000) / 10,
          score_r:     Math.round(r * 1000) / 10,
          score_blend: Math.round(((1 - v + r) / 2) * 1000) / 10,
        },
      }
    }),
  }
}

function countryScoreProp(readiness, vulnerability) {
  if (readiness && vulnerability) return 'score_blend'
  if (readiness)                  return 'score_r'
  return 'score_v'
}

function makeCountryColorExpr(prop) {
  return [
    'interpolate', ['linear'], ['get', prop],
    0,   '#B01020',
    25,  '#E07020',
    50,  '#F0C040',
    75,  '#A8D96B',
    100, '#4EB3D3',
  ]
}

function getInitialView() {
  const p = new URLSearchParams(window.location.search)
  return {
    center: [
      parseFloat(p.get('lng') ?? '10'),
      parseFloat(p.get('lat') ?? '20'),
    ],
    zoom: parseFloat(p.get('zoom') ?? '2.2'),
  }
}

// CMIP6 temperature grid fill colour ramp (ColorBrewer "RdYlBu"/"RdBu" diverging family).
// Extends to [-1.0, 10.0] to match TEMP_ANOMALY_CLIP_MIN/MAX in sources.py — the -1.0 stop
// (#313695) represents real single-run cooling relative to the 1990 baseline, and the 10.0
// stop (#67001f) extends the hot end so cells above the old 5°C ceiling remain distinguishable
// rather than bucketing into identical dark red. The 6.5/8.5 stops are linear RGB blends
// between #a50026 and #67001f (not arbitrary picks) so the 5-10°C band gets banding as fine
// as the 0-5°C band instead of only 2 points spanning 5 degrees.
const CMIP6_COLOR_EXPR = [
  'interpolate', ['linear'], ['get', 'temp_anomaly'],
  -1.0, '#313695',
   0.0, '#4575b4',
   1.0, '#74add1',
   1.5, '#abd9e9',
   2.0, '#fee090',
   2.5, '#fdae61',
   3.0, '#f46d43',
   4.0, '#d73027',
   5.0, '#a50026',
   6.5, '#920024',
   8.5, '#7a0021',
  10.0, '#67001f',
]

export default function MapCanvas() {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const mapLoadedRef = useRef(false)
  const countriesRef = useRef(null)
  const cmip6DebounceRef = useRef(null)

  const activeYear   = useClimateStore((s) => s.activeYear)
  const activeLayers = useClimateStore((s) => s.activeLayers)

  const { countries } = useMapData()

  // ── Initialise map ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const { center, zoom } = getInitialView()

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center,
      zoom,
      minZoom: 1.5,
      maxZoom: 14,
      attributionControl: false,
      pitchWithRotate: false,
    })

    map.addControl(
      new maplibregl.AttributionControl({ compact: true }),
      'bottom-right',
    )

    let styleFailed = false
    map.on('error', (e) => {
      if (!styleFailed && !e.sourceId) {
        styleFailed = true
        map.setStyle(FALLBACK_STYLE)
      }
    })

    map.on('load', () => {
      mapLoadedRef.current = true

      // ── CMIP6 grid fill ────────────────────────────────────────────────────
      map.addSource('cmip6-grid', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: 'cmip6-grid-fill',
        type: 'fill',
        source: 'cmip6-grid',
        layout: { visibility: 'none' },
        paint: {
          'fill-color': CMIP6_COLOR_EXPR,
          'fill-opacity': 0.65,
          'fill-outline-color': 'transparent',
        },
      })

      // ── Country fill (ND-GAIN) ────────────────────────────────────────────
      map.addSource('countries', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: 'countries-fill',
        type: 'fill',
        source: 'countries',
        layout: { visibility: 'none' },
        paint: {
          'fill-color': makeCountryColorExpr('score_blend'),
          'fill-opacity': 0.35,
        },
      })
      map.addLayer({
        id: 'countries-outline',
        type: 'line',
        source: 'countries',
        layout: { visibility: 'none' },
        paint: {
          'line-color': 'rgba(255,255,255,0.1)',
          'line-width': 0.5,
        },
      })

      // Hover cursor + click popup on the CMIP6 grid
      map.on('mouseenter', 'cmip6-grid-fill', () => {
        map.getCanvas().style.cursor = 'pointer'
      })
      map.on('mouseleave', 'cmip6-grid-fill', () => {
        map.getCanvas().style.cursor = ''
      })

      let gridPopup = null
      map.on('click', 'cmip6-grid-fill', (e) => {
        const props = e.features?.[0]?.properties
        if (!props) return
        const html =
          `<div style="background:rgba(10,10,20,0.88);border:1px solid rgba(255,255,255,0.1);` +
          `border-radius:8px;padding:8px 10px;color:#fff;font-family:system-ui,sans-serif">` +
          `<div style="font-size:11px;font-weight:700;margin-bottom:4px">${props.lat.toFixed(2)}°, ${props.lon.toFixed(2)}°</div>` +
          `<div style="font-size:14px;font-weight:700;color:#F0C040">${formatTemp(props.temp_anomaly)}</div>` +
          `<div style="font-size:8px;color:rgba(255,255,255,0.35);margin-top:3px">Temp anomaly vs 1990 baseline</div>` +
          `</div>`

        if (gridPopup) gridPopup.remove()
        gridPopup = new maplibregl.Popup({
          closeButton: true,
          closeOnClick: true,
          offset: 8,
          className: 'city-hover-popup',
        })
          .setLngLat(e.lngLat)
          .setHTML(html)
          .addTo(map)
      })

      // Persist map position to URL
      map.on('moveend', () => {
        const { lng, lat } = map.getCenter()
        const p = new URLSearchParams(window.location.search)
        p.set('lat', lat.toFixed(4))
        p.set('lng', lng.toFixed(4))
        p.set('zoom', map.getZoom().toFixed(2))
        window.history.replaceState(null, '', `?${p.toString()}`)
      })

      // Populate immediately if data arrived before map finished loading
      if (countriesRef.current) {
        map.getSource('countries').setData(enrichCountries(countriesRef.current))
      }
    })

    mapRef.current = map

    return () => {
      mapRef.current?.remove()
      mapRef.current = null
      mapLoadedRef.current = false
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Populate countries once ─────────────────────────────────────────────────
  useEffect(() => {
    countriesRef.current = countries
    const map = mapRef.current
    if (!map || !mapLoadedRef.current || !countries) return
    map.getSource('countries')?.setData(enrichCountries(countries))
  }, [countries])

  // ── Show/hide country fill and switch score property ────────────────────────
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapLoadedRef.current) return
    const show = activeLayers.readiness || activeLayers.vulnerability
    const vis = show ? 'visible' : 'none'
    map.setLayoutProperty('countries-fill', 'visibility', vis)
    map.setLayoutProperty('countries-outline', 'visibility', vis)
    if (show) {
      const prop = countryScoreProp(activeLayers.readiness, activeLayers.vulnerability)
      map.setPaintProperty('countries-fill', 'fill-color', makeCountryColorExpr(prop))
    }
  }, [activeLayers.readiness, activeLayers.vulnerability])

  // ── CMIP6 grid visibility + initial data load ──────────────────────────────
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapLoadedRef.current) return
    const vis = activeLayers.cmip6Grid ? 'visible' : 'none'
    map.setLayoutProperty('cmip6-grid-fill', 'visibility', vis)
    if (activeLayers.cmip6Grid) {
      const gridYear = snapToGridYear(activeYear)
      map.getSource('cmip6-grid')?.setData(`${import.meta.env.BASE_URL}data/cmip6_grid_${gridYear}.geojson`)
    }
  }, [activeLayers.cmip6Grid]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── CMIP6 grid year change (debounced 50 ms) ───────────────────────────────
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapLoadedRef.current || !activeLayers.cmip6Grid) return
    clearTimeout(cmip6DebounceRef.current)
    cmip6DebounceRef.current = setTimeout(() => {
      const gridYear = snapToGridYear(activeYear)
      map.getSource('cmip6-grid')?.setData(`${import.meta.env.BASE_URL}data/cmip6_grid_${gridYear}.geojson`)
    }, 50)
  }, [activeYear, activeLayers.cmip6Grid])

  return <div ref={containerRef} style={{ position: 'absolute', inset: 0 }} />
}
