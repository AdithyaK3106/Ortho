# Ortho — Pilot & Monetization Readiness

**Purpose:** everything standing between Ortho today and a profitable SaaS
product engineering teams are happy to pay for, stated honestly. Every
claim below is either verified this session (with the evidence cited) or
explicitly marked as unverified/aspirational. Nothing here is estimated
when it could instead be measured — where a number is missing, that's the
gap, not an oversight.

This document answers one question: **how does Ortho become a profitable
SaaS that engineering teams are happy to pay for?** Not "what features
should we build?" — every section below is filtered through that lens.
Where the two questions would give different answers, this document picks
the business one and says so.

**Last updated:** 2026-07-16, after the false-positive audit + fix
(`docs/archive/FALSE_POSITIVE_AUDIT_2026-07-16.md`), memory-citation
feature (commit `a35b651`), alignment to the Ortho vNext roadmap
(Engineering Decision Engine, not another AI coding assistant), and a
product/GTM strategy pass (ICP, outcomes, flywheel, PMF criteria).

---

## 0. The one-sentence status

**Update (2026-07-16, later same day):** at the user's explicit direction,
all four vNext roadmap phases were built in this session — not just
Phase 1. This reverses the sequencing this document previously argued for
(build Phase 1, earn trust, then expand), so the honest framing changed:
Ortho now has substantially more surface area than any real user has ever
seen, which is a bigger, not smaller, version of the same underlying gap.
The core review loop is honest (91%→0% verified false-positive rate on a
9-repo hand-audit, re-confirmed on 8 repos this session — see Section 5a)
and has a real, working differentiator (memory citations, including
reject-reasons, verified end-to-end) — but **zero real users have touched
any of it**, so "profitable SaaS" is still gated on the same unanswered
questions as before, now applied to four phases of surface instead of
one: will a developer actually trust it, will they pay, and who
specifically has a reason to pay Ortho instead of a better-funded
competitor. The roadmap's own explicit warning against this sequencing
("do not let features distract from building the review engine") was a
real, named tradeoff, made consciously, not accidentally — see Section
5a for what got built, what got audited, and what's still unverified as
a result of building ahead of pilot data.

---

## 1. Market positioning — broadened, with local-first correctly scoped

The previous framing of this document unintentionally narrowed the market
to "teams using Claude Code who want local-first architecture review."
That's a deployment detail wearing a market-definition costume.

**The actual position:** Ortho is **Engineering Intelligence for
AI-assisted Software Development** — the layer that makes AI-generated
code trustworthy before it merges. Local-first is a real and durable
differentiator (Section 3 depends on it), but it is a *deployment
advantage*, not the product. A compliance team doesn't buy "local-first";
they buy "we can adopt AI coding tools without a new vendor touching our
source." Local-first is how Ortho delivers that; it isn't what's being
sold.

This distinction matters for roadmap sequencing: features should be
justified by the engineering-intelligence value they add, not by whether
they're "local-first enough." A feature that requires, say, opt-in
telemetry to work is not automatically disqualified — it has to be
evaluated on whether it serves the actual buyer, with local-first as one
input to that decision, not a blanket veto.

---

## 2. Ideal Customer Profile — one, not "developers"

"Developers" is not an ICP. Below is the profile this document commits
to, plus the alternates considered and rejected, because a document that
doesn't say no to some markets hasn't actually chosen one.

### 2.1 The chosen ICP

| Dimension | Profile |
|---|---|
| Company size | 30-300 engineers. Small enough that one bad AI-generated merge is felt org-wide; large enough to have a real budget line and more than one repo worth protecting. |
| Engineering team structure | Multiple teams sharing a codebase or a small number of interdependent repos — the pain of "I don't know what that other team's service depends on" has to already exist. |
| AI adoption level | Already shipping AI-generated code at meaningful volume (Claude Code, Copilot, Cursor, etc. in daily use) — not evaluating *whether* to adopt AI coding tools, but already living with the consequences. |
| Repository complexity | Nontrivial architecture (layered, modular, service boundaries) — a 3-file script repo has nothing for Ortho to protect. |
| Buying motivation | A structural reason code/architecture can't leave their infrastructure: compliance (SOC2/HIPAA/FedRAMP-adjacent), IP sensitivity, or a contractual/customer requirement, *not* just general caution. |
| Why they choose Ortho | They're already convinced they need AI-code review; local-first is the only way they're allowed to buy one at all. Competitors (CodeRabbit, Greptile, Qodo) are structurally disqualified before a feature comparison even starts. |
| Why they reject Ortho | (a) They're comfortable with a cloud reviewer and pick a more mature, better-funded competitor on features/polish; (b) they're too small to have a budget or a real architecture to protect; (c) they don't yet trust *any* AI review tool enough to pay for one — the market itself is still forming for them. |

### 2.2 Why this ICP over the alternatives

Considered and explicitly not prioritized:

- **Solo developers / small startups** — no compliance motivation, easy to
  reach but won't pay enough to matter, and local-first isn't a
  differentiator to someone with nothing to protect.
- **Large enterprise (1000+ engineers)** — the buying motivation is real
  and strong, but the sales motion (security review, procurement,
  multi-quarter cycles) requires infrastructure this project has zero of
  today (Section 8.5). Right ICP for Phase 3+ of the *business*, wrong
  ICP to validate product-market fit with first.
- **General AI-coding-tool users with no compliance constraint** — this is
  the market CodeRabbit/Greptile/Qodo already win with funding and
  polish. Competing here is a fight Ortho loses on resources, not
  product.

The chosen ICP is the smallest slice where Ortho's structural advantage
(local-first) is the actual reason to buy, not a nice-to-have — which
means it's the only slice where a five-person team with no sales
infrastructure has a real chance of closing pilots on product merit alone.

---

## 3. Why would someone pay — the actual value case, not the pitch

This has to be stated as a testable hypothesis, not marketing copy,
because nothing here has been tested with a real customer yet.

**The hypothesis:** teams matching the ICP above — shipping meaningful
volumes of AI-generated code, with a structural reason they can't or
won't send their codebase/architecture decisions to a cloud-based
reviewer — will pay for a local-first reviewer with compounding,
repo-specific memory, if and only if its false-positive rate is low
enough to trust on day one.

**Why this is a narrower claim than "all developers who use AI coding
tools":** general AI code review is proven-valuable at scale (CodeRabbit:
$40M ARR, ~$550M valuation) but that market is occupied by well-funded
competitors (CodeRabbit, Greptile, Qodo) and the architecture+memory
angle specifically has direct competitors already (Bito's AI Architect,
cubic.dev, Gemini Code Assist's team-memory feature) — none of whom can
be local-first the way Ortho structurally already is. Competing generally
is a fight Ortho loses to funding; competing on "the only option that
never leaves your machine" is a fight Ortho can actually win, for a
smaller but real market. This matches the roadmap's own instruction: "we
DO NOT compete on code generation, autocomplete, AI chat... we compete on
Engineering Decisions" — of the roadmap's four named differentiators
(Repository Intelligence, Engineering Memory, Evidence-backed Reasoning,
Local-first), the first is built, the third is half-built (see Evidence
Engine gap, Section 5), and the second is the smallest possible slice
(citation only, no reject-reasons yet).

**What makes a developer or team hesitate to work without it (the actual
retention mechanism, not a feature):** the memory citation, once it
includes rejected-recommendation context (Section 6.2), becomes something
literally impossible to get from a stateless tool — "you already tried
this, here's why it didn't work" is institutional memory a new hire on
the team doesn't have and a general reviewer can't produce. That's the
moat. Everything else in the product is either commoditized (general
review) or table stakes (evidence, explanations).

**A discipline worth naming:** memory is the moat, not the product.
Nobody buys "engineering memory" as a line item — they buy fewer
regressions, safer reviews, faster onboarding for new hires, and
decisions that don't repeat old mistakes. Memory is the infrastructure
underneath those outcomes. Every place this document or future roadmap
work is tempted to sell "memory" as a headline feature, it should instead
name the customer-facing outcome memory produces. Section 4 below is
written that way deliberately.

### 3.1 repowise — a named competitor that weakens the local-first wedge (added 2026-07-22)

**repowise** (AGPL-3.0, self-hosted, `pip install repowise`) is close enough to
Ortho's own shape that it has to be named here rather than left implicit.
It builds a dependency graph, git-history intelligence (hotspots, ownership,
co-change), a generated wiki, architectural-decision mining, a 25-marker
code-health score calibrated against a real defect corpus, and a 10-tool MCP
server — overlapping almost every capability row in Sections 1 and 4. It is
more mature on nearly every shared axis: 16 languages parsed to AST (Ortho is
Python-only), a real web dashboard (Ortho has none), a defect-corpus-validated
health score with head-to-head benchmarks published against CodeScene, a VS
Code extension, and a hosted commercial tier already live.

**Why this specifically matters to Section 3's hypothesis:** the ICP argument
above rests on local-first being a structural moat competitors can't cross —
"none of whom can be local-first the way Ortho structurally already is."
repowise **is** local-first, self-hostable, and requires no API key to index
a repo. That sentence is no longer true. A compliance-motivated buyer in the
chosen ICP (Section 2.1) now has a more mature, free, open-source option that
satisfies the same "no vendor touches our source" requirement and does more.

**What still differs, and is where Ortho's remaining case has to live:**
- Ortho's `feedback` loop cites *rejected* recommendations with the original
  reason back to the user, verified end-to-end (Section 5) — a sharper claim
  than repowise's transcript-mined decisions, if it holds up under real usage.
- Ortho is a prescriptive workflow engine (ASES: PLANNER → ARCHITECT →
  BUILDER → TEST-DESIGNER → VERIFIER → REVIEWER via `ortho orchestrate`), not
  just an intelligence/context layer. repowise does not attempt to gate or
  sequence changes through a workflow — it surfaces information for whatever
  agent or human is doing the work.

**What this changes:** local-first alone is no longer a sufficient answer to
"why Ortho and not a competitor" in Section 2.1's ICP table — it should be
treated as necessary but not differentiating. The pilot should explicitly
test whether the reject-reason memory and the workflow-gating model, not
local-first by itself, are what a real buyer says they'd pay for. If neither
survives contact with a pilot customer, Section 2's ICP needs revisiting, not
just this section's wording.

---

## 4. Customer outcomes, not features

The roadmap and this document previously described technical capabilities
(Evidence Model, Review Coverage, Engineering Memory). Rewritten as
outcomes a buyer actually recognizes:

| Instead of saying | Say |
|---|---|
| "Evidence Model" | Developers trust recommendations without manually tracing dependencies themselves. |
| "Review Coverage Rate" | Less AI-generated code reaches production unreviewed — reducing engineering review effort per merge, not adding a new review step on top of the old one. |
| "Memory citations" | The tool remembers what this specific team already tried and rejected, so nobody re-argues a settled decision or re-introduces a bug the team already paid to learn about. |
| "Architecture pattern detection" | New hires and AI tools both stop violating boundaries nobody wrote down but everyone on the team already knows. |
| "Layer boundary / dependency direction checks" | Structural mistakes get caught before code review, not after a production incident traces back to them. |
| "Local-first, zero cloud dependency" | Adopt AI coding tools without a new vendor gaining access to your source code — the actual blocker for the ICP's compliance/security sign-off. |

Every future feature proposed for this project should be run through the
same test before it's built: what customer pain does it remove, what
measurable business outcome does it move, and why would someone pay for
it specifically. A feature that only answers "what's technically
interesting to build" fails this test regardless of engineering merit.

---

## 5. What's actually true today (verified, not aspirational)

| Claim | Status | Evidence |
|---|---|---|
| `guardrails`/`decide`/`plan`/`refactor`/`review`/`ask`/`orchestrate`/`cross-repo`/`feedback` run end-to-end on unseen repos without crashing | ✅ Verified, broadened | Originally verified against `custom_yolo` only; this session re-verified all 9 commands against click, requests, flask, celery, django (2922 files), fastapi, and sqlalchemy — see Section 5a |
| False-positive rate on real repos | ✅ Re-verified this session, `layer_boundaries` caveat below | 9-repo hand audit → 96 true-positive violations (original). This session: `layer_boundaries` redesigned (real persistence/framework-import evidence, not topology) and re-audited across 8 repos including sqlalchemy (an ORM) and fastapi (heavy DI) — **it fired zero times on any of them.** `dependency_direction` and `module_sizing` re-verified true-positive on the same 8 repos (module_sizing: 14 counts hand-checked against `wc -l`, 100% exact). See Section 5a for why "zero false positives" here is not the same claim as "verified correct." |
| Memory citations ("seen before" + "rejected before, here's why") | ✅ Verified working end-to-end | First run on fresh repo → no citation; second run → cites the first; cross-command citation (decide cites guardrails) confirmed; this session added and verified the reject-reason path on django (a repo never used for this test before): rejected a real finding with a reason, next scan cited the exact reason |
| Install path works on a fresh clone | ✅ Verified, fixed | Simulated fresh-clone install found 8/13 workspace packages silently failed to install; fixed `install.sh`/`install.bat`/docs. Re-verified this session: all 13 explicit `-e` paths still resolve; this session's 4 new source files (`feedback.py`, `test_recommender.py`, `repo_qa.py`, `cross_repo.py`) are correctly auto-packaged (poetry-core src-layout discovery, no config change needed) |
| MCP server starts and is reachable from Claude Code | ✅ Verified, broadened | Starts in <2s; grew from 5 to 10 tools this session, all 10 confirmed reachable via a real stdio protocol round-trip test (not just handler functions working in isolation) |
| Local-first, zero cloud dependency | ✅ Structurally true | SQLite-only, no auth, no network calls in the reviewed code paths |
| Architecture *style* classification accuracy | ⚠️ Documented gap, partially addressed, unchanged this audit | Still 75% vs. an 83.3% target (`test_phase5_3_benchmarks.py`) — confirmed as the same 3 pre-existing failures by this session's fresh full-suite re-run, no new regression. One root cause was fixed earlier this session: `sqlalchemy` was confidently WRONG (`LAYERED @ 0.51`) and now correctly reports `UNKNOWN @ 0.18`. Remaining gap unchanged: `sqlalchemy`/`requests` report `UNKNOWN` where the benchmark expects `FLAT` (a ground-truth definitional mismatch, not a code bug — see prior entry in git history), `celery` sits exactly at the confidence threshold. |
| mypy --strict compliance | ✅ Re-verified, slightly improved | Clean on cli-commands (all 13 files including this session's 4 new ones, after fixing 3 new errors found in `repo_qa.py`), arch-guardrails, refactoring-advisor, decision-engine. arch-intelligence: 106 pre-existing errors (down from 109 — this session's `_score_layered` fix incidentally removed 3), none in code this session touched. TS: `strict`+`noImplicitAny` confirmed genuinely enabled (not just claimed), zero compile errors. |
| Real developer usage / trust | ❌ Zero data | No pilot has run. Every claim about adoption, retention, or willingness to pay below is a hypothesis, not a finding — now true across 4 phases of surface instead of 1 |
| Willingness to pay | ❌ Zero data | Not tested in any form — no pricing page, no paid pilot, no LOI |
| Evidence Engine (roadmap's core requirement: every finding cites evidence) | ✅ Built and verified this session | Every `GuardrailViolation`/`Recommendation` construction site now populates real, checkable evidence (measured line counts, real import edges, real cycle chains) instead of the empty list documented as a gap earlier this session. Verified live against celery: every finding shows concrete evidence lines. This closes what was previously the single biggest gap between built state and the roadmap's own non-negotiable requirement. |
| Ideal Customer Profile | ❌ Zero data | Section 2's ICP is a hypothesis derived from the product's structural advantages, not from any customer conversation. Must be validated or corrected in the pilot, not assumed true going in. |

---

## 5a. Full-system audit (2026-07-16, later same day) — after building all four roadmap phases

The user directed building all four vNext phases in one session (Evidence
Engine, Test Intelligence, accept/reject feedback loop, Repository Q&A,
Cross-Repository Intelligence, Workflow Orchestration) rather than the
roadmap-prescribed "earn trust in Phase 1 first" sequencing, then asked
for a full audit to confirm pilot-readiness. This section is that audit's
result — run independently after the build, not self-reported by the
same work that built the features.

**Test suite: 1375 passed, 2 skipped, 13 xfailed, 46 xpassed, 3 failed
(all 3 pre-existing and already documented above), zero new regressions.**
Every package's suite re-run fresh, individually (this repo's pytest has
a known rootdir collision when multiple packages' `tests/` dirs are
collected together). Two non-blocking findings: 46 stale `xfail` markers
in repo-intelligence (bugs likely fixed without updating the markers —
test-hygiene debt, not a functional problem), and zero TS-level (jest)
test coverage for the 4 new CLI commands added this session — only
Python-side `CliCommands` tests plus manual CLI smoke tests exist for
them, meaning the Commander.js argument-parsing/wiring layer itself has
no dedicated test. Real gap, not urgent, listed as follow-up work.

**Static/type-check: 3 new mypy errors found and fixed** (all in
`repo_qa.py`, this session's newest file — missing param annotations and
an `Any`-inference leak from `max(key=...)`). Fixed via a structural
`Protocol` type and an explicit local annotation; `cli-commands` package
is now fully mypy --strict clean across all 13 files. No other package
regressed.

**End-to-end CLI + MCP smoke test across multiple real repos** (click,
sqlalchemy, django, requests, typer — not just click, which had been this
session's most-used and potentially over-fit fixture): every command
produced coherent output with correct exit codes. `ortho review` on
django (2922 files) took 55s; `ortho ask` on sqlalchemy took 45s — both
real but acceptable for a first-scan cold-start. **One real performance
bug found and fixed**: `ortho cross-repo` on two real, moderately-sized
repos (click + typer, no artificial size) took **nearly 11 minutes** —
confirmed independently, twice, on different repo pairs. Root cause: the
underlying AST-similarity algorithm (`ReuseDetector.find_similar`,
pre-existing and correct for its original within-one-repo use case) is
O(n²) per symbol-type bucket, and pooling two whole repos' symbols
crosses that cliff. **Fixed**: a symbol-count guard now fails fast (~7s,
with an actionable "scope to a subdirectory" message) instead of hanging
for minutes with no feedback — verified the fix doesn't break the
previously-working scoped-subdirectory case (still ~37s). This was a
real, shippable-as-a-bug gap that the original build session's own
testing (scoped to subdirectories throughout) never triggered — exactly
the kind of thing an independent audit exists to catch.

**False-positive re-audit (the most important finding of this audit):**
re-ran the original 9-repo hand-verification methodology against the
redesigned `layer_boundaries` rule across 8 real repos (click, requests,
flask, celery, django, fastapi, sqlalchemy, typer) — deliberately
including sqlalchemy (an ORM, the exact kind of codebase the rule targets)
and fastapi (heavy dependency injection). **`layer_boundaries` fired zero
times across all 8 repos.** `dependency_direction` and `module_sizing`
both re-confirmed at the same true-positive rate as the original audit
(module_sizing: every count hand-checked against `wc -l`, exact match).
**This must not be reported as "0% false-positive rate, verified safe."**
The rule never got a chance to be wrong on this sample — the only
evidence it works at all is one synthetic Flask+SQLAlchemy fixture built
during development specifically to exercise it. The honest status is:
*redesigned to require real evidence, confirmed to no longer fire on
false positives, but still unconfirmed to fire correctly on any real,
naturally-occurring repo.* A pilot is the only way to close this gap —
no further hand-auditing of more open-source repos is likely to help,
since the pattern this rule targets (one file cleanly importing only a
persistence library, a different file cleanly importing only a web
framework, with a real dependency between them) may simply be rarer in
practice than the rule's design assumed.

**Fresh-install/onboarding: one real, non-blocking doc gap found and
fixed.** `MCP_SETUP.md` claimed "5 new tools" (stale — actually 10) and
gave a broken install one-liner (`pip install -e packages/*`, which
would fail on non-package directories under `packages/`) in two places.
Fixed: tool list updated to all 10, both broken commands replaced with a
pointer to `install.sh`/`install.bat` (the actual correct, already-tested
install path) so this can't drift out of sync again. `install.sh`/
`install.bat` themselves were unaffected and still correct. CLI `--help`
output confirmed clear for a first-time user, including honest scope
statements on new commands (e.g. `orchestrate --help` states it does not
approve or merge anything). Cold-start timing: `ortho review` on flask,
fresh, no cache: 1.68 seconds — a strong first-value signal.

**Net effect on this document's central claim:** the four new phases are
real, tested, and did not degrade Phase 1's verified false-positive rate
or introduce new crashes — but they also did not, and could not, answer
the question this document has said from the start only a pilot can
answer. Building more before that pilot runs made the honest gap wider
(more capability with zero user validation), not narrower, which is the
literal risk the roadmap named when it said not to do this. Section 6.1's
sequencing recommendation (run the pilot before building further) is now
more urgent, not less.

---

## 6. Product gaps — what's missing before this is sellable

### 6.1 Blocking (must happen before any paid pilot)

- **Run the real pilot.** Everything else in this document is downstream
  of this. Five real developers matching the ICP (Section 2), real repos,
  2-4 weeks, measuring the strategy's own North Star: **Review Coverage
  Rate** (Ortho-reviewed AI changes ÷ total AI-assisted merges) and
  whether they default to "run Ortho first." Nothing else in this list
  matters if this doesn't happen — it's the only thing that converts "we
  fixed the noise" into "developers trust it," and the only thing that
  can confirm or kill the ICP hypothesis in Section 2.
- ~~Redesign or permanently retire `layer_boundaries`~~ **Done, this
  session.** `LayerDetector` no longer derives layer identity from
  import-graph topological depth (the mechanism that caused the 100%
  false-positive rate). It now only assigns a module to the Data or
  Presentation layer when it has real, checkable evidence: an actual
  import of a known persistence/ORM library (`sqlalchemy`, `psycopg2`,
  `pymongo`, etc.) or a known web/API/CLI framework (`flask`, `fastapi`,
  `django`, `click`, etc.). Modules with no such evidence get no layer at
  all — excluded from boundary checking entirely, not defaulted to layer
  0 the way the old topology-based version did. Re-enabled in
  `ArchitectureEnforcer.check_violations()`. Verified against the same
  5 audited repos: `layer_boundaries` now fires 0 times on flask, celery,
  click, requests, and django (all of which had 11-142 false positives
  from it before), and correctly fires on a synthetic Flask+SQLAlchemy
  fixture built specifically to exercise it — confirming the rule is
  silent by default (no evidence → no opinion) rather than silent because
  it's been disabled. Not yet re-run through the full hand-verification
  audit process on a fresh repo sample — that re-audit is the next thing
  that should happen before this is claimed as pilot-ready in a listing
  document, not just here.
- **Architecture-style classifier accuracy gap: partially addressed, not
  closed.** This session fixed the specific mechanism that made the
  classifier *confidently wrong* on `sqlalchemy` (directory-name
  coincidence with zero real cross-directory dependency evidence,
  identical root cause to the `layer_boundaries` fix above) — it now
  reports `UNKNOWN` with low confidence instead of a fabricated `LAYERED`
  answer. Benchmark accuracy is still 75% (6/8), unchanged in raw number,
  but the failure mode changed from "wrong and confident" to "honestly
  uncertain," which is the same tradeoff this project already committed
  to for `click` in an earlier session — not a new standard invented
  here. What's NOT done: `layer_boundaries`'s new evidence-gating (this
  session's other fix) no longer depends on this classifier at all, so
  that specific worry is resolved; but `decide`/`plan` still consume
  `ArchitectureDetector`'s style output for other purposes and haven't
  been individually re-audited for how they behave when it returns
  `UNKNOWN` instead of a wrong-but-confident answer.
- **A pricing model that isn't "TBD."** Section 9 below has options; none
  are decided. You cannot run a paid pilot without deciding this first.

### 6.2 Needed for retention, not just first impression

- **Accept/reject feedback loop.** Currently, memory citations say "seen
  before" but never "rejected before, and here's why" — the single most
  differentiated sentence in the whole product vision (per the strategy
  memory) requires a user action (`ortho feedback accept/reject`) that
  doesn't exist yet. This is real, scoped, unbuilt work — and unproven:
  nothing says developers will actually use it.
- **Structured Evidence model.** `GuardrailViolation`/`Recommendation`
  both have an `evidence: list[str]` field that's mostly unpopulated
  today. A finding a developer can't independently verify is a finding
  they'll stop trusting the first time it's wrong — and the classifier
  gap above guarantees it will be wrong sometimes. (Full spec in
  `docs/architecture/ORTHO_VNEXT_DELTA_BLUEPRINT.md`, Phase 2.2.) In
  outcome terms (Section 4): this is what lets a developer trust a
  recommendation without tracing the dependency themselves — without it,
  Ortho is asking for trust it hasn't earned.
- **Unified `ortho review` command.** Today a developer must know to call
  `guardrails` and separately `decide` to get the full picture. This is
  trial friction, not a value gap, but friction in a 5-minute pilot
  onboarding is exactly the kind of thing that loses a pilot before the
  real value is even seen.

### 6.3 Explicitly NOT needed yet — do not build these before the pilot

Per the roadmap, these are later-phase capabilities (Phase 2-4) or
explicitly rejected altogether — building them now is scope creep against
a Phase 1 product, not a shortcut:

- Repository Q&A ("how does auth work?") — the roadmap places this
  explicitly last ("Repository Q&A should come much later... do not let
  conversational interfaces distract from building the review engine"),
  and it's also the most crowded, least-differentiated part of the
  competitive landscape.
- Change Impact analysis, Test Intelligence, Safe Refactoring guidance —
  Phase 2 ("Own Engineering Decisions") capabilities per the roadmap;
  they depend on Phase 1 review being trusted first, which hasn't
  happened yet.
- Engineering Memory beyond citation ("rejected before, and why") —
  Phase 3 territory; the roadmap is explicit that memory should
  accumulate automatically from real review usage, which requires a
  pilot generating that usage in the first place.
- Cross-repo/organization intelligence — Phase 4, years away by the
  roadmap's own sequencing.
- Streaming responses, response caching, incremental re-indexing beyond
  what exists — nothing in verified usage patterns needs this; scans
  complete in seconds on real repos already.
- ADR/Slack/incident-report ingestion — unbounded integration surface,
  no pilot signal yet that anyone wants it.
- A dashboard or web UI — the roadmap explicitly rejects this
  ("another IDE... another chat interface" is a listed anti-goal); the
  product thesis is "inside the tool developers already use" (Claude
  Code via MCP), and a separate UI competes with that thesis.

---

## 7. Roadmap organized around customer jobs, not technology

The vNext roadmap's four phases (Own Review → Own Decisions → Engineering
Memory → Intelligence Layer) describe *what gets built*. Reframed around
*what makes Ortho indispensable to the customer* at each stage — the
sequencing is the same, the justification for each phase changes:

**Phase 1 — Become indispensable before every merge.**
Every AI-generated change gets reviewed with repository-specific
context before it merges. This is the current phase (Section 0). Maps
1:1 to the roadmap's "Own AI Review."

**Phase 2 — Become indispensable before every major code change.**
Before a developer or an AI agent starts a nontrivial change, Ortho
tells them the blast radius, the relevant history, and the risk — not
just reviewing after the fact but informing the decision before code is
written. Maps to the roadmap's "Own Engineering Decisions."

**Phase 3 — Become indispensable when understanding an unfamiliar
codebase.** New hires, contractors, and AI agents working in an
unfamiliar part of the repo get answers grounded in the actual call
graph and accumulated team memory, not a guess. Maps to the roadmap's
"Engineering Memory" — the memory built in Phases 1-2 is what makes this
phase possible at all, which is why it can't be built first.

**Phase 4 — Become indispensable for engineering teams and leadership.**
Architecture health, technical debt trends, and risk patterns become
visible at the team and org level, not just per-PR. Maps to the
roadmap's "Engineering Intelligence Layer."

The point of this reframe: each phase must earn the next one by making
itself genuinely hard to work without, not by shipping the next
technology layer on schedule. Phase 2 work should not start until Phase
1 has pilot evidence that developers actually feel the loss when Ortho
isn't running — same discipline the roadmap already states, restated in
terms of what "indispensable" concretely means at each stage.

---

## 8. Customer outcomes by phase

For each phase in Section 7: the customer problem it solves, the outcome
delivered, the KPI on each side, and why a team would keep paying. This
is deliberately the most business-oriented section in the document.

### Phase 1 — Before every merge

- **Customer problem:** AI-generated code merges faster than humans can
  review it carefully; architectural mistakes and repo-specific
  conventions get missed.
- **Customer outcome:** Developers trust recommendations without
  manually tracing dependencies; less AI-generated code reaches
  production unreviewed.
- **Engineering KPI:** False-positive rate, Evidence Coverage (Section
  10).
- **Business KPI:** Review Coverage Rate, Time-to-first-value.
- **Why they keep paying:** The false-positive rate stays low enough
  that skipping Ortho starts to feel like the risky choice, not running
  it. This is unproven — it is the entire pilot's job to find out.

### Phase 2 — Before every major change

- **Customer problem:** Developers (and AI agents) don't know the blast
  radius of a change until something breaks downstream.
- **Customer outcome:** Safer changes, fewer regressions traced back to
  "nobody knew that service depended on this."
- **Engineering KPI:** Impact-analysis accuracy (precision/recall against
  real downstream breakage — not built or measured yet).
- **Business KPI:** Reduction in regression-caused incidents per pilot
  team (requires a baseline from the team, not inventable by Ortho).
- **Why they keep paying:** Once a team has been saved from a real
  incident by an impact-analysis warning, the cost of not having it
  becomes concrete and rememberable — same mechanism as Phase 1's moat,
  one level up.

### Phase 3 — Understanding unfamiliar code

- **Customer problem:** New hires and AI agents waste time (and make
  mistakes) navigating code nobody wrote documentation for.
- **Customer outcome:** Faster onboarding, fewer "I didn't know that was
  how it worked" mistakes, from people and from AI tools.
- **Engineering KPI:** Answer accuracy against a real call graph (not
  vector-search guesswork) — not built.
- **Business KPI:** Time-to-productivity for new hires (requires customer
  baseline).
- **Why they keep paying:** Institutional knowledge that would otherwise
  leave when a senior engineer does now persists in the tool. This is
  the clearest "switching cost" moment in the whole roadmap.

### Phase 4 — Team and leadership visibility

- **Customer problem:** Engineering leadership has no visibility into
  architectural drift or accumulating technical debt until it's a
  crisis.
- **Customer outcome:** Debt and risk trends visible before they become
  incidents; defensible engineering decisions for leadership
  conversations.
- **Engineering KPI:** Not defined yet — depends on what Phase 1-3 data
  actually looks like at scale.
- **Business KPI:** Expansion revenue (more seats/repos within an
  existing account) — the natural monetization point for
  leadership-facing value.
- **Why they keep paying:** This is the phase where Ortho stops being a
  developer tool and becomes something a VP of Engineering has a reason
  to renew regardless of any single developer's day-to-day usage.

**Honesty check:** only Phase 1's KPIs have real data behind them today
(Section 5). Phases 2-4 are hypotheses, correctly sequenced per the
roadmap, not commitments with dates.

---

## 9. The daily habit — why Ortho gets used continuously, not occasionally

A gap in the previous version of this document: it never explained why a
developer would open Ortho on a normal Tuesday, as opposed to remembering
it exists during a big scary refactor. Without a daily habit, Ortho is a
tool people mean to use, not one they do use — and "meant to" doesn't
retain a subscription.

**What the daily habit needs to look like, in priority order for a Phase
1 product:**

1. **Every AI-generated PR automatically runs through Ortho** before a
   human looks at it — not a separate command a developer has to
   remember to run. This is the single highest-leverage habit-forming
   mechanism available and doesn't exist yet (Section 6.2's unified
   `ortho review` command is the prerequisite, not the whole thing — CI
   integration is the rest, and isn't scoped yet).
2. **A short morning/session-start summary**: what changed since last
   session, any new risky changes flagged, any recently-rejected
   recommendation that's relevant again. Not built. Would need to be
   genuinely short (a human reads it in under a minute) or it becomes
   noise the way most "digest" features do.
3. **Architecture health and technical-debt trend surfacing** — Phase 4
   territory (Section 7), explicitly not a Phase 1 concern.

**What NOT to build toward this yet:** a dashboard, a notification
system, or anything with its own UI — all three would contradict Section
6.3's explicit rejection of a separate UI, and none of them are proven
necessary until item 1 (automatic PR review) has pilot evidence that
developers actually engage with what Ortho already surfaces. Habit
formation should be earned incrementally, same discipline as the rest of
this document: build the smallest thing that creates the habit, measure
whether it does, then decide if more is warranted.

---

## 10. The Ortho flywheel

```
Developer's AI-generated PR runs through Ortho automatically
                    ↓
Ortho catches a real issue, with evidence the developer can verify
                    ↓
Developer trusts the finding (because it was right and checkable)
                    ↓
Developer runs Ortho more — proactively, not just via automatic PR checks
                    ↓
More usage → more accept/reject signal → engineering memory improves
                    ↓
Recommendations get more repo-specific and more accurate over time
                    ↓
Team adoption increases (one developer's trust becomes the team's default)
                    ↓
Shared organizational memory grows (rejected approaches, past incidents,
architectural decisions specific to this codebase)
                    ↓
Switching cost increases — a competitor starts with none of this history
                    ↓
Retention improves
```

**Why this is a real moat and not just a diagram:** every step depends on
the previous one being genuinely true, not assumed. The flywheel breaks
immediately at step 2 if the false-positive rate isn't low enough
(Section 5's 96-violation, 100%-true-positive result is the first piece
of evidence this is achievable, not proof it holds at pilot scale). It
breaks at step 5 if the accept/reject loop (Section 6.2) never gets used.
Nothing past step 2 exists yet — this diagram describes the intended
mechanism, not a measured one. The pilot's job is to validate steps 1-3;
nothing downstream of that can be tested until those hold.

**What makes it defensible against better-funded competitors:** a
cloud-based competitor could copy the review engine and even the
evidence model. They cannot copy a specific team's two years of
accepted/rejected recommendations without that team's actual usage
history — which is exactly why memory is the moat (Section 3) even
though it's never the thing being sold (Section 4).

---

## 11. SaaS strategy — pricing, expansion, adoption, retention, enterprise, open-source

None of the below has been tested. Listed as options with tradeoffs and
what a pilot should validate, not a recommendation to build billing
infrastructure yet — consistent with Section 6.1's blocking item that a
pricing *decision* (not a full billing system) is needed before a paid
pilot can run.

### 11.1 Pricing philosophy

| Model | Fit | Risk |
|---|---|---|
| Per-seat/month (like Bito's $15, cubic's $30-79) | Familiar to buyers, easy to compare | Commoditizes Ortho against better-funded per-seat competitors on price alone |
| Per-repo/month | Matches "local-first, per-codebase memory" positioning; memory has zero value across repos anyway, so pricing per-repo is honest about what's actually being sold | Harder to explain to a buyer used to per-seat pricing |
| Team license, self-hosted, annual | Matches the "never leaves your infrastructure" buyer directly; higher ACV, slower sales cycle | Requires actual enterprise sales motion this project has zero infrastructure for today (contracts, security review support, SLAs) |
| Free/open-core with a paid "team memory sync" tier | Lowers adoption friction; monetizes the actual differentiator (memory) directly | Requires building multi-user memory sharing, which doesn't exist and adds real complexity |

**Recommendation for the pilot phase specifically:** don't charge yet.
Run the pilot free, and ask directly at the end: "would you pay, how
much, and why/why not." That answer is worth more than guessing a price
now and discovering later it was wrong in either direction.

### 11.2 Adoption strategy

Bottom-up (individual developers self-install) is the only motion this
project can execute today — there is no sales team, no outbound
infrastructure. This is consistent with the ICP being teams already using
AI coding tools daily: those developers are the ones who'd find and try
Ortho without a sales conversation. Top-down (leadership mandates
adoption) is a Phase 4 motion (Section 8), once there's org-level value
to sell to a VP of Engineering — not viable before that value exists.

### 11.3 Retention strategy

Retention is the flywheel (Section 10), not a separate mechanism. The one
thing worth stating explicitly: retention in this product should be
measured by whether developers *choose* to keep running Ortho, not by
contract lock-in — a compliance-motivated buyer (Section 2) will not
accept vendor lock-in as a substitute for genuine value, and trying to
engineer switching costs artificially (proprietary data formats, export
friction) would actively contradict the trust-based positioning this
whole document argues for.

### 11.4 Enterprise strategy

Explicitly deferred. The ICP (Section 2) is mid-size teams reachable
without an enterprise sales motion. Enterprise (SSO, RBAC, audit logs,
formal SLAs, security questionnaires) is real future work but building it
before Phase 1 has pilot validation would be building sales
infrastructure for a product that hasn't proven anyone wants it yet.

### 11.5 Open-source strategy

Not decided, and shouldn't be until the pilot answers a prior question:
does the false-positive rate and evidence quality hold up outside a
hand-picked 9-repo audit? An open-core strategy (core review engine open,
memory/team features paid) would align open-source goodwill with the
actual monetized differentiator (Section 4), but open-sourcing before
Phase 1 is validated risks broadcasting a product that isn't ready to
represent Ortho publicly yet.

### 11.6 Paid vs. free features — a first cut, not a decision

Only sensible once pricing model (11.1) is chosen, but the shape that's
consistent with "memory is the moat, not the product" (Section 4): review
+ evidence engine could plausibly be the free/adoption layer, with
persistent cross-session memory and the accept/reject feedback loop
(Section 6.2) as the paid layer. This is a hypothesis to validate with
pilot users' actual willingness-to-pay answers, not a pricing page draft.

---

## 12. Product-market fit criteria

How will it be known that Ortho has achieved PMF? Defined here so the
pilot has a target instead of a vague "see how it goes." Vanity metrics
(installs, GitHub stars, commands run) are deliberately excluded.

| Indicator | What it means | Currently measured? |
|---|---|---|
| Daily usage | Developers run Ortho (or it runs automatically) on a normal day, not just during audits | No — Section 9's daily habit isn't built yet |
| Review Coverage | Ortho-reviewed AI changes ÷ total AI-assisted merges, trending up over the pilot | No |
| Repeat usage | Same developer still using it in week 3-4 without being reminded | No — requires the pilot to run |
| Developer trust | "Hesitation to code without it" asked directly after 2 weeks (Section 13) | No |
| Pilot retention | Pilot team wants to keep using it after the formal pilot ends, unprompted | No |
| Willingness to pay | Explicit yes, with a number, asked directly at pilot end (Section 11.1) | No |
| Team expansion | Usage spreads beyond the initial pilot developer to teammates without a push | No |
| Referral behavior | A pilot developer recommends Ortho to another team unprompted | No |

None of these exist as data today. This table is the target the pilot is
run against — Section 13 below covers the mechanics of measuring the
subset that overlaps with existing engineering metrics.

---

## 13. Metrics that must exist before "profitable SaaS" is a real question

The roadmap names its own success metrics explicitly (Section "Success
Metrics"): False Positive Rate, Unsupported Findings, Evidence Coverage,
Review Adoption, Review Completion Rate, Review Coverage, Developer Trust,
Pilot Retention, Engineering Time Saved — and explicitly rules out lines
of code generated, tokens consumed, and chat usage as vanity metrics not
to optimize for. Mapped to what this project can concretely measure:

- **Review Coverage Rate** = Ortho-reviewed AI changes ÷ total AI-assisted
  merges, per pilot user. This is the actual adoption signal — not
  installs, not commands run, not stars.
- **False-positive rate, ongoing** — measured the same way this session's
  audit measured it (hand-verified, not estimated), re-run periodically
  as the codebase and detection logic evolve, not just once.
- **Evidence Coverage** — the roadmap treats this as a first-class metric
  in its own right, not a footnote of false-positive rate: what fraction
  of findings carry real, independently-checkable evidence vs. an empty
  `evidence: list[str]`. Currently unmeasured because the field is mostly
  unpopulated (see Section 6.2) — this needs to exist before Evidence
  Coverage can be reported at all.
- **"Hesitation to code without it" after 2 weeks** — the strategy's
  literal product-market-fit test (maps to the roadmap's "Developer
  Trust" / "Pilot Retention"). Binary, per pilot user, asked directly.
- **Time-to-first-value** — how long from `ortho init` to the first
  moment a developer sees a finding that changes what they do. Not
  measured yet at all.

None of these exist as dashboards or tracked numbers today. Before
scaling past five pilots, at least False Positive Rate and Evidence
Coverage need to be instrumentable without manual re-auditing every time
— they're the two the roadmap ties directly to trust, which is the whole
Phase 1 bet.

---

## 14. Sequencing — what to do, in order

1. **Decide and build nothing new until the pilot is scoped.** Recruit
   five pilot developers matching the ICP (Section 2: mid-size team,
   already using AI coding tools daily, real compliance/IP motivation,
   willing to run Ortho for 2-4 weeks).
2. **Ship the unified `ortho review` command (Section 6.2)** — the one
   piece of friction-reduction worth doing before the pilot starts,
   because it's the first five minutes of the pilot's experience, and the
   prerequisite for Section 9's automatic-PR-review daily habit.
3. **Run the pilot.** Measure Review Coverage Rate and false-positive
   rate on real usage (not just the hand-audited sample), weekly. Use
   this to validate or correct the ICP hypothesis (Section 2) — pilot
   recruiting itself is the first real test of whether that profile is
   right.
4. **Mid-pilot checkpoint:** if false-positive rate on real usage is
   materially worse than the 9-repo audit suggested, stop and fix before
   continuing — don't let a bad first impression run its full course.
   The flywheel (Section 10) breaks at step 2 if this isn't caught.
5. **Build the accept/reject feedback loop (Section 6.2)** only if pilot
   developers are actually opening the report and reading citations —
   if they're not reading what's already there, a new interaction won't
   get used either. Verify engagement with what exists before adding
   more.
6. **After the pilot: ask about willingness to pay directly**, using
   Section 11.1's options as discussion starting points, not a fixed
   menu. Also ask the other PMF questions in Section 12 (team expansion,
   referral, repeat usage) directly rather than inferring them.
7. **Only then** decide whether to build billing infrastructure,
   positioning/marketing, or expand beyond the local-first niche — in
   that order, and only with real pilot data backing each decision.

---

## 15. What "profitable SaaS" concretely requires that doesn't exist today

Being blunt about the parts of this that are business infrastructure, not
product work, since they're easy to forget while heads-down on features:

- No billing system, no payment processing, no subscription management.
- No terms of service, privacy policy, or security documentation a
  compliance-conscious buyer (the exact buyer this positioning targets,
  Section 2) would ask for before signing anything.
- No support channel, no SLA, no incident process.
- No pricing page, no sales collateral beyond internal strategy docs.
- No usage analytics or telemetry (deliberately, so far, consistent with
  local-first positioning) — meaning Section 13's metrics currently
  require manual pilot check-ins, not a dashboard. That's fine for five
  pilots; it does not scale past that.
- No enterprise sales motion (Section 11.4) — deliberately out of scope
  until Phase 1 is validated, but worth naming so it isn't mistaken for
  an oversight later.

None of this blocks running the five pilots. All of it blocks charging
anyone real money afterward, and should be sized honestly (weeks, not
days) once the pilot data says it's worth building.
