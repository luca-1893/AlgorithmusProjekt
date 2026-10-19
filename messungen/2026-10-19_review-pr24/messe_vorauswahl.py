"""Misst, wie viele Chunks die BM25-Vorauswahl (top_m) mit echten arXiv-Daten aussortiert.

Pro Anfrage werden einmal 100 Dokumente geholt (arXiv sortiert nach Relevanz);
ausgewertet werden die ersten 20 (= Standard max_documents), 50 und 100.
"""
import json, statistics, sys, time
sys.path.insert(0, sys.argv[1])  # src-Ordner des PR

from bm25 import build_index, compute_idf, tokenize, top_m
from chunking import create_chunks
from pipeline import PipelineConfig
from sources import ArxivSource, normalize_keywords

QUERIES = [
    ["UML", "class diagram", "semantics"],
    ["BM25", "information retrieval"],
    ["retrieval augmented generation", "hallucination"],
    ["transformer", "attention"],
    ["graph neural network", "molecule"],
    ["reinforcement learning", "robotics", "sim-to-real"],
    ["quantum error correction"],
    ["federated learning", "privacy", "differential privacy"],
]
STUFEN = (20, 50, 100)

def auswerten(docs, kw, cfg):
    chunks = [c for d in docs for c in create_chunks(d.id, d.text, cfg.chunk_size, cfg.overlap)]
    index, lengths, n, avgdl = build_index([c.text for c in chunks])
    hits = top_m(" ".join(kw), index, lengths, n, avgdl, cfg.candidates_m)
    terms = sorted(set(tokenize(" ".join(kw))))
    return {
        "docs": len(docs),
        "chunks": len(chunks),
        "top_m": len(hits),
        "ohne_treffer": len(chunks) - len({p for p, _ in hits}) if len(hits) < cfg.candidates_m else None,
        "abgeschnitten_durch_m": max(0, sum(1 for c in chunks if set(tokenize(c.text)) & set(terms)) - cfg.candidates_m),
        "df": {t: len(index.get(t, {})) for t in terms},
        "idf": {t: round(compute_idf(len(index.get(t, {})), n), 2) for t in terms},
    }

cfg = PipelineConfig()
source = ArxivSource()
print(f"PipelineConfig: max_documents={cfg.max_documents}, chunk_size={cfg.chunk_size}, "
      f"overlap={cfg.overlap}, candidates_m={cfg.candidates_m}\n")
alle = []
for q in QUERIES:
    kw = normalize_keywords(q)
    docs = source.search(kw, max(STUFEN))
    woerter = [len(d.text.split()) for d in docs[:20]]
    zeile = {"query": q, "woerter_median_top20": statistics.median(woerter),
             "woerter_max_top20": max(woerter),
             "stufen": {s: auswerten(docs[:s], kw, cfg) for s in STUFEN}}
    alle.append(zeile)
    print(json.dumps(zeile, ensure_ascii=False), flush=True)
    time.sleep(3.5)  # arXiv bittet um mindestens 3 s Abstand

json.dump(alle, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
