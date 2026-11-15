"""Builds Phase4/Testkatalog.md: every unit test with category, input → expected output and actual result."""
import ast
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUTPUT = ROOT / "Phase4" / "Testkatalog.md"
MODULES = ["sources", "chunking", "bm25", "vector_search", "ranking", "pipeline", "mcp_server", "storage"]

ERROR_WORDS = ("error", "fails", "invalid", "unreachable", "missing", "timeout", "rejects",
               "mismatch", "wrong", "bad_", "is_abstract", "immutable", "unequal", "different_lengths",
               "negative_constant", "negative_overlap", "out_of_range", "blank_keywords", "from_after_to",
               "overlap_equals", "overlap_greater", "chunk_size_zero", "k_zero", "max_results_zero",
               "top_k_zero", "mmr_k_zero", "unknown_run", "without_key", "unknown_chunk", "incomplete")
EDGE_WORDS = ("empty", "zero", "only_", "single", "exactly", "no_", "none", "larger_than", "equal", "ties",
              "tie_", "same_day", "negative", "without", "unknown", "whitespace", "old_style", "short",
              "all_equal", "identical", "duplicate", "m_larger", "too_old", "other_model", "other_filter",
              "umlauts", "eszett", "apostrophe", "dash", "hyphen", "quotes", "trailing", "does_not_mutate",
              "does_not_change", "long_document", "lambda_one", "orthogonal", "opposite", "zero_vector",
              "falls_back", "is_normalized", "count_once", "other_order", "replaces", "twice")

OVERRIDES = {
    "test_term_score_k1_zero_missing_term": "edge",
    "test_normalize_min_zero_max_one": "normal",
    "test_tool_k_too_large": "error",
    "test_parse_url_falls_back_to_id": "edge",
}

CATEGORY_NAMES = {"normal": "Normalfall", "edge": "Randfall", "error": "Fehlerfall"}


def category(name: str, source: str) -> str:
    """Error case if the test expects an exception or a failing dependency, edge case for limits, else normal."""
    if name in OVERRIDES:
        return OVERRIDES[name]
    if "assertRaises" in source or any(word in name for word in ERROR_WORDS):
        return "error"
    if any(word in name for word in EDGE_WORDS):
        return "edge"
    return "normal"


def shorten(text: str, limit: int = 140) -> str:
    """One line, at most limit characters, safe inside a Markdown table."""
    text = " ".join(text.split()).replace("|", "\\|")
    return text if len(text) <= limit else text[:limit - 1] + "…"


def describe(function: ast.FunctionDef) -> str:
    """Input → expected output from the first check in the test body."""
    checks = []
    for node in ast.walk(function):
        if isinstance(node, ast.With):
            for item in node.items:
                call = item.context_expr
                if isinstance(call, ast.Call) and getattr(call.func, "attr", "").startswith("assertRaises"):
                    body = ast.unparse(node.body[-1]) if node.body else ""
                    checks.append((node.lineno, f"{body} → {ast.unparse(call.args[0])}"))
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "").startswith("assert"):
            name = node.func.attr
            if name.startswith("assertRaises"):
                if len(node.args) > 1:
                    checks.append((node.lineno, f"{ast.unparse(node.args[1])}(…) → {ast.unparse(node.args[0])}"))
                continue
            args = [ast.unparse(argument) for argument in node.args]
            if name in ("assertEqual", "assertAlmostEqual", "assertListEqual", "assertDictEqual") and len(args) >= 2:
                checks.append((node.lineno, f"{args[0]} → {args[1]}"))
            elif name in ("assertTrue", "assertFalse", "assertIsNone", "assertIsNotNone") and args:
                expected = {"assertTrue": "wahr", "assertFalse": "falsch", "assertIsNone": "None",
                            "assertIsNotNone": "nicht None"}[name]
                checks.append((node.lineno, f"{args[0]} → {expected}"))
            else:
                checks.append((node.lineno, f"{name}({', '.join(args)})"))
    if not checks:
        return "siehe Testcode"
    checks.sort()
    text = shorten(checks[0][1])
    return text if len(checks) == 1 else f"{text} (+{len(checks) - 1} weitere Prüfungen)"


def collect(module: str) -> list[dict]:
    """All test methods of src/<module>/test_<module>.py in file order."""
    path = SRC / module / f"test_{module}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    tests = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for function in node.body:
            if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)) and function.name.startswith("test_"):
                tests.append({
                    "id": f"{module}.test_{module}.{node.name}.{function.name}",
                    "name": f"{node.name}.{function.name}",
                    "category": category(function.name, ast.unparse(function)),
                    "check": describe(function),
                })
    return tests


class OutcomeResult(unittest.TextTestResult):
    """Remembers the outcome of every test by its id."""

    def startTestRun(self):
        super().startTestRun()
        self.outcomes = {}

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes[test.id()] = "✓ wie erwartet"

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes[test.id()] = "✗ " + shorten(str(err[1]).splitlines()[0], 80)

    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes[test.id()] = "✗ Fehler: " + shorten(str(err[1]).splitlines()[0], 80)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes[test.id()] = f"übersprungen ({reason})"


def run_tests() -> dict[str, str]:
    """Runs the whole suite and returns outcome per test id."""
    sys.path.insert(0, str(SRC))
    suite = unittest.defaultTestLoader.discover(str(SRC), top_level_dir=str(SRC))
    runner = unittest.TextTestRunner(resultclass=OutcomeResult, verbosity=0, stream=open("/dev/null", "w"))
    return runner.run(suite).outcomes


def render(tests_by_module: dict[str, list[dict]], outcomes: dict[str, str]) -> str:
    """Markdown with a summary table and one table per module."""
    lines = [
        "# Testkatalog",
        "",
        f"Automatisch erzeugt mit `Phase4/testkatalog.py` am {date.today().strftime('%d.%m.%Y')}. "
        "Erklärung und ausgewählte Fälle im Detail: `Phase4/Testdokumentation.md`.",
        "",
        "Spalte **Input → erwartet** zeigt die erste Prüfung des Tests; „→ Fehlerklasse“ heißt, der Aufruf muss "
        "genau diesen Fehler werfen. **Tatsächlich** ist das Ergebnis des letzten Laufs: „wie erwartet“ heißt, "
        "das tatsächliche Output stimmt mit dem erwarteten überein.",
        "",
        "## Übersicht",
        "",
        "| Modul | Normalfall | Randfall | Fehlerfall | gesamt | wie erwartet |",
        "|---|---|---|---|---|---|",
    ]
    totals = {"normal": 0, "edge": 0, "error": 0, "all": 0, "passed": 0}
    for module, tests in tests_by_module.items():
        counts = {key: sum(1 for test in tests if test["category"] == key) for key in CATEGORY_NAMES}
        passed = sum(1 for test in tests if outcomes.get(test["id"], "").startswith("✓"))
        for key in CATEGORY_NAMES:
            totals[key] += counts[key]
        totals["all"] += len(tests)
        totals["passed"] += passed
        lines.append(f"| `{module}` | {counts['normal']} | {counts['edge']} | {counts['error']} | "
                     f"{len(tests)} | {passed} |")
    lines.append(f"| **gesamt** | **{totals['normal']}** | **{totals['edge']}** | **{totals['error']}** | "
                 f"**{totals['all']}** | **{totals['passed']}** |")
    for module, tests in tests_by_module.items():
        lines += ["", f"## `{module}`", "", "| Nr. | Test | Kategorie | Input → erwartet | Tatsächlich |",
                  "|---|---|---|---|---|"]
        for number, test in enumerate(tests, start=1):
            outcome = outcomes.get(test["id"], "nicht gelaufen")
            lines.append(f"| {number} | `{test['name']}` | {CATEGORY_NAMES[test['category']]} | "
                         f"`{test['check']}` | {outcome} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    """Collects, runs and writes the catalogue."""
    tests_by_module = {module: collect(module) for module in MODULES}
    outcomes = run_tests()
    OUTPUT.write_text(render(tests_by_module, outcomes), encoding="utf-8")
    print(f"{sum(len(tests) for tests in tests_by_module.values())} Tests nach {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
