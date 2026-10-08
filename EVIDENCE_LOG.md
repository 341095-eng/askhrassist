# Evidence Log

This log records observed failures and limitations rather than presenting the demo as
perfect. Dates use UTC.

## 2026-10-08 — Repository state did not match expectation

**What happened:** The working folder was expected to be a clone of
`git@github.com:Snehal1124/AskHRAssist.git`, but it contained no files and `git status`
reported that it was not a Git repository.

**Why:** The clone metadata was not present at the workspace path. The cause cannot be
established from the folder contents.

**Change:** Implementation proceeded without pretending Git history existed. Repository
initialization and exact remote verification were deferred to final verification before
any commit/push.

**Remaining limitation:** If a separate clone exists elsewhere, initializing this folder
could create divergent history. The remote must be fetched and inspected first.

## 2026-10-08 — Leave numbers must not depend on generation

**Failure risk:** A language model can confidently change, combine, or invent a leave
number, especially in a follow-up such as “what about sick leave?”

**Why:** Generation optimizes likely text, not arithmetic integrity.

**Change:** CSV loading validates `entitled - used = remaining`; Python selects and
formats balances. The leave route does not call the LLM and the debug trace says so.

**Evidence:** `tests/test_retrieval.py` checks the AP1001 annual balance and output.

## 2026-10-08 — Handbook intentionally cannot answer every question

**Observed limitation:** Real policy sources contain gaps. This handbook deliberately
omits a universal bereavement duration, international-remote-work day limit, and mileage
rate.

**Change:** The source explicitly acknowledges each gap and directs employees to the
appropriate human channel. The prompt forbids filling a gap, and all three questions are
evaluation cases G1–G3.

**Why retained:** Inventing a precise number would be more harmful than a transparent
handoff. This is a product behavior to demonstrate, not missing implementation work.

## 2026-10-08 — Session storage is not durable ticketing

**Observed limitation:** Streamlit session state can reset during refreshes, inactivity,
deployment restarts, or host lifecycle events.

**Change:** The app labels tickets “demo,” warns that they are session-only, and offers a
CSV download. Ticket summaries are local and deterministic.

**Production fix:** Use an authenticated backend and durable case-management/database
integration with access control, audit, retention, and notifications.

## 2026-10-08 — Confident but wrong lexical retrieval

**What happened:** The initial retriever marked “Give me a recipe for sourdough bread”
as confident with a BM25 score of 4.10. It had matched a handbook section solely on the
generic word “give.” A cafeteria question could similarly match “office.”

**Why:** The first confidence rule required only one overlapping term plus a raw BM25
threshold. BM25 scores are corpus-relative and a rare but meaningless shared word can
score highly. The score looked precise but did not mean the answer was relevant.

**Change:** Added conversational filler words to retrieval stop words and required both
minimum term count and at least 34% query-term coverage. The unsupported recipe and
cafeteria tests now fall back before any LLM call.

**What this demonstrates:** This is the project’s concrete confident-but-wrong example.
The fix addresses these cases but does not prove that every future high-scoring result
is relevant. Human-reviewed evaluation and fallback remain necessary.

## 2026-10-08 — Substring intent routing caused false leave lookups

**What happened:** “unused annual leave” was routed to the personal leave-balance tool
because the substring `used` appears inside `unused`. “How many days may I work from
another country?” also looked like a balance request because it contained “how many
days.”

**Why:** Intent phrases were matched as unrestricted substrings and balance wording did
not initially require a leave term.

**Change:** Balance phrases now use word boundaries and must occur with an explicit leave
term (unless continuing an existing leave-tool conversation). Evaluation cases P1a,
P1b, and G2 now take the correct RAG route.

## 2026-10-08 — Dependency isolation and compatibility

**What happened:** Installing into the existing user site failed because its
`watchdog` directory was not writable. The OpenAI SDK version also permits a newer
`httpx` release with a known-incompatible constructor surface.

**Change:** Verification uses the ignored project `.venv`, as documented. `httpx` is
pinned to `0.27.2` alongside the OpenAI SDK to keep local and cloud installs repeatable.

## 2026-10-08 — Cloud build hung on Python 3.14

**What happened:** The first Streamlit Community Cloud deployment ran far longer than
expected and was deleted.

**Why:** The cloud defaulted to Python 3.14. `pandas==2.2.3` publishes no Python 3.14
wheel, so the installer fell back to compiling pandas (and its C extensions) from
source. Local testing on Python 3.10 could not reveal this.

**Change:** Pinned `pandas==2.3.3`, which ships 3.14 wheels. Verified with
`pip download --only-binary=:all:` that every dependency resolves to a prebuilt wheel
on Python 3.11, 3.12, and 3.14. The README now tells deployers to pick the Python
version explicitly in the dropdown.

**Lesson:** Pinning versions makes a build repeatable only on the interpreter you
tested; the deployment platform's default interpreter is part of the environment.

## Verification results — 2026-10-08

- `pytest -q`: **17 passed**.
- Offline `tests/run_evaluation.py`: **26/26 passed** for deterministic route/source,
  planted-gap retrieval, paraphrases, refusals, fallback, and simulated failure.
- Streamlit AppTest: title, disclosure banner, chat input, and exception-free initial
  render passed.
- A real OpenAI answer evaluation was not run because no API key was stored in the
  repository or test environment. It remains a pre-deployment manual check.
- Timestamped local output:
  `tests/results/evaluation_20261008T053724Z.json` and `.csv` (ignored by Git).
