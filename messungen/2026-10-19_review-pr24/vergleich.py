import json, sys
from pathlib import Path
D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
R = D / "referenz"; A = D / "ausgaben"

def lines(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.startswith("{")]

print("## Vorauswahl auf Abstracts (PR-Kommentar → lokal)")
ref = {tuple(x["query"]): x for x in lines(R / "vorauswahl_pr.log")}
loc = {tuple(x["query"]): x for x in lines(A / "vorauswahl.log")}
print(f"{'Anfrage':<48} {'Stufe':>5} {'Chunks':>11} {'top_m':>9} {'durch m ab':>11} IDF Hauptterm")
for q, r in ref.items():
    l = loc.get(q)
    for s in ("20", "50", "100"):
        a, b = r["stufen"][s], (l["stufen"][s] if l else None)
        t = max(a["df"], key=a["df"].get)
        f = lambda key, x: "-" if x is None else x[key]
        print(f"{' '.join(q)[:48]:<48} {s:>5} {a['chunks']:>4} → {f('chunks', b):<4} {a['top_m']:>3} → {f('top_m', b):<3} "
              f"{a['abgeschnitten_durch_m']:>4} → {f('abgeschnitten_durch_m', b):<4} {t}: {a['idf'][t]} → {b['idf'].get(t) if b else '-'}")

print("\n## Abstract gegen Volltext (PR-Kommentar → lokal)")
ref = {tuple(x["query"]): x for x in lines(R / "volltext_pr.log")}
loc = {tuple(x["query"]): x for x in lines(A / "volltext.log")}
print(f"{'Anfrage':<48} {'Quellen html/pdf/fehlt':>24} {'Chunks Volltext':>16} {'aussortiert':>13} {'Paper in top_m':>15}")
for q, r in ref.items():
    l = loc.get(q)
    qs = lambda x: "/".join(str(x["quellen"][k]) for k in ("html", "pdf", "fehlt"))
    if not l:
        print(f"{' '.join(q)[:48]:<48} fehlt lokal"); continue
    print(f"{' '.join(q)[:48]:<48} {qs(r):>10} → {qs(l):<10} {r['volltext']['chunks']:>6} → {l['volltext']['chunks']:<6} "
          f"{r['volltext']['aussortiert_anteil']:.0%} → {l['volltext']['aussortiert_anteil']:.0%}   "
          f"{r['volltext']['dokumente_in_top_m']:>3} → {l['volltext']['dokumente_in_top_m']}")
