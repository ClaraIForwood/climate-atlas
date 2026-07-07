import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import useClimateStore from '../store/useClimateStore'
import { useMapData } from '../hooks/useMapData'
import { formatTemp, formatPrecipPct } from '../utils/formatters'

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

// Precipitation grid fill colour ramp — ColorBrewer "BrBG" diverging (brown=drier,
// green=wetter), deliberately distinct from the temperature ramp above.
const PRECIP_COLOR_EXPR = [
  'interpolate', ['linear'], ['get', 'precip_change_pct'],
  -50, '#8c510a',
  -25, '#bf812d',
  -10, '#dfc27d',
    0, '#f5f5f5',
   10, '#c7eae5',
   25, '#80cdc1',
   50, '#35978f',
  100, '#01665e',
]

function gridUrl(name, gridYear) {
  return `${import.meta.env.BASE_URL}data/${name}_grid_${gridYear}.geojson`
}

function buildGridPopupHTML(lat, lon, valueLabel, valueColor, captionText) {
  return (
    `<div style="background:rgba(10,10,20,0.88);border:1px solid rgba(255,255,255,0.1);` +
    `border-radius:8px;padding:8px 10px;color:#fff;font-family:system-ui,sans-serif">` +
    `<div style="font-size:11px;font-weight:700;margin-bottom:4px">${lat.toFixed(2)}°, ${lon.toFixed(2)}°</div>` +
    `<div style="font-size:14px;font-weight:700;color:${valueColor}">${valueLabel}</div>` +
    `<div style="font-size:8px;color:rgba(255,255,255,0.35);margin-top:3px">${captionText}</div>` +
    `</div>`
  )
}

// Pure functions of a feature's properties — used identically by the click handler
// (initial popup) and by useGridLayerSync's year-change refresh (in-place update),
// so the two can never drift apart from each other.
const buildCmip6PopupHTML = (props) =>
  buildGridPopupHTML(props.lat, props.lon, formatTemp(props.temp_anomaly), '#F0C040', 'Temp anomaly vs 1990 baseline')

const buildPrecipPopupHTML = (props) =>
  buildGridPopupHTML(props.lat, props.lon, formatPrecipPct(props.precip_change_pct), '#80cdc1', 'Precip change vs 1990 baseline')

// Shared visibility/data-load + debounced year-change wiring for a raw grid layer.
// Pure parameterization of the two effect-pairs that used to exist only for the
// temperature grid — no behavioural differences between the temp/precip call sites.
function useGridLayerSync(mapRef, mapLoadedRef, {
  sourceId, layerId, enabled, activeYear, urlFor, debounceRef,
  popupRef, idleHandlerRef, buildPopupHTML,
}) {
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapLoadedRef.current) return
    map.setLayoutProperty(layerId, 'visibility', enabled ? 'visible' : 'none')
    if (enabled) {
      map.getSource(sourceId)?.setData(urlFor(snapToGridYear(activeYear)))
    } else {
      // Layer just turned off — either toggled off directly, or turned off by
      // LayerToggles' mutual-exclusivity logic when the other grid turned on.
      // A popup for a now-hidden layer is meaningless either way.
      popupRef.current?.remove()
    }
  }, [enabled]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapLoadedRef.current || !enabled) return

    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      map.getSource(sourceId)?.setData(urlFor(snapToGridYear(activeYear)))

      const popup = popupRef.current
      if (!popup) return // nothing open for this layer — nothing to refresh

      // Wait for the new data to actually be rendered before querying it —
      // 'idle' fires only after a render with all tiles loaded, unlike the
      // source's own 'data' event (which fires once parsed but before paint,
      // so queryRenderedFeatures could still miss it).
      const onIdle = () => {
        idleHandlerRef.current = null
        if (popupRef.current !== popup) return // closed while we were waiting

        const point = map.project(popup.getLngLat())
        const [feature] = map.queryRenderedFeatures(point, { layers: [layerId] })

        if (!feature) {
          popup.remove() // edge of land mask, or panned/zoomed since the click
          return
        }
        popup.setHTML(buildPopupHTML(feature.properties))
      }

      idleHandlerRef.current = onIdle
      map.once('idle', onIdle)
    }, 50)

    return () => {
      clearTimeout(debounceRef.current)
      if (idleHandlerRef.current) {
        map.off('idle', idleHandlerRef.current)
        idleHandlerRef.current = null
      }
    }
  }, [activeYear, enabled])
}

export default function MapCanvas() {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const mapLoadedRef = useRef(false)
  const countriesRef = useRef(null)
  const cmip6DebounceRef = useRef(null)
  const precipDebounceRef = useRef(null)
  const cmip6PopupRef = useRef(null)
  const precipPopupRef = useRef(null)
  const cmip6PopupIdleRef = useRef(null)
  const precipPopupIdleRef = useRef(null)

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

      // ── CMIP6 temperature grid fill ────────────────────────────────────────
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

      // ── Precipitation grid fill ─────────────────────────────────────────────
      map.addSource('precip-grid', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: 'precip-grid-fill',
        type: 'fill',
        source: 'precip-grid',
        layout: { visibility: 'none' },
        paint: {
          'fill-color': PRECIP_COLOR_EXPR,
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

      // Hover cursor + click popup on the CMIP6 temperature grid
      map.on('mouseenter', 'cmip6-grid-fill', () => {
        map.getCanvas().style.cursor = 'pointer'
      })
      map.on('mouseleave', 'cmip6-grid-fill', () => {
        map.getCanvas().style.cursor = ''
      })

      map.on('click', 'cmip6-grid-fill', (e) => {
        const props = e.features?.[0]?.properties
        if (!props) return
        cmip6PopupRef.current?.remove()
        const popup = new maplibregl.Popup({
          closeButton: true,
          closeOnClick: true,
          offset: 8,
          className: 'city-hover-popup',
        })
          .setLngLat(e.lngLat)
          .setHTML(buildCmip6PopupHTML(props))
          .addTo(map)
        popup.on('close', () => {
          if (cmip6PopupRef.current === popup) cmip6PopupRef.current = null
        })
        cmip6PopupRef.current = popup
      })

      // Hover cursor + click popup on the precipitation grid
      map.on('mouseenter', 'precip-grid-fill', () => {
        map.getCanvas().style.cursor = 'pointer'
      })
      map.on('mouseleave', 'precip-grid-fill', () => {
        map.getCanvas().style.cursor = ''
      })

      map.on('click', 'precip-grid-fill', (e) => {
        const props = e.features?.[0]?.properties
        if (!props) return
        precipPopupRef.current?.remove()
        const popup = new maplibregl.Popup({
          closeButton: true,
          closeOnClick: true,
          offset: 8,
          className: 'city-hover-popup',
        })
          .setLngLat(e.lngLat)
          .setHTML(buildPrecipPopupHTML(props))
          .addTo(map)
        popup.on('close', () => {
          if (precipPopupRef.current === popup) precipPopupRef.current = null
        })
        precipPopupRef.current = popup
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

      // Populate immediately if a layer is already enabled by the time the map
      // finishes loading — otherwise it silently never renders, since the
      // useGridLayerSync/country-fill effects below only re-apply state in
      // response to `enabled` *changing*, not to mapLoadedRef becoming true
      // (a ref mutation doesn't trigger a re-render). Reads live store state
      // via getState() rather than the closure's activeLayers/activeYear,
      // since useUrlState's mount-time URL hydration (in the parent App
      // component) runs AFTER this child effect's closure was captured, but
      // BEFORE this async 'load' event actually fires.
      const { activeLayers: initialLayers, activeYear: initialYear } = useClimateStore.getState()
      if (initialLayers.cmip6Grid) {
        map.setLayoutProperty('cmip6-grid-fill', 'visibility', 'visible')
        map.getSource('cmip6-grid').setData(gridUrl('cmip6', snapToGridYear(initialYear)))
      }
      if (initialLayers.precipGrid) {
        map.setLayoutProperty('precip-grid-fill', 'visibility', 'visible')
        map.getSource('precip-grid').setData(gridUrl('precip', snapToGridYear(initialYear)))
      }
      if (initialLayers.readiness || initialLayers.vulnerability) {
        const prop = countryScoreProp(initialLayers.readiness, initialLayers.vulnerability)
        map.setLayoutProperty('countries-fill', 'visibility', 'visible')
        map.setLayoutProperty('countries-outline', 'visibility', 'visible')
        map.setPaintProperty('countries-fill', 'fill-color', makeCountryColorExpr(prop))
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

  // ── Raw grid layers: visibility + initial load + debounced year-change ─────
  useGridLayerSync(mapRef, mapLoadedRef, {
    sourceId: 'cmip6-grid',
    layerId: 'cmip6-grid-fill',
    enabled: activeLayers.cmip6Grid,
    activeYear,
    urlFor: (yr) => gridUrl('cmip6', yr),
    debounceRef: cmip6DebounceRef,
    popupRef: cmip6PopupRef,
    idleHandlerRef: cmip6PopupIdleRef,
    buildPopupHTML: buildCmip6PopupHTML,
  })

  useGridLayerSync(mapRef, mapLoadedRef, {
    sourceId: 'precip-grid',
    layerId: 'precip-grid-fill',
    enabled: activeLayers.precipGrid,
    activeYear,
    urlFor: (yr) => gridUrl('precip', yr),
    debounceRef: precipDebounceRef,
    popupRef: precipPopupRef,
    idleHandlerRef: precipPopupIdleRef,
    buildPopupHTML: buildPrecipPopupHTML,
  })

  return <div ref={containerRef} style={{ position: 'absolute', inset: 0 }} />
}
