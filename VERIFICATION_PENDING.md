# Pending manual verification

Browser automation is currently blocked in the development environment used
for this project (no MCP browser tool registered, and Playwright install
fails on a TLS/CA certificate-revocation trust gap in that sandbox). The
items below were implemented and verified at the code/data level, but still
need a human to click through `npm run dev` in an actual browser before
they're fully confirmed. Check each box after confirming.

- [ ] Hot-end color ramp: toggle CMIP6 grid, 2060/2070, confirm a high-latitude
      land cell and a ~3-4°C cell render as visibly distinct maroon shades
- [ ] UK negative-anomaly popup: 2050, hover a UK cell (~50-59°N, -6 to 2°E),
      confirm popup shows a correctly single-signed negative value
- [ ] Precipitation fill renders distinctly (brown/green) from temperature layer
- [ ] Mutual exclusivity: toggling one grid layer off auto-disables the other
- [ ] Year slider updates precipitation fill per decade
- [ ] Legend shows correct units/gradient/captions for whichever layer is active
- [ ] Persistent "Data: MRI-ESM2-0..." caption visible regardless of active layer
- [ ] "i" button opens InfoPanel with single-model text + AR6 global figure; closes correctly
- [ ] URL round-trip: reload with `?layers=precipGrid` restores correctly
- [ ] Base-path check: `npm run build && npm run preview`, confirm data files
      resolve under `/climate-atlas/`
