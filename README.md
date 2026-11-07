# دليل | Daleel — Arabic Academic Advisor

Arabic/Palestinian-Levantine academic Q&A grounded in the supplied An-Najah
National University documents, with a deterministic Computer Engineering planner.
A local hackathon prototype, not an official registration system.

## Run on this computer

Dependencies, the embedding model, knowledge index, and production website have
already been prepared in this workspace.

1. Open `.env` locally and set `GEMINI_API_KEY` to a **new** Gemini API key.
   Do not reuse the key previously pasted into chat. Never commit `.env`.
2. Set `GEMINI_MODEL` to a model available to that key. The initial configurable
   default is `gemini-3.1-flash-lite`; this model responded successfully with the locally configured key.
3. In PowerShell, from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

4. Open **http://127.0.0.1:8000**. API documentation: **http://127.0.0.1:8000/docs**.
5. Press Ctrl+C in that terminal to stop.

No database accounts, Docker, Node server, or Python environment activation are
needed for normal use. The Python server serves the built React website.
The first chat request may take around a minute while the local embedding model warms up. The planner and source library work without Gemini credentials. The chat returns
an explicit setup error until a key is configured. Restart after changing `.env`.
Use only hypothetical course selections, not real student records.

Check the configured Gemini access manually:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_gemini --list-models
.\.venv\Scripts\python.exe -m scripts.check_gemini
```

The second command makes one generation request. Change `GEMINI_MODEL` if the
configured default is unavailable. No credentials are printed by either command.

## Fresh-clone setup

Prerequisites: Python 3.11, Node.js 22.12+ or a compatible newer release, npm,
and internet access for package/model downloads. This machine has Python 3.11
and Node 24. Install Python 3.11 if `py -3.11` is unavailable.

Keep the supplied data files in `data/` or `data/raw/`, with no duplicate copies.
Then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The setup script creates `.venv`, installs `requirements-lock.txt`, creates a blank
`.env` only if absent, builds the local index, runs `npm ci`, and builds the UI.
The first embedding-model download is large and CPU indexing takes several
minutes. Subsequent runs reuse cached embeddings. No Hugging Face token is
required for the public model. Windows symlink warnings are nonfatal.

If running commands manually:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env  # first setup only; do not overwrite a configured .env
.\.venv\Scripts\python.exe -m app.ingestion
Set-Location frontend
npm ci
npm run build
Set-Location ..
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The execution-policy override applies only to that script invocation; no permanent
PowerShell policy change is required. `requirements.txt` describes supported ranges;
`requirements-lock.txt` captures the tested Python 3.11/Windows environment.
`frontend/package-lock.json` captures the tested frontend dependencies.

## Features

- Arabic RTL / English LTR React interface and self-hosted IBM Plex Sans Arabic fonts.
- Formal Arabic or Palestinian/Shami answer style.
- Original-question retrieval plus conservative dialect keyword expansion.
- E5 multilingual semantic retrieval + BM25 + exact course-code matching + RRF.
- Tokenizer-aware article/page chunking and bounded parent-section expansion.
- Structured Gemini claims, backend-owned citations, and a second support check.
- Separate answers, partial answers, clarification, source conflicts, missing
  evidence, out-of-scope requests, and technical errors.
- Expandable original excerpts and original PDF page links.
- Ephemeral follow-up context, without persisting student identities.
- Saved completed-course checklist, explicit AND/OR prerequisites, category-capped credit calculations, and profile-aware chatbot answers.
- Degree/source conflicts and ambiguous course records remain visible.

Multilingual retrieval and dialect examples do not establish complete coverage
of all Levantine variants. Live answer quality still requires evaluation.

## Stack and design

Python 3.11; FastAPI/Pydantic; PyMuPDF; pdfplumber available for table investigation;
Sentence Transformers `intfloat/multilingual-e5-base`; persistent Chroma;
rank-bm25; SQLite; official `google-genai`; React/TypeScript/Vite/Tailwind.

See [architecture](docs/architecture.md) and [data audit](docs/data-audit.md).
The pipeline is explicit Python, with no agent framework, fine-tuning, or
hardcoded academic answers. Local retrieval and planning do not call Gemini.
A supported answer normally makes **two Gemini calls**: generation and claim
support checking. Requests may incur provider charges. Token usage is returned
in the API response; no cost is asserted without current pricing.

## Data, provenance, and important limits

Original supplied data remain unchanged. Evidence includes:

- `dlyl_ltlb_25.pdf`: 135-page student guide, identifying itself as 2026–2027.
- `computer_engineering_courses.csv`: 125 supplied catalog/option entries.
- `prerequisites.csv`: 61 prerequisite entries.
- `degree_requirements.csv`.
- `academic_faq.csv`: attributed summaries, not verified original policy text.
- Official-source rows from `academic_rules.csv`.

Source links are preserved from the supplied registry and CSVs:

- [Official Computer Engineering plan](https://www.najah.edu/ar/academic/undergraduate-programs/program/computer-engineering/study-plan/).
- [Student guide index](https://www.najah.edu/ar/academic/admissions/student-guide-book/).
- [Undergraduate FAQ](https://www.najah.edu/ar/faq/undergraduate/).
- [General FAQ](https://www.najah.edu/ar/faq/general/).

The dataset's source-verification labels are retained as supplied; this project
has not independently reverified every university webpage. Project READMEs,
collection gaps, source registries, and user-selected prototype rules are excluded
from policy retrieval. The hackathon guide is not part of the academic corpus.

**Conflict:** supplied plan totals 162; guide pages 47–48 list 163 and a different
category breakdown. Planner numbers are estimates for the supplied plan and
never confirm graduation. The effective year of that plan is not established.

Course 10221115 has an ambiguous prerequisite. Course 11032102 has a credit
conflict. Both require review rather than asserted eligibility. Courses requiring
individual approvals are not guaranteed by satisfied listed prerequisites.
The 18-credit planner ceiling is a prototype constraint, not a universal official
policy. Selected courses must already be hypothetically passed; no grade engine
or grade conversion is inferred. Missing alternate course codes are not assumed
passed. Elective options are not all counted as mandatory.

Some PDF numerical tables require manual column validation and are excluded
from retrieval rather than flattened into misleading prose. Image-heavy/divider
pages are reported. This is not a claim of complete OCR or table coverage.
Check `data/processed/inspection.json` for the generated audit and
`data/processed/sample_chunks.json` for inspection examples.

No current semester offerings, timetable conflicts, equivalencies, private
registrar integration, or special approvals are available.

## Reindex after changing data

Stop the server, then run:

```powershell
.\.venv\Scripts\python.exe -m app.ingestion
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

Unchanged inputs skip work. Changed content builds a replacement generation and
switches the active manifest only after success. Cached embeddings are reused.
The currently tested generation has 427 chunks; that number changes with inputs.

A CLI process interruption can leave `data/indexes/ingest.lock`. Remove that
single lock file only after confirming no ingestion is running, then retry.
Do not delete the active database to fix a lock.

An optional `ADMIN_TOKEN` enables authenticated `POST /api/documents/ingest` for
reindexing files already placed in the local data folder. Supply
`Authorization: Bearer <token>`. It is disabled by default. No public file upload
or administration dashboard is provided.

## API

All endpoints are under `/api`; equivalent unprefixed routes exist for integration.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Index, semantic search, and Gemini configuration status |
| POST | `/chat` | Question, optional conversation_id, style=formal/levantine |
| GET | `/documents` | Source inventory and provenance |
| GET | `/documents/{id}` | One document's metadata |
| GET | `/documents/{id}/file` | Whitelisted original PDF |
| GET | `/sources/{source_id}` | Original chunk citation |
| GET | `/courses` | Supplied course records |
| POST | `/planner` | Hypothetical completed/proposed code lists |
| GET | `/inspection` | Extraction issues and conflicts |
| POST | `/documents/ingest` | Optional token-protected rebuild |

Chat returns `answer`, `status`, `sources`, `conversation_id`, optional
`clarification_question`, scope limitations, and token usage. CSV citations use
record IDs, never invented page numbers. Provider failures return HTTP errors,
not fabricated academic refusals. Do not expose this prototype publicly without
adding deployment authentication, resource limits, and an appropriate privacy policy.

## Checks and evaluation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m evaluation.evaluate
.\.venv\Scripts\python.exe -m evaluation.evaluate --split held_out
.\.venv\Scripts\python.exe -m evaluation.evaluate --split fresh
Set-Location frontend
npm run build
# Start the Python server on port 8000 in another terminal before browser tests:
npm run test:e2e
```

Browser checks use installed Microsoft Edge on Windows. They exercise real course
and document endpoints; the missing-key chat UI is mocked to prevent accidental
paid calls. Provider contract tests also use mocks. Neither establishes live LLM
accuracy. See [evaluation report](evaluation/REPORT.md).

After configuring a fresh key, explicitly run metered answer evaluation:

```powershell
.\.venv\Scripts\python.exe -m evaluation.evaluate --live
```

Then manually review the saved answers against the annotated facts and sources,
including refusals, engineering exceptions, conflicts, and dialect questions.
Two live API smoke cases have since passed (a cited Palestinian prerequisite answer and an unavailable exam-date refusal). Full live reference evaluation and broader manual answer review are still required; see evaluation/REPORT.md.

## Frontend development

Run the API on port 8000 and, in a separate terminal:

```powershell
Set-Location frontend
npm run dev
```

Open the URL Vite prints (normally http://127.0.0.1:5173). Its `/api` proxy talks
to FastAPI. For the single-process version rebuild with `npm run build` and
restart the Python server if asset mounts have changed.

## Competition handoff

See `docs/presentation/NOTES.md` for presentation preparation notes. The presentation itself is deferred and no PPTX is included.
Business numbers are explicitly illustrative assumptions, not verified market
research or current vendor prices. Add the team names and real problem/market
validation before submission. Capture a live sourced-answer demo after adding
a replacement key. The optional recording should be 2–3 minutes.

## AI tools and attribution

Developed with OpenAI Codex assistance for architecture, implementation,
Arabic copy, tests, and documentation. Runtime generation uses Gemini; retrieval
uses the pretrained multilingual E5 model, not fine-tuning. University data and
source links were supplied by the team. No academic knowledge is authored by
Codex as a substitute for supplied evidence.

IBM Plex Sans Arabic fonts are distributed under the included SIL Open Font
License in `frontend/public/fonts/OFL.txt`. Icons use lucide-react. Official
implementation references include [E5 model card](https://huggingface.co/intfloat/multilingual-e5-base),
[Sentence Transformers](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html),
[Chroma](https://docs.trychroma.com/reference/python), and
[Google Gen AI SDK](https://googleapis.github.io/python-genai/).

## Login and saved study profile

The website opens with Arabic/English login and registration. Create a local username
(3–32 ASCII letters, numbers, or underscores) and a password of at least 8 characters.
No email, university ID, or external identity service is needed. After login, select your current study year and completed courses on the checklist page, then save and continue to Ask Daleel. Answers use the saved profile and prerequisite calculations.
Selections and year are saved per account in ignored data/indexes/accounts.sqlite.
Passwords use individually salted PBKDF2 hashes; browser sessions use opaque
HttpOnly SameSite cookies. Logout invalidates the server-side session. This is
local demo authentication, not a university login or public production identity system.

Study year is the current progress year, not a curriculum/coterm eligibility rule.
No verified semester/year assignment exists for all supplied course rows, so
no course is hidden or marked passed automatically based on year. Prerequisites
continue to use the supplied AND/OR expressions. Inconsistent completed-course
selections receive a warning; only previously completed prerequisites unlock
course eligibility calculations. Use hypothetical course histories for the hackathon.

## Personal credit questions

Questions about remaining credits now use the authenticated account's saved
completed-course list and deterministic category-capped calculations directly.
They do not ask Gemini to calculate totals or invent references. The answer cites
the saved-profile calculation, supplied plan, and conflicting guide evidence
when present. Arabic and English are supported. A 162/163 source conflict remains
explicit and the result is not presented as graduation confirmation.

For generated answers, the model receives short source aliases constrained by
the response schema. The backend maps only known aliases back to original
source records and retains claim-support verification. Unknown citations remain
rejected.
