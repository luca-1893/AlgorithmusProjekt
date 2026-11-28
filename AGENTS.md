# AlgorithmusProjekt agent guide

AlgorithmusProjekt is a hackathon project (FOM module "Algorithmen &
Datenstrukturen", group 2): a rule-based RAG pipeline that searches arXiv,
ranks chunks with BM25 + vector search (RRF, MMR) and hands only the best
passages to a language model through the MCP tool `research_papers`
(Python 3.15, FastMCP, PostgreSQL 18, Voyage embeddings). This file is the
working manual for any coding agent (Claude Code, Codex, OpenCode, ...).
Read it fully before changing code.

- Overview, setup, commands, project status: [README.md](README.md)
- Overall algorithm, decision rules R1–R17, loops, complexity:
  [Phase2/Pseudocode.md](Phase2/Pseudocode.md) (flowchart: `Phase2/Flowchart_RAG-Pipeline.drawio`)
- Per-module design: `docs/<module>/<module>-pseudocode.md` and
  `*-formelsammlung.md` (bm25, chunking, sources, vector_search, ranking,
  pipeline, mcp_server, storage, cache)
- Architecture decisions: `docs/adr/NNNN-*.md` (status, date, who decided)
- Database: [docs/storage/schema-entwurf.md](docs/storage/schema-entwurf.md)
  (decisions E1–E32), [docs/storage/sql-aufgaben.md](docs/storage/sql-aufgaben.md)
  (contract per SQL file), `sql/schema.sql`
- Cache behavior and its decisions C1–C16: [docs/cache/cache-pseudocode.md](docs/cache/cache-pseudocode.md)
- Measurement: questions F01–F25 with expected arXiv id in
  [docs/evaluation/testfragen.md](docs/evaluation/testfragen.md); manual
  check of `runs`: [Phase4/Klicktest-runs.md](Phase4/Klicktest-runs.md)
- Test evidence: [Phase4/Testdokumentation.md](Phase4/Testdokumentation.md);
  `Phase4/Testkatalog.md` is generated, never edit it by hand
- Limitations L1–L10 and reflection: [Phase5/Reflexion.md](Phase5/Reflexion.md)
- What happened and why, per day: [docs/journal.md](docs/journal.md)
- Tasks and phases: GitHub issues and milestones (one milestone per hackathon phase)
- Machine-specific paths and preferences: `AGENTS.local.md` if present.
  It is gitignored; never copy its contents into tracked files.

The repository is the source of truth. Behavior is defined by the rule IDs
(R, E, C) in the docs above; cite them in code docstrings, tests and commit
bodies (`(R16)`, `(C10)`). If a decision made in chat affects behavior, write
it into the pseudocode or an ADR and add a journal line. `docs/journal.md`
and `messungen/` are historical records: append, do not rewrite.

## Talking to the user

- Reply in German. Code, identifiers, docstrings, comments and commit
  messages are English. Project documents (`docs/`, `Phase*/`, README) are
  German, because they are the graded submission. User-facing strings
  returned by the tool (`warnings`, CLI output of `messlauf`) are German.
- This is a learning project. Luca writes the SQL himself and is learning
  it from scratch. Do **not** write or fix files in `sql/` unless he asks
  you to do it for him; otherwise act as tutor (`docs/storage/sql-tutor-prompt.md`):
  name the mistake, ask a guiding question, explain with a toy example.
  When you do it on his behalf, say so in the commit/ADR ("umgesetzt von
  Claude im Auftrag").
- The algorithm modules were built by hand as exercises without libraries.
  Do not replace them with numpy, rank_bm25, LangChain or similar.
- Do not claim results you have not measured. "Tests pass" is not "the
  measurement shows fewer tokens". Numbers in docs come with their source
  (run, date, command).
- Deadlines: Phase 5 (Optimierung & Reflexion) 16.11.2026, pitch 30.11.2026.

## Build, test, run

```bash
python3.15 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m unittest discover -s src -t src                  # all tests, from repo root
python -m coverage run --branch -m unittest discover -s src -t src
python -m coverage report --omit="*/test_*,*/__init__.py"
python Phase4/testkatalog.py                               # regenerates Phase4/Testkatalog.md
```

- Run the full suite after every change. It must end in `OK`.
  Storage/cache tests skip without a reachable `algorithmusprojekt_test`;
  a skip is not a pass. Say how many were skipped. Regenerate the test
  catalogue only with the database running, otherwise skipped tests change it.
- Imports between modules need `src` on the path; always run from the repo
  root with `-s src -t src` or `PYTHONPATH=src`.
- Databases: `algorithmusprojekt_test` for tests (each test runs in a
  rolled-back transaction), `algorithmusprojekt` for the MCP tool and real
  measurements (`DATABASE_URL` overrides). Never write test data into the
  working database.
- `sql/schema.sql` must stay re-runnable (`IF NOT EXISTS`). A changed table
  only arrives after a `DROP` in the test database; never put `DROP` into
  `schema.sql`. Run it twice in a row without errors before committing.
- MCP server: `PYTHONPATH=src .venv/bin/python -m mcp_server` (stdio);
  without `VOYAGE_API_KEY` it runs BM25 only, without a database it runs
  without cache.
- Measurement: `python -m evaluation.messlauf` calls the Claude API and
  arXiv and **costs money**. Never start it without the user's go. Use
  `--probe` (no API, no arXiv, rows prefixed `[Probe]`) or `--fragen F01`
  to check plumbing. The measurement is done without cache on purpose.
- arXiv: keep the pause between requests (`ARXIV_PAUSE_S`); never loop
  live requests in tests. Tests use fakes for `Source`, `Embedder` and the
  Claude client.
- Secrets (`VOYAGE_API_KEY`, `ANTHROPIC_API_KEY`) come from the
  environment. Never write them into files, `.mcp.json` or logs.

### Claude Code cloud sessions

The cloud environment "AlgorithmusProjekt" has a setup script that creates
`.venv` and a local PostgreSQL 16 (user `postgres`, no password) with both
databases and the schema; `DATABASE_URL` and `TEST_DATABASE_URL` point to
it. The server is stopped after setup, start it first:

```bash
su postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/pg/data -l /var/lib/pg/log -o '-c listen_addresses=localhost' -w start"
```

- The Voyage key is injected by the network proxy; `VOYAGE_API_KEY` only
  holds the placeholder `proxy-injected`.
- `ANTHROPIC_API_KEY` must be set by the user as an environment variable
  of the cloud environment (the proxy cannot inject keys for Anthropic
  hosts). The session sets `ANTHROPIC_BASE_URL` to an internal endpoint:
  run the measurement with `env -u ANTHROPIC_BASE_URL`, otherwise the SDK
  does not reach `api.anthropic.com`.
- The databases live in the container and vanish with it. Results that
  matter go into `messungen/<date>_messlauf/` (JSONL log plus a CSV export
  of `runs`) and get committed.

## Architecture in one page

```
src/bm25           tokenizer, inverted index, IDF, BM25 score, top_m (heap)
src/chunking       overlapping word chunks
src/ranking        reciprocal rank fusion, score normalization
src/vector_search  cosine, top-k, MMR, Embedder ABC + VoyageEmbedder
src/sources        Document, SearchFilter, Source ABC + ArxivSource, full text (R17)
src/pipeline       research(): wires the modules, rules R1–R12
src/cache          CachedSource / CachedEmbedder in front of arXiv and Voyage (R13–R16)
src/storage        one function per SQL file in sql/, psycopg 3
src/mcp_server     FastMCP tool research_papers, stdio or HTTP
src/evaluation     measurement runs (Claude API tool runner) into table runs
sql/               one statement per file; sql/uebungen/ = DataGrip test cases
messungen/         dated measurement scripts, logs and results
```

Rules the code already follows; keep them:

1. **Algorithm modules use the standard library only** (bm25, chunking,
   ranking, the math in vector_search). They know nothing about arXiv,
   databases or MCP and are covered at 100 %.
2. **The pipeline depends on abstractions.** `Source` and `Embedder` are
   ABCs; the cache wraps them (decorator), tests inject fakes. New
   providers subclass, they do not add branches to `research()`.
3. **Fail open, never fail the research.** Embedding fails → BM25 only
   with a warning (R10). Database unreachable → no cache, warning "Cache
   nicht verfügbar" (R15). Only invalid input (R1) and an unreachable
   source (R2) are errors. Every fallback adds a German warning to
   `ResearchResult.warnings`.
4. **Deterministic results.** Ties break by smaller position / smaller id
   (R12). No randomness, no dependence on dict or set order.
5. **SQL**: one file per purpose `sql/<name>.sql`, loaded with
   `load_sql("<name>")`, named psycopg placeholders `%(column)s`, never
   string concatenation. Style: keywords upper case, names snake_case,
   named constraints `<table>_invalid_<rule>`, `;` after every statement.
   psycopg sends untyped lists: cast arrays explicitly (`::text[]`).
   Missing values are `NULL`, not `''`.
6. **Storage** wraps every database error in `StorageError`; callers
   decide whether that is fatal. Relevance scores are never stored, they
   depend on the query.
7. **Cache keys**: keywords and categories are casefolded and sorted
   (`normalize_key`); search results keep arXiv's order. Chunks are only
   rewritten when their texts changed, otherwise `CASCADE` deletes stored
   vectors (C10). The question is never cached.
8. **MCP tool contract** (`research_papers` parameters, JSON fields of
   `Hit.to_dict`) is shared with `evaluation/messlauf.py`. Change both or
   neither, and update README and `docs/mcp_server/`.

## Way of working

- Design first, then a failing test, then the code: update the module
  pseudocode (and `Phase2/Pseudocode.md` if a rule changes), write the test
  (it may be committed red: "red until X exists"), then implement.
- Tests: `unittest`, `src/<module>/test_<module>.py`, class per function
  (`TestTopM`), method names that state the case
  (`test_empty_query_returns_nothing`). Hand-calculated reference values
  belong in the formula collection and the test. Name tests so
  `testkatalog.py` can classify them (normal / edge / error words).
- Code style: match surrounding code. Small functions, type hints,
  frozen dataclasses for values, one-line docstrings that say what is
  returned, few comments. PEP 8, lines up to ~120.
- Do not copy code from other RAG projects or libraries; the point is to
  implement the algorithms ourselves. Libraries are only used at the edges
  (FastMCP, psycopg, anthropic).

## Docs to update with a change

- Behavior or rule changed: module pseudocode, `Phase2/Pseudocode.md`
  (rule table), flowchart if the flow changed.
- Non-obvious technical decision with alternatives: new ADR, next number,
  same structure (Status, Datum, Entschieden von, Kontext, Messung or
  Optionen, Entscheidung, Konsequenzen).
- Tests added or removed: regenerate `Phase4/Testkatalog.md`, update
  counts and coverage in `Phase4/Testdokumentation.md` and the "Stand"
  paragraph in README.
- Limitation solved or measured: its L-entry and "Offen bis zum Pitch" in
  `Phase5/Reflexion.md`.
- End of a working session: dated bullet list in `docs/journal.md`
  (what was done, what was learned, next step).

## Git

- Work on `luca-dev`; `master` only gets merged phase results. Do not push
  or open pull requests without being asked.
- One logical change per commit. Subject: Conventional Commits with the
  module as scope, English, lower case, imperative, ~70 chars:
  `feat(cache): reuse stored chunk vectors (R16)`,
  `fix(sql): cast texts to text[] in insert_chunks.sql`,
  `docs(phase4): ...`, `test(bm25): ...`. Body when the why or a measured
  number matters.
- Commit only with a green test suite (red tests only in a `test(...)`
  commit that says so). Code and its docs in the same or the next commit.
- Never commit `.venv/`, `.env`, `messungen/**/cache/`, probe logs or
  DataGrip/PyCharm files (see `.gitignore`).

## When to stop and ask

Stop, write down what you found, and hand back to the user when:

- A choice changes what is measured or how it is rated (variants, model,
  system prompt, partial hits, question set), or the outcome of the pitch.
- A change would alter the schema of an existing table, delete data in
  `algorithmusprojekt`, or change the MCP tool contract.
- The task is SQL Luca wants to write himself (default: assume he does).
- You would spend API credit (full `messlauf`, many Voyage calls).
- The same test fails twice for reasons you do not understand, or arXiv /
  Voyage behave differently from the docs.
- The change touches more than ~5 files outside the module of the task.

Hand-back note format: goal, what you changed (commits), what you observed
(test output, timings, logs), the open question, and your best next guess.
