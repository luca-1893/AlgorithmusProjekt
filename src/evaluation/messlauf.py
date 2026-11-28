"""Measurement runs for the KPI evaluation: every question in every variant, stored in the table runs."""
import argparse
import json
import re
import time
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Optional

from anthropic import Anthropic, beta_tool

from mcp_server.mcp_server import MAX_K, parse_date
from pipeline import PipelineConfig, research
from sources import ArxivSource, SearchFilter, Source, SourceError
from storage.storage import Run, connect, rate_run, save_run
from vector_search import Embedder, VoyageEmbedder

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS_FILE = ROOT / "docs" / "evaluation" / "testfragen.md"
LOG_DIR = ROOT / "messungen"
VARIANTS = ("agent_websearch", "bm25", "hybrid")
MODEL = "claude-opus-5-5"
MAX_TOKENS = 16000
MAX_ITERATIONS = 10
DEFAULT_K = 5
ARXIV_PAUSE_S = 3.0
WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search"}
SYSTEM = (
    "Answer the question with the help of scientific papers. Research before you answer and do not rely on memory. "
    "Answer briefly in the language of the question. End with a line 'Quellen:' followed by the arXiv URLs "
    "of the papers your answer is based on."
)
PROBE_PREFIX = "[Probe] "
VOLLTEXT_PREFIX = "[Volltext] "
ARXIV_ID = re.compile(r"(?<![\d.])\d{4}\.\d{4,5}(?!\d)")


@dataclass(frozen=True)
class Question:
    """One measurement question from testfragen.md."""
    number: str
    text: str
    language: str
    expected_id: str


@dataclass(frozen=True)
class Measurement:
    """A finished run together with what is needed to check it by hand."""
    run: Run
    answer: str
    found_source: bool
    tool_calls: tuple[dict, ...]
    stop_reason: str


def load_questions(path: Path = QUESTIONS_FILE) -> list[Question]:
    """Reads the rows F01 to F25 of the question table."""
    questions = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if re.fullmatch(r"F\d\d", cells[0]) and len(cells) >= 4 and ARXIV_ID.fullmatch(cells[3]):
            questions.append(Question(cells[0], cells[1], cells[2], cells[3]))
    return questions


def found_source(answer: str, expected_id: str) -> bool:
    """True if the expected arXiv id is cited in the answer, with or without version."""
    return expected_id in ARXIV_ID.findall(answer)


def research_tool(source: Source, embedder: Optional[Embedder], config: PipelineConfig, calls: list[dict]):
    """The research_papers tool with the same parameters as the MCP server, recording every call."""

    @beta_tool
    def research_papers(keywords: list[str], k: int = DEFAULT_K, question: str = "", published_after: str = "",
                        peer_reviewed_only: bool = False) -> str:
        """Finds scientific papers for the keywords and returns the k most relevant passages with title, authors, date and url.

        Args:
            keywords: 2 to 8 English technical terms, e.g. ['UML', 'class diagram']
            k: Number of passages to return, 1 to 20
            question: The user's original question in any language, improves ranking
            published_after: Only papers first published on or after this date, YYYY or YYYY-MM-DD
            peer_reviewed_only: Only papers with a journal reference or DOI
        """
        calls.append({"keywords": list(keywords), "k": k})
        try:
            if not 1 <= k <= MAX_K:
                raise ValueError(f"k must be between 1 and {MAX_K}")
            search_filter = SearchFilter(published_from=parse_date(published_after), peer_reviewed_only=peer_reviewed_only)
            return json.dumps(research(keywords, k, source, embedder, question, config, search_filter).to_dict(),
                              ensure_ascii=False)
        except (ValueError, SourceError) as error:
            return json.dumps({"error": str(error)})

    return research_papers


def measure(client, question: Question, variant: str, source: Source, embedder: Optional[Embedder],
            model: str = MODEL, config: PipelineConfig = PipelineConfig(),
            clock: Callable[[], float] = time.perf_counter) -> Measurement:
    """Lets the model answer one question in one variant and sums the tokens over all steps."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant: {variant}")
    calls: list[dict] = []
    if variant == "agent_websearch":
        tools = [WEB_SEARCH]
    else:
        tools = [research_tool(source, embedder if variant == "hybrid" else None, config, calls)]

    run_at = datetime.now(timezone.utc)
    start = clock()
    runner = client.beta.messages.tool_runner(
        model=model, max_tokens=MAX_TOKENS, max_iterations=MAX_ITERATIONS, system=SYSTEM,
        thinking={"type": "adaptive"}, tools=tools,
        messages=[{"role": "user", "content": question.text}],
    )
    input_tokens = output_tokens = 0
    last = None
    for message in runner:
        usage = message.usage
        input_tokens += (usage.input_tokens + (usage.cache_creation_input_tokens or 0)
                         + (usage.cache_read_input_tokens or 0))
        output_tokens += usage.output_tokens
        last = message
    duration_ms = round((clock() - start) * 1000)

    answer = "".join(block.text for block in last.content if block.type == "text") if last else ""
    if variant == "agent_websearch":
        keywords, k = None, None
    elif calls:
        keywords, k = calls[0]["keywords"], min(max(calls[0]["k"], 1), MAX_K)
    else:
        keywords, k = [], DEFAULT_K
    run = Run(run_at, variant, question.text, input_tokens, output_tokens, duration_ms, keywords, k)
    return Measurement(run, answer, found_source(answer, question.expected_id), tuple(calls),
                       last.stop_reason if last else "")


def store(connection, measurement: Measurement) -> int:
    """Saves the run and its rating; returns the id of the run."""
    run_id = save_run(connection, measurement.run)
    rate_run(connection, run_id, measurement.found_source)
    return run_id


def log_entry(run_id: int, question: Question, measurement: Measurement) -> dict:
    """One line of the JSON log for checking answers by hand."""
    run = measurement.run
    return {"run_id": run_id, "nr": question.number, "language": question.language, "variant": run.variant,
            "expected_id": question.expected_id, "found_source": measurement.found_source,
            "input_tokens": run.input_tokens, "output_tokens": run.output_tokens, "duration_ms": run.duration_ms,
            "tool_calls": list(measurement.tool_calls), "stop_reason": measurement.stop_reason,
            "answer": measurement.answer}


class ProbeClient:
    """Stands in for the Claude API in a probe run: one tool call, then an answer citing the expected paper."""

    def __init__(self, expected_id: str = ""):
        self.expected_id = expected_id
        self.beta = SimpleNamespace(messages=SimpleNamespace(tool_runner=self.tool_runner))

    def tool_runner(self, tools, messages, **_):
        if not isinstance(tools[0], dict):
            tools[0].call({"keywords": ["probe"], "k": 3})
        text = f"Probelauf ohne API. Quellen: https://arxiv.org/abs/{self.expected_id}"
        usage = SimpleNamespace(input_tokens=100, output_tokens=20, cache_creation_input_tokens=0,
                                cache_read_input_tokens=0)
        return [SimpleNamespace(usage=usage, stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)])]


class ProbeSource(Source):
    """Offline source for a probe run, so no arXiv request is made."""
    name = "probe"

    def search(self, keywords, max_results, search_filter=None):
        return []


def source_for_run(probe: bool, full_text: bool) -> Source:
    """Offline source for a probe, otherwise arXiv without cache, with full texts only if asked (R17)."""
    if probe:
        return ProbeSource()
    return ArxivSource(full_text=full_text)


def mark_full_text(measurement: Measurement) -> Measurement:
    """Prefixes the stored question so full-text runs stay apart from abstract runs in table runs."""
    return replace(measurement, run=replace(measurement.run, question=VOLLTEXT_PREFIX + measurement.run.question))


def main(argv: Optional[list[str]] = None) -> None:
    """Runs the selected questions in the selected variants and stores every run."""
    parser = argparse.ArgumentParser(description="Messläufe für die KPI-Auswertung")
    parser.add_argument("--fragen", default="", help="z. B. F01,F06; leer = alle 25")
    parser.add_argument("--varianten", default=",".join(VARIANTS))
    parser.add_argument("--modell", default=MODEL)
    parser.add_argument("--probe", action="store_true", help="ohne API und arXiv, schreibt trotzdem in runs")
    parser.add_argument("--volltext", action="store_true",
                        help="Tool mit Volltext statt Abstract (ohne Cache); Frage in runs mit Präfix [Volltext]")
    args = parser.parse_args(argv)

    wanted = {number.strip() for number in args.fragen.split(",") if number.strip()}
    questions = [question for question in load_questions() if not wanted or question.number in wanted]
    if args.probe:
        questions = [replace(question, text=PROBE_PREFIX + question.text) for question in questions]
    variants = [variant.strip() for variant in args.varianten.split(",") if variant.strip()]
    embedder = None if args.probe or "hybrid" not in variants else VoyageEmbedder()
    source = source_for_run(args.probe, args.volltext)
    suffix = ("_volltext" if args.volltext else "") + ("_probe" if args.probe else "")
    log_path = LOG_DIR / f"{date.today().isoformat()}_messlauf{suffix}" / "runs.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with connect() as connection, log_path.open("a", encoding="utf-8") as log:
        for question in questions:
            for variant in variants:
                try:
                    client = ProbeClient(question.expected_id) if args.probe else Anthropic()
                    measurement = measure(client, question, variant, source, embedder, args.modell)
                    if args.volltext:
                        measurement = mark_full_text(measurement)
                except Exception as error:
                    print(f"{question.number} {variant}: Fehler {error!r}, Lauf nicht gespeichert")
                    continue
                run_id = store(connection, measurement)
                log.write(json.dumps(log_entry(run_id, question, measurement), ensure_ascii=False) + "\n")
                print(f"{question.number} {variant}: run {run_id}, {measurement.run.input_tokens} Input-Tokens, "
                      f"{measurement.run.duration_ms} ms, Quelle {'gefunden' if measurement.found_source else 'fehlt'}")
                if not args.probe and variant != "agent_websearch":
                    time.sleep(ARXIV_PAUSE_S)
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()
