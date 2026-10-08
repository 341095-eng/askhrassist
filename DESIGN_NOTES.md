# Design Notes

## Business framing

### Problem, customer, and user

Employees lose time searching long handbooks or waiting for repetitive HR answers.
The paying customer is AsterPeak Solutions’ HR department/company; employees are the
end users. The product aims to deflect routine questions while making uncertainty and
handoff explicit. It is not intended to replace HR judgment or case management.

### SWOT

**Strengths**

- Available outside desk hours and responds quickly to repetitive questions.
- Grounds policy answers in a controlled handbook and shows citations.
- Retrieves leave figures exactly from a structured source instead of asking a model.
- Gives HR a repeatable intake format and makes routing visible during evaluation.

**Weaknesses**

- BM25 is lexical and can miss unusual synonyms or indirect questions.
- An LLM can still misread evidence or sound more certain than warranted.
- Demo identity selection is not authentication.
- Tickets and chat are session-only; the free deployment has no durable workflow.
- English-only content and a small fictional handbook limit coverage.

**Opportunities**

- Add multilingual answers while retaining source-language citations.
- Integrate SSO, an HRIS, ticketing, document versioning, and analytics.
- Extend to onboarding, payroll FAQs, manager support, and regional handbooks.
- Use unanswered-query reports to improve policy documentation.

**Threats**

- API price changes, outages, model retirement, or changed model behavior.
- Privacy, labor, AI, records-retention, and cross-border data regulations.
- Prompt injection or poisoned source documents.
- Employees relying on general guidance for a consequential individual case.
- Competitors bundling assistants into an existing HR or enterprise-search platform.

### Competitors and differentiation

**Leena AI** provides enterprise employee-service and HR automation capabilities.
**Moveworks** provides broad enterprise copilots and employee support across systems.
Those products are substantially more mature than this student project. AsterPeak’s
demo differentiation is narrowness and inspectability: local BM25 retrieval, visible
scores/routes, deterministic leave output, explicit planted gaps, and a small codebase
that can be explained end to end. This is educational differentiation, not a claim of
commercial feature superiority.

### Monetization

A plausible business model is a monthly company subscription tiered by active employees,
handbook regions, and integrations, with an implementation fee for SSO/HRIS setup.
Premium tiers could add multilingual support, analytics, durable case management, and
service-level commitments. Production pricing must account for LLM usage, support,
security reviews, hosting, and compliance—not only token cost.

## Model choice

The default is configurable `gpt-4o-mini` through the OpenAI API. It was selected for a
low-cost, low-latency classroom demo with adequate instruction following and concise
generation. Temperature is `0.1` for more consistent phrasing. The app does not depend
on model-specific tool calling, which makes replacement simpler.

Alternatives considered:

- A larger OpenAI model may improve subtle policy interpretation but costs more and does
  not remove hallucination risk.
- Anthropic or another hosted provider could be added behind `hr_assistant/llm.py`, but
  the available key is OpenAI and multiple SDKs would add unnecessary deployment risk.
- A local model would avoid sending messages to a hosted LLM but is too heavy for a
  simple free-tier Streamlit deployment.
- Fully extractive responses would be cheaper and more deterministic but less natural
  for follow-ups and synthesis across a few sections.

Model IDs, availability, and prices change. The configured model should be verified in
the account before deployment; changing `OPENAI_MODEL` does not require UI changes.

## Prompt and guardrail design

The system prompt defines the role, source boundary, citation format, non-binding
persona, privacy behavior, and instruction hierarchy. Retrieved handbook text and user
text are explicitly treated as untrusted data. The prompt forbids filling evidence gaps
and requires uncertainty.

Prompting is only one layer:

1. Deterministic regex/phrase checks reject common prompt-injection and off-topic
   requests before an API call.
2. Explicit handoff and leave intents route before RAG.
3. Leave values are formatted in Python.
4. BM25 confidence gates unsupported questions.
5. Generated answers must contain a citation matching a retrieved section.
6. Invalid output or an API exception is retried once, then converted to a ticket offer.

Pattern checks are intentionally modest. They reduce obvious attacks but cannot prove
that every adversarial phrasing is safe. Production should add continuously evaluated
classifiers, source-ingestion controls, abuse monitoring, and security review.

## RAG design and trade-offs

Seven fictional Markdown files are chunked on `##` headings. Each chunk retains its file
and section name. Query text is lowercased, stripped of punctuation, filtered for common
stop words, and expanded for a few domain aliases such as PTO/vacation and WFH. A local
BM25 index returns the top three chunks. Confidence requires a configurable top score and
term overlap.

Why BM25:

- No embedding API cost or vector database.
- Fast startup on a small corpus.
- Deterministic, inspectable scores suitable for a student demonstration.
- Exact policy terms, dates, limits, and labels are often lexical.

Trade-offs:

- Semantic paraphrases can score poorly unless aliases cover them.
- BM25 scores are corpus-relative, not probabilities.
- Common HR words may produce a high score for the wrong section.
- Section boundaries may omit useful neighboring context.

The confidence score is therefore displayed as a retrieval score, never as “percent
correct.” A threshold prevents some unsupported answers but cannot guarantee relevance.

### Accuracy validation

`tests/test_cases.md` defines observable expectations. The suite includes five
paraphrase pairs, planted gaps, unsupported topics, adversarial prompts, multi-turn
follow-ups, vague requests, and failure simulation. Unit tests verify routing, source
selection, CSV arithmetic, ticket export, and retry behavior. The evaluation runner
saves route, source, score, response, and pass/fail evidence.

Validation focuses on:

- Retrieval: expected file/section appears at the top.
- Grounding: live answers contain a citation from the retrieved set.
- Consistency: paraphrases return the same rule and source.
- Safety: no unsupported number, hidden prompt, or whole employee dataset is exposed.
- Recovery: ambiguous input asks one question; low confidence and failures offer a
  ticket.

The test corpus is small and authored with the application, so a high test pass rate
does not establish real-world accuracy. A production evaluation needs independent HR
reviewers, historical anonymized questions, region-specific policies, and regression
sets that were not written by the developer.

## Privacy and data minimization

The UI warns that messages go to a third-party API and asks users not to enter sensitive
information. For policy Q&A, the API receives only:

- The current question.
- Up to four recent messages, truncated.
- The top retrieved handbook sections.
- The system safety instructions.

The complete handbook and CSV are not sent. Leave lookup is entirely local and sends no
employee row to the model. The debug trace shows only the selected employee ID and never
the API key or whole record. Ticket summaries are generated locally.

These controls reduce exposure but do not make the demo suitable for personal or case
data. Production requires a data-processing agreement, retention controls, encryption,
access controls, audit logs, regional review, deletion procedures, and a clear policy on
whether provider training is disabled.

## Known limitations and accountability

The largest model limitation is that fluent wording can make an evidence
misinterpretation sound authoritative. Citations improve auditability but do not prove
that the cited text entails the answer. The accountable organization remains the
employer/HR department; responsibility cannot be delegated to the model or vendor.

The assistant should never act unsupervised to:

- Approve/deny leave, expenses, benefits, accommodations, or remote work.
- Diagnose health issues or decide insurance coverage.
- Investigate harassment, assess credibility, recommend discipline, or terminate.
- Calculate final settlement, interpret individual legal rights, or change HR records.
- Make hiring, rating, pay, promotion, or redundancy decisions.

The most useful “confident but wrong” demonstration is a retrieval false positive:
a lexical matcher can rank a section because it shares common terms while missing the
question’s meaning. The evaluation and `EVIDENCE_LOG.md` record the concrete case found
during testing and the resulting threshold/alias change. Even after correction, the
underlying risk remains, so debug evidence and handoff are part of the product design.

Other limitations include:

- Demo employee selection is not secure authentication.
- Session tickets disappear on reset and do not notify HR.
- Ticket IDs are unique only within a session, not globally.
- Simple phrase guardrails have false positives and false negatives.
- Recent-message memory is short and can carry the wrong topic into a follow-up.
- English aliases and fictional India-oriented amounts do not cover every locale.
- Streamlit Community Cloud can cold-start and has no availability commitment here.

## Cost estimate

BM25 retrieval and leave lookup have no per-query API charge. Only grounded policy
generation uses OpenAI. A short turn typically sends a few retrieved sections plus brief
history. As a planning estimate, a 10-turn conversation using a low-cost mini model is
expected to be well below one US cent, approximately **USD 0.005**, but this is not a
quote. The real calculation is:

`input tokens × current input rate + output tokens × current output rate`

Cached-token rates, retries, longer histories, model changes, and taxes can alter cost.
Current OpenAI pricing should be checked immediately before the report or deployment.
The under-USD-5 development budget is protected by local retrieval, concise outputs,
manual live evaluation, and no embedding calls.

## Scaling beyond 100 users per day

At 100+ daily users, replace or extend the demo as follows:

- Add SSO/OIDC and enforce employee authorization server-side.
- Store tickets and conversations in a durable database with retention controls.
- Integrate an HR case-management system and globally unique ticket IDs.
- Move orchestration to a backend API so secrets and policy enforcement are centralized.
- Add rate limiting, queues, retries with backoff, caching, health checks, and metrics.
- Version and approve source documents; rebuild retrieval indexes on controlled publish.
- Consider hybrid lexical/embedding retrieval and reranking, measured against a larger
  independent test set.
- Separate countries/business units and enforce document-level access.
- Add human quality review, red-team tests, incident response, and model-change gates.
- Track token cost, latency, unanswered topics, refusal quality, and handoff completion.

The free Streamlit deployment remains suitable for demonstration, not these production
requirements.
