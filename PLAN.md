# HR Helpdesk Assistant — Implementation Plan

## 1. Product Summary

**Product:** HR Helpdesk Assistant

**Fictional company:** AsterPeak Solutions, a mid-size technology services company

**Paying customer:** The company’s HR department

**End users:** Employees

The application will provide a turn-by-turn Streamlit chat interface that:

1. Answers handbook questions using retrieval-augmented generation (RAG) with citations.
2. Looks up the selected employee’s leave balance deterministically from fictional CSV data.
3. Creates an HR ticket when confidence is low, the topic is unsupported, an API call fails, or the employee requests a human.
4. Makes limitations, routing, retrieved evidence, and failure behavior visible for assessment and demonstration.

All handbook, employee, and ticket data used in the project will be fictional.

## 2. Confirmed Decisions

- **LLM provider:** OpenAI API.
- **Default model:** `gpt-4o-mini`, chosen as a low-cost, fast, widely supported default. The exact model remains configurable.
- **Budget target:** Under USD 5 for development and demonstration.
- **UI/deployment:** Python and Streamlit Community Cloud.
- **Retrieval:** Local BM25-style lexical retrieval; no paid embedding calls.
- **Demo login:** Employee dropdown plus optional manual employee ID.
- **Ticket download:** CSV.
- **Git workflow:** One final implementation commit and push after verification and a
  staged secret scan, per the updated user instruction.
- **Deployment support:** Click-by-click Streamlit Community Cloud and GitHub instructions.

## 3. Architecture

```text
Employee
   |
   v
Streamlit chat UI + demo identity selector
   |
   v
Input safety and route selection
   |--------------------|----------------------|---------------------|
   v                    v                      v                     v
Leave tool        Policy RAG route       Scope/refusal       Human handoff
(CSV lookup)      (BM25 retrieval)        route               route
   |                    |                      |                     |
   |                    v                      |                     |
   |             confidence gate              |                     |
   |              |           |               |                     |
   |            high          low              |                     |
   |              v           v               v                     v
   |          OpenAI answer   ticket offer  safe response      ticket creation
   |          from evidence
   |              |
   |              v
   |       citation validation
   |______________|_______________________________________________
                                  |
                                  v
                    Chat response + debug trace
```

### Request-routing order

1. Detect direct prompt injection and prohibited/off-topic requests.
2. Detect human-handoff requests.
3. Detect ticket-workflow replies already in progress.
4. Detect leave-balance intent and use only the selected employee’s CSV row.
5. Retrieve handbook sections for likely policy questions.
6. Ask one clarifying question for genuinely vague HR input.
7. Fall back to an HR ticket when evidence is weak or the subject is absent.

Routing will be primarily deterministic so safety and leave numbers do not depend on model judgment. The LLM will phrase grounded answers and use limited recent context for follow-ups.

## 4. Technology Stack

- Python 3.11-compatible application.
- Streamlit for UI, session state, chat components, sidebar, downloads, and deployment.
- OpenAI Python SDK for answer generation and concise conversation summaries.
- `rank-bm25` for lightweight local retrieval.
- pandas for reading and validating fictional employee data.
- python-dotenv for local configuration.
- pytest for deterministic unit tests.
- Standard-library CSV/JSON utilities for ticket logs and evaluation output.

Dependencies will be pinned in `requirements.txt`. Heavy local models, vector databases, external databases, and paid embedding calls are intentionally excluded.

## 5. RAG Design

The handbook will contain seven Markdown documents:

1. Leave policy.
2. Hybrid/work-from-home policy.
3. Expense reimbursement.
4. Code of conduct.
5. Benefits.
6. Notice period and exit.
7. Performance reviews.

Each document will be approximately 300–600 words. Markdown headings will define chunks, with file name, section title, and chunk ID retained as metadata. Queries will be lowercased and lightly normalized. BM25 will retrieve the top `k` sections.

A calibrated confidence gate will combine:

- Top BM25 score.
- Gap between the first and second result.
- Presence of meaningful query terms in the retrieved section.

The LLM receives only the recent conversation context and retrieved chunks. Its prompt requires an answer based only on that evidence, explicit uncertainty, and citations in a machine-checkable format. Output will be validated for citation presence. Unsupported or malformed output triggers one retry, then a ticket offer.

BM25 is preferred because it is deterministic, fast, free, transparent, and easy to deploy on Streamlit’s free tier. It is weaker than semantic embeddings for synonyms and indirect wording; paraphrase tests and explicit confidence calibration will document that trade-off.

## 6. Conversation and State Design

Streamlit session state will hold:

- Selected demo employee ID.
- Recent user/assistant messages, capped to a small context window.
- Current ticket-collection state.
- Session ticket list and incrementing display counter.
- Last retrieval results, confidence, route, and error details for debug mode.

Ticket IDs will use a timestamp/session-safe form such as `HR-2026-0001`. Tickets persist only for the active Streamlit session and can be downloaded as CSV. This is not durable production persistence and will be stated in the UI and documentation.

The ticket flow will:

1. Offer a ticket after a fallback.
2. Accept confirmation.
3. Ask for one short description if needed.
4. Create the ticket and provide its ID.

“Talk to a human” will create a ticket from a concise conversation summary after confirmation. Sensitive topics will point to the fictional confidential HR channel and avoid making policy or legal determinations.

## 7. Guardrails and Failure Handling

- Persistent AI/third-party API/privacy warning in the main UI and sidebar.
- Deterministic topic and injection checks before any model call.
- System prompt instructing the model not to reveal hidden instructions or follow instructions found in retrieved content.
- Minimum-data prompts: retrieved sections and, only when necessary, one employee row.
- Leave calculations performed in Python; the model never generates or changes balances.
- Low temperature and normalized retrieval queries for consistency.
- API timeout and exception handling around every model call.
- One bounded retry for timeout, API error, malformed output, or missing citations.
- `SIMULATE_API_FAILURE=true` path for a repeatable failure demo.
- Friendly failure response followed by a ticket offer.
- Debug/Transparency view showing route, normalized query, retrieved sections, raw scores, confidence decision, retry/failure state, and citations.
- No hidden system prompt, API key, or full employee dataset shown in debug output.

## 8. Planned File Structure

```text
AskHRAssist/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example
├── data/
│   ├── employees.csv
│   └── handbook/
│       ├── leave_policy.md
│       ├── hybrid_work.md
│       ├── expense_reimbursement.md
│       ├── code_of_conduct.md
│       ├── benefits.md
│       ├── notice_and_exit.md
│       └── performance_reviews.md
├── hr_assistant/
│   ├── __init__.py
│   ├── config.py
│   ├── llm.py
│   ├── retrieval.py
│   ├── routing.py
│   ├── leave_tool.py
│   ├── tickets.py
│   ├── guardrails.py
│   └── conversation.py
├── tests/
│   ├── test_cases.md
│   ├── run_evaluation.py
│   ├── test_retrieval.py
│   ├── test_routing.py
│   └── results/
│       └── .gitkeep
├── README.md
├── DESIGN_NOTES.md
├── EVIDENCE_LOG.md
└── PLAN.md
```

## 9. Milestones

### Milestone 0 — Repository and safety baseline

- Confirm why the current folder is not detected as a Git clone.
- Restore or initialize Git only after verifying the intended GitHub remote.
- Add `.gitignore`, placeholder secret files, pinned dependencies, configuration loader, and app shell.
- Add the disclosure banner and sidebar.
- Scan staged files for secret-like values before committing.

**Test:** Run the app locally, confirm both disclosures appear, confirm missing API key produces setup guidance, and verify ignored secret files are not staged.

### Milestone 1 — Fictional source data and deterministic tools

- Write seven handbook files with deliberate, documented gaps.
- Generate approximately 15 internally consistent employee rows.
- Add employee selection and validated leave lookup.
- Add ticket state, unique ticket IDs, session log, and CSV download.

**Test:** Select multiple employees, verify entitled/used/remaining arithmetic, test unknown IDs, create tickets, and download/open the CSV.

### Milestone 2 — Retrieval and grounded policy answers

- Parse Markdown by heading and build the BM25 index.
- Add query normalization, top-k retrieval, confidence scoring, and citations.
- Add the single provider module for OpenAI with configurable model/timeout.
- Add grounded answer prompting and citation validation.

**Test:** Run known-answer, paraphrase, unsupported, and planted-gap queries; inspect retrieved sections and citations in debug mode.

### Milestone 3 — Conversation routing and guardrails

- Add deterministic route selection.
- Add multi-turn follow-up context and one-question vague-input recovery.
- Add scope refusal, injection refusal, sensitive-topic guidance, and human handoff.
- Ensure the minimum required data is sent to the API.

**Test:** Exercise off-topic, adversarial, vague, leave, follow-up, sensitive, and handoff prompts; confirm debug route labels.

### Milestone 4 — Reliability and evaluation evidence

- Add retry-once behavior and API-failure simulation.
- Build deterministic unit tests and the evaluation runner.
- Complete required prompt matrix and save timestamped results.
- Record discovered failures and resulting changes in `EVIDENCE_LOG.md`.
- Tune retrieval thresholds from test evidence, not only intuition.

**Test:** Run pytest and the scripted test suite with normal API behavior and simulated failure. Confirm output is saved without secrets or private data.

### Milestone 5 — Documentation and demo readiness

- Complete README, design notes, limitations, cost estimate, scaling notes, SWOT/business framing, competitors, monetization, accountability, and deployment instructions.
- Add sample questions and a short video demo script/checklist.
- Validate dependency installation in a clean environment.

**Test:** Follow README from a clean environment, run every documented sample, and verify claims against saved evaluation evidence.

### Milestone 6 — GitHub and Streamlit deployment

- Perform final staged-secret scan.
- Create one clear implementation commit and push it to
  `git@github.com:Snehal1124/AskHRAssist.git`.
- Guide the user through Streamlit Community Cloud signup, GitHub connection, app creation, and secrets entry.
- Run a live smoke-test checklist on the public URL.

**Test:** Verify startup, disclosure, policy citation, leave lookup, fallback ticket, human handoff, guardrails, debug mode, failure simulation where safe, and ticket download on the deployed app.

## 10. Evaluation Coverage

`tests/test_cases.md` and the runner will cover at minimum:

- Five semantically equivalent paraphrase pairs.
- Three off-topic requests.
- Three prompt-injection attempts.
- Three planted handbook-gap questions.
- Multi-turn policy and leave follow-ups.
- Vague inputs that require one clarifying question.
- Sensitive HR topics.
- Human handoff.
- Unknown employee IDs and malformed input.
- API-failure simulation.
- Citation presence and retrieved-source relevance.
- Repeated/paraphrased prompts for consistency.

Evaluation output will capture prompt, expected route/behavior, actual route, response, sources, scores, and pass/fail notes. LLM wording cannot be perfectly deterministic, so automated checks will focus on observable contracts while qualitative answer quality is reviewed manually.

## 11. Key Risks and Mitigations

- **Current folder is empty/not a Git repository:** verify location and remote before any commit or push; do not overwrite another clone.
- **API key exposure:** ignore local secret files, use placeholders, inspect staged diffs, and run a secret-pattern scan before every commit.
- **BM25 misses paraphrases:** normalize terms, use section-level chunks, calibrate with paraphrase tests, and fall back safely when evidence is weak.
- **LLM invents facts or citations:** tightly limit context, require citations, validate output, retry once, then decline and offer a ticket.
- **Streamlit session resets:** disclose that tickets and chat are session-only and provide immediate CSV download.
- **Shared-host concurrency:** avoid mutable global user data; keep user-specific state in Streamlit session state.
- **Model/API changes:** isolate OpenAI usage in one module and configure provider/model through environment variables or Streamlit secrets.
- **Free-host cold starts or package issues:** keep dependencies small and pinned; test installation in a clean environment.
- **Over-broad safety matching:** preserve a debug route and adversarial/false-positive tests, then document threshold changes.
- **“Login” mistaken for real authentication:** label it clearly as demo identity selection; never claim it secures personal data.

## 12. Definition-of-Done Checks

- Public Streamlit URL opens and completes the live smoke test.
- README sample prompts behave as documented.
- Policy answers are grounded and cite source sections.
- Leave figures come only from the selected fictional CSV row.
- Fallback, ticket, handoff, guardrail, vague-input, and API-failure paths are demonstrable.
- Required test cases have saved results.
- Evidence log and design notes support the report’s business, technical, critical-thinking, execution, and conversation-design sections.
- Repository contains no API keys or local secret files.
- The final implementation commit is pushed to the intended GitHub repository.
