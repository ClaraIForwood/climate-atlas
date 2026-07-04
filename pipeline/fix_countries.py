import json
import urllib.request

# Download Natural Earth 110m countries GeoJSON (public domain)
url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
urllib.request.urlretrieve(url, "ne_countries.geojson")

with open("ne_countries.geojson", encoding="utf-8") as f:
    ne = json.load(f)

# Patch ISO_A2 for countries that Natural Earth tags as -99
ISO_A2_PATCHES = {
    "Norway":  "NO",  # Natural Earth 110m tags Norway as -99
    "France":  "FR",  # Same issue
    # Singapore (SG) is absent from the 110m file — too small to polygon at this scale
    # United Arab Emirates already has ISO_A2="AE" in current Natural Earth release
}
for feature in ne["features"]:
    props = feature["properties"]
    name = props.get("ADMIN", "") or props.get("NAME", "")
    if name in ISO_A2_PATCHES:
        props["ISO_A2"] = ISO_A2_PATCHES[name]

# ── ND-GAIN approximate scores (vulnerability 0-1, readiness 0-1) ────────────
# Source: Notre Dame Global Adaptation Initiative rankings, illustrative values
# vulnerability: lower = less exposed; readiness: higher = more adaptive capacity
NDGAIN = {
    # Top-tier readiness
    "NO": (0.22, 0.89), "DK": (0.20, 0.90), "FI": (0.24, 0.87),
    "SE": (0.23, 0.88), "CH": (0.18, 0.92), "NZ": (0.22, 0.87),
    "AU": (0.26, 0.83), "CA": (0.24, 0.85), "NL": (0.25, 0.84),
    "DE": (0.26, 0.83), "AT": (0.24, 0.84), "GB": (0.28, 0.82),
    "BE": (0.24, 0.83), "FR": (0.28, 0.80), "IE": (0.25, 0.81),
    "IS": (0.20, 0.89), "LU": (0.22, 0.86), "JP": (0.30, 0.76),
    # High readiness
    "US": (0.32, 0.78), "KR": (0.28, 0.78), "ES": (0.27, 0.78),
    "IT": (0.29, 0.76), "PT": (0.28, 0.74), "IL": (0.32, 0.76),
    "CZ": (0.28, 0.77), "SI": (0.27, 0.78), "SK": (0.30, 0.74),
    "EE": (0.26, 0.79), "LV": (0.28, 0.76), "LT": (0.28, 0.75),
    "PL": (0.30, 0.72), "HU": (0.32, 0.70), "HR": (0.32, 0.70),
    "AE": (0.35, 0.72), "QA": (0.38, 0.72), "KW": (0.40, 0.70),
    "SA": (0.42, 0.68), "OM": (0.44, 0.64), "BH": (0.38, 0.70),
    "SG": (0.30, 0.82), "MY": (0.38, 0.62), "CL": (0.40, 0.62),
    # Medium readiness
    "GR": (0.33, 0.70), "RO": (0.36, 0.65), "BG": (0.35, 0.65),
    "RS": (0.36, 0.64), "AL": (0.40, 0.58), "MK": (0.40, 0.58),
    "BY": (0.36, 0.62), "UA": (0.38, 0.58), "MD": (0.40, 0.56),
    "GE": (0.42, 0.56), "AM": (0.44, 0.54), "AZ": (0.44, 0.54),
    "KZ": (0.40, 0.58), "UZ": (0.48, 0.48), "TM": (0.50, 0.44),
    "MN": (0.44, 0.54), "RU": (0.36, 0.66), "TR": (0.40, 0.62),
    "CN": (0.38, 0.62), "BR": (0.44, 0.55), "MX": (0.45, 0.54),
    "AR": (0.42, 0.58), "CO": (0.46, 0.53), "PE": (0.47, 0.51),
    "EC": (0.48, 0.50), "BO": (0.50, 0.46), "PY": (0.48, 0.50),
    "VE": (0.50, 0.40), "CU": (0.44, 0.54), "CR": (0.40, 0.60),
    "PA": (0.42, 0.58), "DO": (0.46, 0.54), "JM": (0.48, 0.52),
    "MA": (0.49, 0.50), "TN": (0.50, 0.50), "DZ": (0.50, 0.46),
    "LY": (0.50, 0.42), "JO": (0.48, 0.52), "LB": (0.46, 0.50),
    "IR": (0.45, 0.50), "IQ": (0.55, 0.38), "SY": (0.60, 0.28),
    "YE": (0.78, 0.20), "AF": (0.76, 0.22), "PK": (0.58, 0.40),
    "LK": (0.50, 0.48), "NP": (0.60, 0.38), "BT": (0.52, 0.48),
    "VN": (0.48, 0.50), "KH": (0.58, 0.40), "LA": (0.56, 0.40),
    "MM": (0.60, 0.36), "IN": (0.56, 0.46), "BD": (0.68, 0.36),
    "TH": (0.50, 0.50), "PH": (0.58, 0.44), "ID": (0.54, 0.46),
    "TL": (0.64, 0.34), "PG": (0.62, 0.34), "FJ": (0.56, 0.44),
    # Low readiness
    "EG": (0.55, 0.44), "SD": (0.72, 0.28), "SS": (0.80, 0.18),
    "ET": (0.68, 0.32), "SO": (0.82, 0.18), "DJ": (0.70, 0.30),
    "ER": (0.74, 0.24), "KE": (0.65, 0.38), "TZ": (0.65, 0.36),
    "UG": (0.65, 0.34), "RW": (0.62, 0.40), "BI": (0.76, 0.24),
    "CD": (0.76, 0.24), "CG": (0.64, 0.34), "CF": (0.82, 0.16),
    "CM": (0.68, 0.32), "GA": (0.56, 0.46), "GQ": (0.60, 0.36),
    "NG": (0.72, 0.30), "GH": (0.60, 0.40), "CI": (0.64, 0.36),
    "BF": (0.74, 0.26), "ML": (0.78, 0.22), "NE": (0.80, 0.20),
    "TD": (0.80, 0.18), "MR": (0.70, 0.28), "SN": (0.62, 0.40),
    "GM": (0.68, 0.34), "GW": (0.76, 0.24), "GN": (0.74, 0.26),
    "SL": (0.72, 0.28), "LR": (0.72, 0.26), "TG": (0.68, 0.32),
    "BJ": (0.66, 0.34), "AO": (0.64, 0.34), "ZM": (0.65, 0.36),
    "ZW": (0.65, 0.33), "MZ": (0.72, 0.28), "MW": (0.72, 0.28),
    "MG": (0.70, 0.28), "TZ": (0.65, 0.36), "NA": (0.54, 0.48),
    "BW": (0.52, 0.50), "ZA": (0.52, 0.48), "LS": (0.64, 0.36),
    "SZ": (0.60, 0.38), "MU": (0.44, 0.60), "MV": (0.54, 0.52),
    # Central America & Caribbean
    "GT": (0.56, 0.44), "HN": (0.58, 0.40), "SV": (0.56, 0.46),
    "NI": (0.56, 0.44), "BZ": (0.52, 0.52), "HT": (0.74, 0.26),
    "TT": (0.48, 0.56), "BS": (0.52, 0.56), "GY": (0.52, 0.48),
    "SR": (0.52, 0.48), "UY": (0.42, 0.62),
    # Balkans / Eastern Europe
    "BA": (0.40, 0.58), "ME": (0.38, 0.60), "KP": (0.60, 0.26),
    # Central Asia
    "KG": (0.52, 0.44), "TJ": (0.58, 0.40),
    # Pacific / Other
    "SB": (0.60, 0.36), "VU": (0.62, 0.36), "CY": (0.30, 0.72),
    "BN": (0.42, 0.64), "PS": (0.62, 0.38), "PR": (0.38, 0.68),
    # Name-based fallbacks for Natural Earth -99 ISO codes
    # (handled separately below)
}

# Name-based fallback for countries where NE has ISO_A2 = -99
NAME_FALLBACK = {
    "France":             ("FR", (0.28, 0.80)),
    "Norway":             ("NO", (0.22, 0.89)),
    "Finland":            ("FI", (0.24, 0.87)),  # in case
    "Northern Cyprus":    (None, (0.38, 0.55)),
    "Kosovo":             (None, (0.44, 0.50)),
    "Somaliland":         (None, (0.82, 0.18)),
}

matched = 0
for feature in ne["features"]:
    p = feature["properties"]
    iso = (p.get("ISO_A2") or "").strip().upper()
    admin = (p.get("ADMIN") or p.get("NAME") or "").strip()

    vuln, ready = None, None

    if iso and iso != "-99" and iso in NDGAIN:
        vuln, ready = NDGAIN[iso]
        matched += 1
    elif admin in NAME_FALLBACK:
        _, scores = NAME_FALLBACK[admin]
        vuln, ready = scores
        matched += 1

    p["vulnerability"] = vuln
    p["readiness"] = ready

print(f"Matched {matched} / {len(ne['features'])} countries")

with open("../public/data/countries.geojson", "w", encoding="utf-8") as f:
    json.dump(ne, f, separators=(",", ":"))

print("Written to public/data/countries.geojson")
