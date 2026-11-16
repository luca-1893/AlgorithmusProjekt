"""Vergleicht die BM25-Vorauswahl auf Abstracts mit derselben auf Volltexten.

Pro Anfrage: die 20 besten arXiv-Dokumente (wie PipelineConfig), Volltext per HTML
(export.arxiv.org/html), sonst PDF (export.arxiv.org/pdf); Literaturverzeichnis wird entfernt.
Downloads werden in cache/ abgelegt, damit ein zweiter Lauf nichts neu lädt.
"""
import io, json, re, statistics, sys, time, urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from bm25 import build_index, compute_idf, tokenize, top_m
from chunking import create_chunks
from pipeline import PipelineConfig
from sources import ArxivSource, normalize_keywords
from sources.sources import USER_AGENT

CACHE = Path(sys.argv[2])
OUT = Path(sys.argv[3])
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
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SKIP_TAGS = {"script", "style", "math", "nav", "header", "footer", "svg", "figure", "table"}
SKIP_CLASSES = ("ltx_bibliography", "ltx_page_footer", "ltx_page_header", "ltx_authors", "ltx_role_footnote")

_last = [0.0]
def get(url):
    wait = PAUSE - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(), r.headers.get("Content-Type", "")


class ArticleText(HTMLParser):
    """Text aus <article> (LaTeXML), ohne Formeln, Tabellen, Abbildungen und Literaturverzeichnis."""
    def __init__(self):
        super().__init__()
        self.in_article = 0
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        cls = dict(attrs).get("class") or ""
        if self.skip:
            self.skip += 1
            return
        if tag == "article":
            self.in_article += 1
        if self.in_article and (tag in SKIP_TAGS or any(c in cls for c in SKIP_CLASSES)):
            self.skip = 1

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.skip:
            self.skip -= 1
            return
        if tag == "article":
            self.in_article -= 1
        if tag in ("p", "div", "section", "h1", "h2", "h3", "h4", "li"):
            self.parts.append("\n")

    def handle_data(self, data):
        if self.in_article and not self.skip:
            self.parts.append(data)


def html_text(raw):
    p = ArticleText()
    p.feed(raw.decode("utf-8", "replace"))
    return " ".join("".join(p.parts).split())


def pdf_text(raw):
    from pypdf import PdfReader
    text = "\n".join((page.extract_text() or "") for page in PdfReader(io.BytesIO(raw)).pages)
    hits = list(re.finditer(r"\n\s*(References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*\n", text))
    if hits and hits[-1].start() > len(text) * 0.5:
        text = text[:hits[-1].start()]
    text = re.sub(r"-\n(\w)", r"\1", text)  # Silbentrennung am Zeilenende
    return " ".join(text.split())


def fulltext(doc_id):
    """Gibt (art, text) zurück; art ist html, pdf oder fehlt."""
    safe = doc_id.replace("/", "_")
    cached = CACHE / f"{safe}.json"
    if cached.exists():
        return tuple(json.loads(cached.read_text()))
    result = ("fehlt", "")
    try:
        raw, ctype = get(f"https://export.arxiv.org/html/{doc_id}")
        if "html" in ctype:
            text = html_text(raw)
            if len(text.split()) > 500:
                result = ("html", text)
    except Exception:
        pass
    if result[0] == "fehlt":
        try:
            raw, ctype = get(f"https://export.arxiv.org/pdf/{doc_id}")
            if raw[:4] == b"%PDF":
                text = pdf_text(raw)
                if len(text.split()) > 500:
                    result = ("pdf", text)
        except Exception as error:
            print("   PDF-Fehler", doc_id, error, file=sys.stderr)
    cached.write_text(json.dumps(result))
    return result


def auswerten(texte, kw, cfg):
    chunks = [c for doc_id, text in texte for c in create_chunks(doc_id, text, cfg.chunk_size, cfg.overlap)]
    index, lengths, n, avgdl = build_index([c.text for c in chunks])
    hits = top_m(" ".join(kw), index, lengths, n, avgdl, cfg.candidates_m)
    terms = sorted(set(tokenize(" ".join(kw))))
    mit_schlagwort = sum(1 for c in chunks if set(tokenize(c.text)) & set(terms))
    return {
        "chunks": len(chunks),
        "mit_schlagwort": mit_schlagwort,
        "top_m": len(hits),
        "aussortiert_anteil": round(1 - len(hits) / len(chunks), 3) if chunks else None,
        "df_anteil": {t: round(len(index.get(t, {})) / n, 2) for t in terms},
        "idf": {t: round(compute_idf(len(index.get(t, {})), n), 2) for t in terms},
        "dokumente_in_top_m": len({chunks[p].document_id for p, _ in hits}),
    }


cfg = PipelineConfig()
source = ArxivSource(fetch=lambda url: get(url)[0].decode("utf-8"))
alle = []
for q in QUERIES:
    kw = normalize_keywords(q)
    docs = source.search(kw, cfg.max_documents)
    arten, voll = [], []
    for d in docs:
        art, text = fulltext(d.id)
        arten.append(art)
        voll.append((d.id, f"{d.title}\n\n{text}" if text else d.text))
    zeile = {
        "query": q,
        "docs": len(docs),
        "quellen": {a: arten.count(a) for a in ("html", "pdf", "fehlt")},
        "woerter_median_volltext": statistics.median(len(t.split()) for _, t in voll),
        "abstract": auswerten([(d.id, d.text) for d in docs], kw, cfg),
        "volltext": auswerten(voll, kw, cfg),
    }
    alle.append(zeile)
    print(json.dumps(zeile, ensure_ascii=False), flush=True)
    OUT.write_text(json.dumps(alle, ensure_ascii=False, indent=1))
