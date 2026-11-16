"""Wie wirkt overlap beim Chunking? Gemessen auf den Volltexten aus messe_volltext.py (cache/).

Pro overlap und Anfrage:
- chunks:          Anzahl Chunks (Kosten für Index, ggf. Einbettung aller Chunks in der DB)
- saetze_ganz:     Anteil der relevanten Sätze (>= 2 verschiedene Suchterme), die vollständig
                   in mindestens einem Chunk liegen, also nicht von einer Chunkgrenze zerschnitten werden
- fenster_ganz:    dasselbe für relevante 3-Satz-Fenster (Satz mit Vorgänger und Nachfolger)
- top_m_doppelt:   Anteil der Wörter in den Top-m-Chunks, die doppelt drin sind, weil sich zwei
                   ausgewählte Chunks überlappen (verschwendete Tokens/Einbettungen)
- top_m_nachbarn:  Anteil der Top-m-Chunks, deren direkter Nachbar (gleiches Dokument) auch in Top-m ist
- kurz:            Anteil der Chunks unter 50 Wörtern (Rest-Chunks am Dokumentende)
- kurz_in_top_m:   wie viele davon BM25 unter die Top m wählt
"""
import json, re, statistics, sys, time
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from bm25 import build_index, tokenize, top_m
from chunking import create_chunks
from pipeline import PipelineConfig
from sources import ArxivSource, normalize_keywords

CACHE = Path(sys.argv[2])
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
OVERLAPS = [int(x) for x in sys.argv[3].split(",")]
CHUNK_SIZE = int(sys.argv[4]) if len(sys.argv) > 4 else 200
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def starts(n_words, size, overlap):
    """Startpositionen wie split_into_chunks."""
    step, start, result = size - overlap, 0, []
    while start < n_words:
        result.append(start)
        if start + size >= n_words:
            break
        start += step
    return result


def contained(span_start, span_len, chunk_starts, size):
    return any(s <= span_start and span_start + span_len <= s + size for s in chunk_starts)


def relevant_spans(text, terms):
    """(Startwort, Länge) relevanter Sätze und 3-Satz-Fenster."""
    sentences = [s for s in SENTENCE.split(text) if s.strip()]
    lengths = [len(s.split()) for s in sentences]
    pos = [0]
    for length in lengths:
        pos.append(pos[-1] + length)
    rel = [i for i, s in enumerate(sentences) if len(set(tokenize(s)) & terms) >= 2]
    saetze = [(pos[i], lengths[i]) for i in rel if lengths[i] <= CHUNK_SIZE]
    fenster = []
    for i in rel:
        a, b = max(0, i - 1), min(len(sentences), i + 2)
        if pos[b] - pos[a] <= CHUNK_SIZE:
            fenster.append((pos[a], pos[b] - pos[a]))
    return saetze, fenster


source = ArxivSource()
docs_per_query = []
for q in QUERIES:
    kw = normalize_keywords(q)
    docs = source.search(kw, PipelineConfig().max_documents)
    texts = []
    for d in docs:
        f = CACHE / f"{d.id.replace('/', '_')}.json"
        art, text = json.loads(f.read_text()) if f.exists() else ("fehlt", "")
        texts.append((d.id, f"{d.title}\n\n{text}" if text else d.text))
    docs_per_query.append((kw, texts))
    time.sleep(3.5)

print(f"chunk_size={CHUNK_SIZE}, m={PipelineConfig().candidates_m}, {sum(len(t) for _, t in docs_per_query)} Dokumente")
print(f"{'overlap':>7} {'chunks':>7} {'saetze_ganz':>11} {'fenster_ganz':>12} {'top_m_doppelt':>13} {'top_m_nachbarn':>14} {'kurz':>6} {'kurz_in_top_m':>13}")
for overlap in OVERLAPS:
    agg = {k: [] for k in ("chunks", "saetze", "fenster", "doppelt", "nachbarn", "kurz", "kurz_top")}
    for kw, texts in docs_per_query:
        terms = set(tokenize(" ".join(kw)))
        chunks, s_ok, s_all, f_ok, f_all = [], 0, 0, 0, 0
        for doc_id, text in texts:
            cs = create_chunks(doc_id, text, CHUNK_SIZE, overlap)
            chunks += cs
            st = starts(len(text.split()), CHUNK_SIZE, overlap)
            saetze, fenster = relevant_spans(text, terms)
            s_ok += sum(contained(p, l, st, CHUNK_SIZE) for p, l in saetze); s_all += len(saetze)
            f_ok += sum(contained(p, l, st, CHUNK_SIZE) for p, l in fenster); f_all += len(fenster)
        index, lengths, n, avgdl = build_index([c.text for c in chunks])
        hits = [chunks[p] for p, _ in top_m(" ".join(kw), index, lengths, n, avgdl, PipelineConfig().candidates_m)]
        chosen = {(c.document_id, c.position) for c in hits}
        nachbarn = sum(1 for c in hits if (c.document_id, c.position + 1) in chosen or (c.document_id, c.position - 1) in chosen)
        doppelt_woerter = sum(overlap for c in hits if (c.document_id, c.position + 1) in chosen)
        alle_woerter = sum(len(c.text.split()) for c in hits)
        agg["chunks"].append(len(chunks))
        agg["saetze"].append(s_ok / s_all if s_all else 1)
        agg["fenster"].append(f_ok / f_all if f_all else 1)
        agg["doppelt"].append(doppelt_woerter / alle_woerter if alle_woerter else 0)
        agg["nachbarn"].append(nachbarn / len(hits) if hits else 0)
        agg["kurz"].append(sum(len(c.text.split()) < 50 for c in chunks) / len(chunks))
        agg["kurz_top"].append(sum(len(c.text.split()) < 50 for c in hits))
    m = {k: statistics.mean(v) for k, v in agg.items()}
    print(f"{overlap:>7} {sum(agg['chunks']):>7} {m['saetze']:>11.1%} {m['fenster']:>12.1%} {m['doppelt']:>13.1%} "
          f"{m['nachbarn']:>14.1%} {m['kurz']:>6.1%} {sum(agg['kurz_top']):>13}", flush=True)
