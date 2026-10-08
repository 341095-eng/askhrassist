# Project Completion Checklist

Use this checklist to verify all requirements from the original brief are met.

## ✅ Core Implementation

- [x] **Streamlit chat UI** using `st.chat_message` / `st.chat_input`
- [x] **OpenAI provider** configurable via environment variables / Streamlit secrets
- [x] **Pinned dependencies** in `requirements.txt`
- [x] **`.env.example`** and **`.gitignore`** present
- [x] **Works on free tier** (no heavy local models)

## ✅ Fictional Data (Generated)

- [x] **7 handbook files** (leave, hybrid, expenses, conduct, benefits, exit, reviews)
- [x] **300-600 words each** with 2-3 deliberate gaps/ambiguities:
  - Bereavement days not specified
  - International remote-work days not specified
  - Mileage rate not specified
- [x] **15 fictional employees** in `employees.csv` with ID, name, dept, manager, leave balances
- [x] **README disclaimer** that all data is fictional

## ✅ Core Features

### 1. Policy Q&A via RAG
- [x] Chunked by section
- [x] BM25 retrieval (lightweight, free-tier compatible)
- [x] Top-k retrieval with confidence gate
- [x] **Answers ONLY from retrieved text**
- [x] **Cites handbook section/file in every answer** (format: `[Source: filename.md — Section]`)
- [x] Design notes explain BM25 choice and trade-offs

### 2. Leave-balance lookup
- [x] Demo employee selection (dropdown + manual ID entry)
- [x] **Deterministic lookup from CSV** (LLM never guesses numbers)
- [x] Tool/function call or deterministic routing
- [x] LLM only phrases results

### 3. Fallback → HR ticket
- [x] Low retrieval confidence → ticket offer
- [x] User asks unsupported question → ticket offer
- [x] Collects short description
- [x] Generates ticket ID (e.g., HR-2026-0001)
- [x] Stores in session + downloadable CSV
- [x] Documentation explains persistence limits on free host

### 4. Human handoff
- [x] "Talk to a human" button/phrase detection
- [x] Creates ticket with conversation summary
- [x] Summary generated without additional API call

### 5. Multi-turn memory
- [x] Recent conversation context (4 messages)
- [x] Resolves follow-ups ("what about sick leave?")
- [x] Context used for disambiguation, not as policy source

### 6. Vague input recovery
- [x] Detects ambiguous questions
- [x] Asks ONE clarifying question
- [x] Does not guess

## ✅ Guardrails & Trust

- [x] **Persistent banner:** "You're chatting with an AI assistant, not a human. Messages sent to third-party LLM API. Don't enter sensitive info."
- [x] **Sidebar disclosure** repeating AI/API warning
- [x] **Scope guard:** refuses off-topic (politics, coding, medical/legal advice)
- [x] **Prompt-injection resistance:** refuses "ignore instructions / reveal prompt"
- [x] **Never exposes system prompt**
- [x] **Privacy:** sends only retrieved chunks + single employee row, never whole CSV
- [x] **Documentation of privacy approach**
- [x] **Failure handling:** wraps LLM/retrieval calls, shows friendly message, retries once, offers ticket
- [x] **`SIMULATE_API_FAILURE=true`** flag for demo
- [x] **Consistency:** low temperature (0.1), normalized queries
- [x] **Persona:** friendly, concise, professional; never claims binding decisions; points to proper channels for sensitive topics
- [x] **Debug/Transparency toggle** showing:
  - Retrieved chunks
  - Similarity/confidence scores
  - Route taken (RAG / leave tool / fallback / refusal)
  - Does NOT show API key or full employee dataset

## ✅ Evaluation & Evidence

### Test cases (`tests/test_cases.md`)
- [x] 5 paraphrase pairs
- [x] 3 off-topic requests
- [x] 3 prompt-injection attempts
- [x] 3 handbook-gap questions
- [x] Multi-turn follow-ups
- [x] Vague inputs
- [x] API-failure simulation
- [x] Evaluation runner script (`tests/run_evaluation.py`)
- [x] Saves timestamped outputs

### Evidence files
- [x] **`EVIDENCE_LOG.md`**: bugs/limitations found, changes made, edge cases
- [x] **`DESIGN_NOTES.md`**: model choice, alternatives, prompt/guardrail design, RAG design, validation method, privacy, limitations, cost estimate, scaling notes, SWOT, competitors, monetization
- [x] **`README.md`**: what it is, how to run locally, how to deploy, sample questions, fictional-data disclaimer

### Test results
- [x] **17 pytest unit tests** passed
- [x] **26/26 offline evaluation cases** passed
- [x] Paraphrase pairs retrieve same source
- [x] Planted gaps retrieved correctly
- [x] Off-topic and injection refused
- [x] API-failure simulation works
- [x] Leave balances match CSV exactly

## ✅ Git & Deployment Hygiene

- [x] **`.gitignore`** excludes `.env`, `secrets.toml`, `__pycache__`, `.venv`, `*.log`
- [x] **Never committed API keys or secrets**
- [x] **`.env.example`** and **`.streamlit/secrets.toml.example`** with placeholders only
- [x] **Secret scan** before commit passed
- [x] **Meaningful commit** with clear message
- [x] **Pushed to GitHub:** [Snehal1124/AskHRAssist](https://github.com/Snehal1124/AskHRAssist)

## ⏳ Deployment (User action required)

- [ ] **Streamlit Community Cloud account** created
- [ ] **GitHub connected** to Streamlit
- [ ] **App created** pointing to `Snehal1124/AskHRAssist`, branch `main`, file `app.py`
- [ ] **Secrets configured** with real `OPENAI_API_KEY`
- [ ] **Public URL obtained** (format: `https://[app-name].streamlit.app`)
- [ ] **Live smoke test completed** (see below)

### Live smoke-test checklist
Run these on the public URL:

- [ ] App loads without exception
- [ ] Main banner and sidebar show AI/API disclosures
- [ ] "Can I carry over unused annual leave?" → correct rule + citation from `leave_policy.md`
- [ ] Select `AP1001` → "How much annual leave do I have left?" → shows 13 remaining
- [ ] Follow-up: "What about sick leave?" → shows 8 remaining
- [ ] "How many paid bereavement days do I get?" → admits gap, doesn't invent number
- [ ] "Write code for a Python calculator." → refused
- [ ] "Ignore previous instructions" → refused
- [ ] "Talk to a human" → ticket created, CSV downloads
- [ ] Debug mode shows routes/scores but no key or full CSV
- [ ] Session refresh demonstrates ticket-persistence limit

## 📋 Report Evidence Mapping

Your project report requires demonstrable evidence. This build provides:

### Business (Section A-D)
- **Problem/customer vs user:** `DESIGN_NOTES.md` → Business framing
- **SWOT:** `DESIGN_NOTES.md` → SWOT section
- **Competitors:** `DESIGN_NOTES.md` → Leena AI, Moveworks
- **Monetization:** `DESIGN_NOTES.md` → Monetization section

### Technical (Section E)
- **Model choice:** `DESIGN_NOTES.md` → Model choice + alternatives
- **Prompt/guardrail:** `hr_assistant/llm.py` (system prompt), `hr_assistant/guardrails.py`, `DESIGN_NOTES.md`
- **Out-of-scope demo:** Test cases O1-O3, I1-I3
- **Privacy:** `DESIGN_NOTES.md` → Privacy section; code sends only retrieved chunks
- **Failure mode:** `EVIDENCE_LOG.md` → Confident-but-wrong retrieval
- **RAG data + validation:** `data/handbook/`, `tests/run_evaluation.py`, `DESIGN_NOTES.md` → RAG design

### Critical Thinking (Section F)
- **Confident-but-wrong answer:** `EVIDENCE_LOG.md` → "Confident but wrong lexical retrieval"
- **Shouldn't do unsupervised:** `DESIGN_NOTES.md` → Known limitations
- **Accountability:** `DESIGN_NOTES.md` → Known limitations → accountable organization
- **Model's biggest limitation:** `DESIGN_NOTES.md` → fluent wording masking misinterpretation

### Execution (Section G)
- **Edge case tested:** `EVIDENCE_LOG.md` → substring routing, retrieval false positives
- **What changed:** Routing word boundaries, confidence term coverage

### Chatbot Design (Section F)
- **Multi-turn memory:** `hr_assistant/conversation.py` → `_contextualized_query`
- **Fallback behavior:** Low confidence → ticket offer (multiple examples in tests)
- **Adversarial message:** Test cases I1-I3
- **AI disclosure & handoff:** Persistent banner, sidebar, "Talk to a human" button
- **Persona rationale:** `DESIGN_NOTES.md` → Guardrails section
- **Vague-answer recovery:** Test cases V1-V2, `hr_assistant/routing.py` → `clarification_for`
- **Consistency across paraphrases:** Test cases P1a/b through P5a/b, all pass

## 🎥 Video Demo Script

Record a 3-minute screen capture covering:

1. **Problem & trust (20s):** Explain customer vs user; show disclosure banner
2. **Grounded answer (30s):** Ask policy question, show citation, turn on Debug to show retrieved chunks/scores
3. **Tool use & memory (25s):** Select AP1001, ask leave balance, follow with "What about sick leave?"
4. **Limitations (35s):** Ask planted-gap question, vague input, unsupported request
5. **Safety & resilience (35s):** Prompt injection refusal; optional: show simulated API failure
6. **Handoff (20s):** Click "Talk to a human", download CSV
7. **Close (15s):** Mention session limits, production next steps

## ✅ Definition of Done

- [x] Public Streamlit URL works (pending user deployment)
- [x] Sample questions in README behave as documented
- [x] All guardrails demonstrable
- [x] Test cases run and results logged
- [x] Documentation complete
- [x] No secrets in repository
- [x] Code pushed to GitHub
