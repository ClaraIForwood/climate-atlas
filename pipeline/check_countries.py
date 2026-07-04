import json

with open("../public/data/countries.geojson", encoding="utf-8") as f:
    gj = json.load(f)

unscored = []
for feat in gj["features"]:
    p = feat["properties"]
    if p.get("vulnerability") is None:
        unscored.append(f"{p.get('ISO_A2','??'):6s} {p.get('ADMIN','?')}")
    if p.get("ADMIN") in ("France", "Norway"):
        print(f"CHECK: {p['ADMIN']} vuln={p['vulnerability']} ready={p['readiness']}")

print(f"\nUnscored ({len(unscored)}):")
for u in sorted(unscored):
    print(" ", u)
