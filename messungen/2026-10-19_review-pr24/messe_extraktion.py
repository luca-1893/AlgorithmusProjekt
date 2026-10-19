"""Vergleicht PDF-Extraktoren mit der LaTeX-Quelle als Referenz.

Für Paper aus den 8 Testanfragen, die eine LaTeX-Quelle haben:
- Referenz:  LaTeX-Quelle (export.arxiv.org/src/<id>) -> pandoc -> Text, ohne Literaturverzeichnis
- Kandidaten: pypdf (Stand jetzt), pymupdf4llm, docling, GROBID (nur wenn GROBID_URL gesetzt ist)
Fehlt ein Paket, wird der Extraktor übersprungen.

Kennzahlen pro Paper und Extraktor (Tokens über bm25.tokenize):
- recall:      Anteil der Referenz-Tokens, die der Extraktor wiederfindet (Multimenge)
- precision:   Anteil der Extraktor-Tokens, die auch in der Referenz stehen
- unbekannt:   Anteil der Extraktor-Tokens, deren Wort in der Referenz gar nicht vorkommt
               (zerrissene Wörter wie "ev ans", Kopfzeilen, Formelreste)
- suchterme:   Anteil der Vorkommen der Suchbegriffe aus der Referenz, die der Extraktor wiederfindet
- sekunden:    Laufzeit der Extraktion

Aufruf aus dem Repo-Root:
    python messe_extraktion.py src messung_extraktion/ [max_paper]
Downloads landen in messung_extraktion/raw/, ein zweiter Lauf lädt nichts neu.
"""
import gzip, io, json, os, re, statistics, subprocess, sys, tarfile, time, urllib.request, uuid
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from bm25 import tokenize
from pipeline import PipelineConfig
from sources import ArxivSource, normalize_keywords
from sources.sources import USER_AGENT

OUT = Path(sys.argv[2])
MAX_PAPER = int(sys.argv[3]) if len(sys.argv) > 3 else 25
RAW = OUT / "raw"
RAW.mkdir(parents=True, exist_ok=True)
GROBID_URL = os.environ.get("GROBID_URL", "")

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
PAUSE = 3.1
REFS_HEADING = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*)?(?:\*\*)?[ \t]*(?:\d+\.?[ \t]*)?(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY)\b",
    re.MULTILINE)


def log(*parts):
    print(time.strftime("%H:%M:%S"), *parts, flush=True)


_last = [0.0]
def get(url, timeout=60):
    """GET mit mindestens PAUSE Sekunden Abstand zwischen allen arXiv-Anfragen."""
    wait = PAUSE - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def cached_download(url, path):
    if not path.exists():
        path.write_bytes(get(url))
    return path.read_bytes()


def cut_references(text):
    """Schneidet ab der letzten Überschrift References/Bibliography ab, wenn sie in der zweiten Hälfte steht."""
    hits = list(REFS_HEADING.finditer(text))
    if hits and hits[-1].start() > len(text) * 0.5:
        return text[:hits[-1].start()]
    return text


# --- Referenz: LaTeX-Quelle -> pandoc ---------------------------------------------------------

def latex_files(raw):
    """Gibt {Pfad: Inhalt} aller .tex-Dateien zurück, oder {} wenn die Quelle kein LaTeX ist."""
    if raw[:4] == b"%PDF":
        return {}
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:*") as tar:
            return {os.path.normpath(m.name): tar.extractfile(m).read().decode("utf-8", "replace")
                    for m in tar.getmembers() if m.isfile() and m.name.endswith(".tex")}
    except tarfile.TarError:
        pass
    try:
        text = gzip.decompress(raw).decode("utf-8", "replace")
    except OSError:
        text = raw.decode("utf-8", "replace")
    return {"main.tex": text} if "\\documentclass" in text else {}


def inline_inputs(text, files, base, depth=0):
    """Ersetzt \\input{x} und \\include{x} durch den Dateiinhalt."""
    if depth > 5:
        return text

    def replace(match):
        name = match.group(1).strip()
        for candidate in (name, name + ".tex"):
            path = os.path.normpath(os.path.join(base, candidate))
            if path in files:
                return inline_inputs(files[path], files, base, depth + 1)
        return ""
    return re.sub(r"\\(?:input|include)\{([^}]+)\}", replace, text)


def reference_text(raw):
    files = latex_files(raw)
    mains = [p for p, t in files.items() if "\\documentclass" in t and "\\begin{document}" in t]
    if not mains:
        return ""
    main = max(mains, key=lambda p: len(files[p]))
    tex = inline_inputs(files[main], files, os.path.dirname(main))
    tex = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}", "", tex, flags=re.DOTALL)
    tex = re.sub(r"\\bibliography\{[^}]*\}", "", tex)
    result = subprocess.run(["pandoc", "-f", "latex", "-t", "plain", "--wrap=none", "--quiet"],
                            input=tex, capture_output=True, text=True, timeout=120)
    return cut_references(result.stdout)


# --- Kandidaten -------------------------------------------------------------------------------

def extract_pypdf(pdf_path):
    from pypdf import PdfReader
    text = "\n".join((page.extract_text() or "") for page in PdfReader(str(pdf_path)).pages)
    text = cut_references(text)
    return re.sub(r"-\n(\w)", r"\1", text)


def extract_pymupdf4llm(pdf_path):
    import pymupdf4llm
    return cut_references(pymupdf4llm.to_markdown(str(pdf_path)))


_docling = []
def extract_docling(pdf_path):
    if not _docling:
        from docling.document_converter import DocumentConverter
        _docling.append(DocumentConverter())
    return cut_references(_docling[0].convert(str(pdf_path)).document.export_to_markdown())


def extract_grobid(pdf_path):
    if not GROBID_URL:
        raise ImportError("GROBID_URL nicht gesetzt")
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"input\"; filename=\"paper.pdf\"\r\n"
            f"Content-Type: application/pdf\r\n\r\n").encode() + pdf_path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(f"{GROBID_URL.rstrip('/')}/api/processFulltextDocument", data=body,
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(request, timeout=300) as response:
        root = ET.fromstring(response.read())
    tei = "{http://www.tei-c.org/ns/1.0}"
    parts = [root.find(f".//{tei}profileDesc/{tei}abstract"), root.find(f".//{tei}text/{tei}body")]
    return "\n".join(" ".join(part.itertext()) for part in parts if part is not None)


EXTRACTORS = {
    "pypdf": extract_pypdf,
    "pymupdf4llm": extract_pymupdf4llm,
    "docling": extract_docling,
    "grobid": extract_grobid,
}


# --- Kennzahlen -------------------------------------------------------------------------------

def compare(reference, candidate, terms):
    ref, cand = Counter(tokenize(reference)), Counter(tokenize(candidate))
    common = sum((ref & cand).values())
    ref_terms = sum(ref[t] for t in terms)
    return {
        "recall": round(common / sum(ref.values()), 3) if ref else 0.0,
        "precision": round(common / sum(cand.values()), 3) if cand else 0.0,
        "unbekannt": round(sum(c for t, c in cand.items() if t not in ref) / sum(cand.values()), 3) if cand else 0.0,
        "suchterme": round(sum(min(ref[t], cand[t]) for t in terms) / ref_terms, 3) if ref_terms else None,
    }


def main():
    log(f"Extraktoren: {', '.join(EXTRACTORS)}; GROBID_URL={GROBID_URL or '-'}; max_paper={MAX_PAPER}")
    source = ArxivSource(fetch=lambda url: get(url).decode("utf-8"))
    papers = []
    for query in QUERIES:
        keywords = normalize_keywords(query)
        for document in source.search(keywords, PipelineConfig().max_documents):
            if document.id not in {p[0] for p in papers}:
                papers.append((document.id, keywords))
    log(f"{len(papers)} Paper aus {len(QUERIES)} Anfragen")

    unavailable, results = {}, []
    for doc_id, keywords in papers:
        if len(results) >= MAX_PAPER:
            break
        safe = doc_id.replace("/", "_")
        try:
            raw_src = cached_download(f"https://export.arxiv.org/src/{doc_id}", RAW / f"{safe}.src")
            reference = reference_text(raw_src)
        except Exception as error:
            log(f"{doc_id}: Quelle nicht verwendbar ({type(error).__name__}: {error})")
            continue
        if len(reference.split()) < 500:
            log(f"{doc_id}: keine brauchbare LaTeX-Quelle, übersprungen")
            continue
        try:
            pdf_path = RAW / f"{safe}.pdf"
            cached_download(f"https://export.arxiv.org/pdf/{doc_id}", pdf_path)
        except Exception as error:
            log(f"{doc_id}: PDF nicht ladbar ({error})")
            continue

        terms = set(tokenize(" ".join(keywords)))
        row = {"id": doc_id, "query": keywords, "referenz_woerter": len(reference.split()), "extraktoren": {}}
        for name, extract in EXTRACTORS.items():
            if name in unavailable:
                continue
            start = time.perf_counter()
            try:
                text = extract(pdf_path)
            except ImportError as error:
                unavailable[name] = str(error)
                log(f"{name}: nicht verfügbar ({error}), wird übersprungen")
                continue
            except Exception as error:
                log(f"{doc_id} {name}: Fehler ({type(error).__name__}: {error})")
                continue
            metrics = compare(reference, text, terms)
            metrics["sekunden"] = round(time.perf_counter() - start, 2)
            row["extraktoren"][name] = metrics
        results.append(row)
        log(json.dumps(row, ensure_ascii=False))
        (OUT / "ergebnis_extraktion.json").write_text(json.dumps(results, ensure_ascii=False, indent=1))

    print()
    print(f"{len(results)} Paper mit LaTeX-Quelle ausgewertet")
    print(f"{'Extraktor':<12} {'Paper':>5} {'recall':>7} {'precision':>9} {'unbekannt':>9} {'suchterme':>9} {'s/Paper':>8}")
    for name in EXTRACTORS:
        rows = [r["extraktoren"][name] for r in results if name in r["extraktoren"]]
        if not rows:
            print(f"{name:<12} {'-':>5}   {unavailable.get(name, 'keine Ergebnisse')}")
            continue
        median = lambda key: statistics.median(m[key] for m in rows if m[key] is not None)
        print(f"{name:<12} {len(rows):>5} {median('recall'):>7.1%} {median('precision'):>9.1%} "
              f"{median('unbekannt'):>9.1%} {median('suchterme'):>9.1%} {median('sekunden'):>8.2f}")
    print("(Mediane über die Paper)")


if __name__ == "__main__":
    main()
