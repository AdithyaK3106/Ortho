<title>Ortho — The Definitive Pilot Roadmap</title>

# Ortho — The Definitive Pilot Roadmap

**Built from first principles. Optimized for one outcome: developers refuse to merge AI code without Ortho.**

---

## 1. Executive Summary

After stripping every assumption, here is the honest strategic picture:

**The product is not "prepare + review." The product is engineering memory that reviews code.**

Three first-principles conclusions drive everything below:

1. **Review is the wedge, not Prepare.** The bottleneck in AI-assisted development has shifted from *generation* to *verification*. Claude Code and Cursor are getting rapidly better at exploring repos on their own — the "context assembly" value prop erodes every quarter. But the anxiety of "AI wrote 400 lines and I'm not sure I trust it" is *growing*, not shrinking. Review addresses the pain that compounds. Prepare addresses the pain that's disappearing.

2. **ContextHub must start accumulating on Day 1 — silently.** The moat is not a feature you build in v1.1. It's a byproduct of usage: every review verdict, every accepted/rejected finding, every architectural rule enforced becomes engineering memory no competitor can recreate. You don't build the moat. You *capture* it while shipping the wedge.

3. **MCP moves from v1.1 to Week 3.** (This reverses my earlier advice.) An MCP server wrapping two functions is days of work, not weeks — and it's the difference between "a habit developers must remember" and "a workflow that happens automatically inside Claude Code." Copy-paste friction will kill retention by week 3 no matter how good the output is. Friction reduction is not polish; it's survival.

**The five-stage architecture is internal philosophy, not product.** In the pilot product: Planner and Architect collapse into "the memory," Builder is Claude Code (not yours), Reviewer is the product, Verifier doesn't exist yet. Ship two commands backed by one growing memory.

---

## 2. Product Strategy

### The one-sentence product

> **Ortho reviews AI-generated code against your repository's own engineering knowledge — and gets smarter every time you use it.**

Not "better context." Not "five intelligence stages." Not "engineering platform." A reviewer that knows *your* codebase's rules, decisions, and history — which generic AI review tools (and Claude Code's built-in review) fundamentally cannot, because that knowledge lives outside any single session.

### Why this framing wins

Apply your own competitive filter — "If Claude Code adds this tomorrow, does Ortho still matter?" — to every candidate value prop:

| Value prop | Claude Code adds it tomorrow? | Survives? |
|---|---|---|
| Assemble repo context before generation | Already doing it (agentic search, /init) | ❌ Dies |
| Generic diff review (bugs, smells) | Already exists (/code-review) | ❌ Dies |
| Token optimization | Prompt caching + cheaper models erode it | ❌ Dies |
| Architecture detection as a report | Nice demo, no daily pull | ❌ Dies |
| **Review against YOUR accumulated ADRs, decisions, past incidents — persistent across sessions and across tools** | Cannot: session-scoped, single-tool, no persistent memory layer | ✅ **Survives** |
| **Memory that works whether the team uses Claude Code, Cursor, or both** | Anthropic will never build the Cursor-compatible layer | ✅ **Survives** |

Everything in the roadmap either ships the wedge (review), feeds the moat (memory), or removes friction (MCP). Nothing else gets built.

### The stage-by-stage verdicts you asked for

| Stage / idea | Verdict | Reasoning |
|---|---|---|
| **Planner** | Simplify radically | Full graph suite is overkill for the wedge. Related files + similar code + blast radius is enough. It becomes an MCP tool Claude Code calls, not a manual step. |
| **Architect** | Don't ship as a stage — ship as review rules | The differentiated part of Architect is "check the diff against ADRs/conventions." That's a review feature, not a pipeline stage. |
| **Builder** | Never build | Claude Code is the builder. Wrapping it adds zero value and infinite maintenance. |
| **Reviewer** | **The product** | Ship week 1. |
| **Verifier** | Cut from MVP entirely | Merge-readiness gates are governance. Governance sells to teams of 50, not pilots of 5. Revisit at 20+ users. |
| **MCP** | Week 3 (accelerated) | Cheap to build, existential for habit formation. |
| **A2A** | Never (for now) | You said it yourself: scaling decision, not product decision. There is no second agent to talk to yet. |
| **Token Optimizer as a pitch** | Cut from messaging | Nobody adopts a tool to save tokens. Keep the code internally for context budgeting; never lead with it. |
| **ContextHub** | **Accelerate to Day 1** | See Section 15. This is the company. |

---

## 3. Core Product Hypothesis

> **Startup developers who merge AI-generated code daily will voluntarily run a review step before merging IF (a) it catches at least one real issue per week that they would have missed, (b) its false-positive rate stays below ~30%, and (c) it costs them under 60 seconds of friction.**

Every week of the roadmap tests one clause of this hypothesis. If the hypothesis is false, no amount of features saves the company — better to learn that in week 3 than week 30.

Secondary hypothesis (the moat): *reviews informed by accumulated repo-specific memory will be measurably more trusted than generic reviews — and that difference becomes visible to pilots within 4–6 weeks of accumulation.*

---

## 4. Biggest Risks

Ranked by (probability × damage):

1. **Trust collapse from false positives.** The #1 killer of review tools. One week of noisy findings and pilots stop reading the output forever — they won't tell you, they'll just stop. *Mitigation: launch with conservative, high-precision rules. A review that says "2 real issues" beats one that says "14 maybe-issues." Track FP rate as a first-class metric from day 1.*
2. **The novelty cliff (weeks 2–3).** Pilots try anything once. The habit dies silently when the third copy-paste feels annoying. *Mitigation: MCP by week 3–4, attach to an existing trigger (pre-commit moment), daily async presence.*
3. **Prepare turns out worthless AND you spent weeks on it.** *Mitigation: prepare is a week-2 experiment costing ~2 days (it's a thin wrapper on existing repo-intelligence), instrumented, with a pre-committed kill criterion.*
4. **Pilots are polite, not honest.** Five friendly pilots will say "it's cool" while never using it. *Mitigation: measure behavior (logs), not opinions. Unprompted usage is the only truth.*
5. **Crowded review market** (CodeRabbit, Greptile, Graphite, built-in /code-review). *Mitigation: never compete on generic review. Every finding that cites repo-specific memory ("this violates ADR-015" / "you rejected this pattern on May 3") is the differentiation. If pilots can't tell Ortho's review from a generic one by week 6, that's a No-Go signal.*
6. **Solo-founder burnout.** 8 weeks of build + daily pilot ops is heavy. *Mitigation: the ruthless kill list below exists precisely so the surviving scope fits one person.*

---

## 5. Biggest Opportunities

1. **The verification gap is widening.** Every month, AI generates a larger share of code and developer review capacity stays flat. You're building into a growing pain, not a shrinking one.
2. **Memory compounds while you sleep.** Every pilot session makes the product better for that pilot. This is the only feature with a built-in retention curve that *improves* over time.
3. **Tool-agnosticism.** Teams are mixed (some on Cursor, some on Claude Code). An intelligence layer above the tools is the only thing that serves the whole team. No coding-assistant vendor can credibly build this.
4. **The teammate expansion vector.** When pilot #2 works in the same repo as pilot #1, Ortho already knows the repo's decisions. Time-to-value for user 2 is near zero. That's your organic growth engine — design week 6 around it.
5. **You already have the hard parts built.** Repo-intelligence, ContextHub, arch-intelligence exist. The 8-week plan is mostly *integration and packaging*, not research. That's a genuine unfair advantage on timeline.

---

## 6. What Should Be Removed (never build, for this product)

- **Builder stage / any orchestration of Claude Code** — the developer is the orchestrator.
- **Verifier as a separate stage** — merge readiness = developer reads the review.
- **A2A services** — no demand exists.
- **Confidence percentages** — theater. Findings + severity only.
- **Benchmark suite as a product feature** — keep internally for regression testing; never roadmap-visible.
- **Dashboard generator, HTML reports, web UI** — the terminal and the PR are the UI.
- **Architecture-style detection as a user-facing feature** — pilots do not wake up wanting to know they have a "layered monolith."
- **Five-stage architecture in any user-facing material** — it's your internal design philosophy; users see two commands.

## 7. What Should Be Postponed

- **MCP `prepare` deep integration** → week 4+, only if prepare survives its week-2/3 experiment.
- **Team/shared ContextHub** → week 6 (cohort 2), earliest.
- **Cursor integration** → after Claude Code integration proves the pattern (weeks 8+).
- **Git-hook / CI automation of review** → week 5+, only after trust is established. Auto-running an untrusted reviewer is how you become noise and get uninstalled.
- **Pricing** → after PMF signal. Pilots ride free.
- **Public launch, docs site, marketing** → week 8, gated on the week-7 decision.
- **New languages beyond Python/TS** → post-PMF.

## 8. What Should Be Accelerated

- **`ortho review` v0: week 5 → week 1.** It's mostly wiring existing packages.
- **ContextHub capture: v1.1 → Day 1.** Log every review, finding, and verdict from the first run. Costs ~a day. Pays forever.
- **MCP: v1.1 → week 3.** Existential friction reduction, cheap to build.
- **Memory-cited findings: "someday" → week 4.** The first time Ortho says *"this contradicts the decision you made two weeks ago"* is the product's magic moment. Engineer toward that moment deliberately.
- **The kill decision on Prepare: week 7 → week 3.**

---

## 9. The 8-Week Roadmap

### Week 1 — Ship the Reviewer. Start the Memory.

- **Objective:** A real `ortho review` runs on pilots' real diffs before the week ends. ContextHub silently records everything.
- **Hypothesis:** A high-precision review of an AI-generated diff surfaces at least one issue per pilot per week that they say they'd have missed.
- **Experiment:** Days 1–3: wire `ortho review` — git diff in; findings out (bugs, missing tests, oversized change surface, violations of rules parsed from CLAUDE.md/ADRs if present). Conservative rules only. Days 3–5: two power-user pilots run it on every AI-generated change. Every run + finding + pilot verdict ("real" / "noise") logged to ContextHub.
- **Deliverables:** `ortho review` v0 (markdown output, <60s end-to-end); ContextHub capture layer; #ortho-pilots channel live; written daily-use commitment from all 5 pilots; North Star instrumentation (a log line is enough).
- **Success metric:** ≥6 real reviews run across 2 pilots; ≥1 finding per pilot marked "real catch"; false-positive rate <40% (v0 tolerance).
- **Learning objective:** What class of finding do pilots actually value — bugs? missing tests? convention violations? (This decides week 2 rule priorities.)
- **Exit criteria:** Both pilots ran it unprompted at least once; nobody asked "why would I use this?"

### Week 2 — The Prepare Experiment. Tune for Trust.

- **Objective:** Test Prepare cheaply while making Review trustworthy. Onboard pilots 3–5.
- **Hypothesis (falsifiable, pre-committed):** Pilots given `ortho prepare` will use it voluntarily on ≥50% of AI tasks. **If under 25% by end of week 3, Prepare is cut from the CLI.**
- **Experiment:** Days 1–2: ship minimal `ortho prepare` — related files, similar code, blast radius from existing repo-intelligence; output = one markdown file the pilot points Claude Code at. ~2 days, thin wrapper, no new graphs. Days 2–5: all 5 pilots live; A/B by nature — track prepare-vs-review usage per pilot without pushing either.
- **Deliverables:** `ortho prepare` v0; review rules tuned from week-1 verdicts (kill every rule that produced noise); pilots 3–5 onboarded in <15 min each.
- **Success metric:** Review FP rate <30%; ≥3 pilots active; usage split between prepare/review measured cleanly.
- **Learning objective:** Which command has pull? Is copy-paste friction the complaint (expected) or is output *value* the complaint (much worse)?
- **Exit criteria:** 5 pilots onboarded; FP rate trending down; a defensible read on prepare-vs-review demand.

### Week 3 — Go/No-Go #1: Pick the Wedge. Start MCP.

- **Objective:** Concentrate all firepower on whichever command has pull. Begin killing friction.
- **Hypothesis:** Removing the copy-paste step (MCP inside Claude Code) at least doubles per-pilot usage frequency.
- **Experiment:** Day 1: usage data decides — Review-dominant (predicted), Prepare-dominant (surprise — update the strategy honestly), or genuinely both. Days 2–5: build the thin MCP server exposing the surviving command(s) as tools inside Claude Code; ship to 2 pilots.
- **Deliverables:** A written wedge decision (one paragraph, dated — this is a company decision); MCP server v0 in 2 pilots' Claude Code configs; the losing command deprioritized or cut.
- **Success metric:** ≥3/5 pilots used Ortho ≥3× this week; MCP pilots run review without leaving their session.
- **Learning objective:** Does in-session invocation change *when* pilots review (earlier, more often, smaller diffs)?
- **Go/No-Go #1:** ≥3 pilots at ≥3×/week → proceed. 2 → one more focused iteration week, diagnose honestly. ≤1 → **stop building; spend a full week in pilot conversations; the problem statement is wrong, not the code.**

### Week 4 — The Magic Moment: Memory-Cited Review.

- **Objective:** The first review finding that cites the repo's own accumulated knowledge — visibly.
- **Hypothesis:** A finding that references a repo-specific decision ("violates ADR-015 layer rules"; "you rejected this pattern in review #12") is trusted and acted on at a visibly higher rate than a generic finding.
- **Experiment:** Days 1–3: feed ContextHub's 3 weeks of accumulated verdicts + indexed ADRs/CLAUDE.md into review — findings now carry a *source* ("per your ADR-015…"). Tag memory-cited vs. generic findings in logs. Days 3–5: MCP rollout to all 5 pilots; measure act-on rate per finding type.
- **Deliverables:** Memory-informed review live; per-finding source attribution; all pilots on MCP (CLI still works for holdouts).
- **Success metric:** Act-on rate for memory-cited findings > generic findings; ≥1 pilot spontaneously remarks on Ortho "knowing" their repo.
- **Learning objective:** Is memory-informed review *visibly* better to users — or only theoretically better? (This validates or breaks the moat thesis.)
- **Exit criteria:** Memory citations appearing in real reviews; usage flat or rising vs. week 3; zero pilots churned.

### Week 5 — PMF Measurement Week. Go/No-Go #2.

- **Objective:** Stop building. Measure whether a habit actually exists.
- **Hypothesis:** ≥60% of pilots' AI-generated merges now pass through `ortho review` without any prompting from you.
- **Experiment:** Days 1–2: compute **Review Coverage Rate** per pilot (Ortho reviews ÷ AI-assisted merges — get the denominator by asking pilots to count, or from their git activity). Day 3: the disappointment question, asked 1:1: *"If Ortho disappeared tomorrow, how would you feel — very disappointed / somewhat / not really?"* Days 4–5: ship exactly ONE fix targeting the lowest-coverage pilots' stated blocker. Optionally introduce an opt-in pre-commit hook for the highest-trust pilots (automation only *after* trust).
- **Deliverables:** PMF scorecard (coverage, retention, disappointment, FP rate); one targeted fix shipped; opt-in hook available.
- **Success metric:** Coverage ≥60% average; ≥2/5 "very disappointed"; FP rate <20%.
- **Learning objective:** Is this a habit or a favor to you? Unprompted usage is the only evidence that counts.
- **Go/No-Go #2:** Strong (coverage ≥60%, ≥2 very-disappointed) → weeks 6–8 as planned. Moderate (40–60%) → weeks 6–7 become iteration, delay cohort 2. Weak (<40%, zero very-disappointed) → **hard stop. Do not proceed to launch prep. Either pivot the wedge or wind down with your evidence in hand.**

### Week 6 — Cohort 2: The Teammate Test.

- **Objective:** Prove the memory moat's growth mechanic: a new developer joining a repo Ortho already knows.
- **Hypothesis:** A pilot's *teammate* (same repo) reaches their first "real catch" in <2 days — dramatically faster than cohort 1 — because the memory already exists.
- **Experiment:** Days 1–2: recruit 3–5 cohort-2 devs, prioritizing teammates of existing pilots. Days 2–5: onboard; measure time-to-first-value for same-repo joiners vs. fresh-repo joiners. Watch cohort 1 for churn signals (declining usage, silence in Slack) — 1:1 within 24h of any signal.
- **Deliverables:** Cohort 2 live; onboarding path proven <15 min; same-repo vs. fresh-repo TTFV comparison; cohort-1 churn interventions done.
- **Success metric:** 0% cohort-1 churn; cohort 2 ≥50% weekly-active by Friday; same-repo joiners measurably faster to value.
- **Learning objective:** Does the memory create a network effect within a repo? (If yes — that's the growth strategy AND the fundraising story.)
- **Exit criteria:** 8–10 total devs; the teammate effect measured either way.

### Week 7 — The Honest Decision.

- **Objective:** A binary, evidence-backed call: public beta or another iteration cycle.
- **Hypothesis:** Pilots will *sell* Ortho unprompted — the only pre-launch proxy for word-of-mouth growth.
- **Experiment:** Days 1–2: full scorecard across both cohorts (coverage, retention, FP, disappointment, referral willingness). Day 3: the sell test — ask each pilot to describe Ortho to a colleague in their own words, in writing. If their pitch matches your value prop ("it catches stuff / it knows our repo"), messaging is validated; if their pitches are scattered, positioning isn't ready regardless of usage. Days 4–5: pre-launch fixes or iteration planning, per the decision.
- **Deliverables:** Written go/no-go memo with the data; pilot quotes bank; launch checklist (if Go) or the ONE unlock hypothesis (if No-Go).
- **Success metric:** ≥70% would recommend; ≥6/10 devs weekly-active; decision made without ambiguity or rationalization.
- **Go/No-Go #3 (the founder moment):** If the data is mixed and you feel the pull to rationalize — that IS the answer, and it's No. Extend iteration. A launch of a product pilots merely tolerate burns your one first impression.

### Week 8 — Launch or Loop.

**If Go:**
- **Objective:** Soft public beta that replicates pilot adoption in strangers.
- **Experiment:** README with one sentence + 3 examples (no docs site); GitHub public; hand-invite 10–15 developers outside your network via pilots' referrals; measure whether strangers adopt at pilot-like velocity *without your daily presence* — the true test of self-serve product strength.
- **Success metric:** ≥10 external installs; ≥3 external devs complete a real review in week 1; time-to-first-value <15 min unassisted.
- **Exit:** v1.0 defined by behavior, not features: *a stranger installs Ortho, reviews an AI diff, and comes back tomorrow — without talking to you.*

**If Loop:**
- **Objective:** One precise unlock hypothesis, one 2-week test cycle, one decision date (end of week 10: ship or shelve).
- **Deliverables:** Retro answering exactly one question — was the problem wrong, the solution wrong, or the friction too high? Then test the single change that addresses it. No feature grab-bags.

---

## 10. Product Milestones

| Milestone | Target | Evidence |
|---|---|---|
| **First real catch** | Week 1 | A pilot says "I would have missed that" about a specific finding |
| **First unprompted use** | Week 2 | A review runs with zero nudging from you |
| **Wedge locked** | Week 3 | Written decision, backed by usage data |
| **First memory moment** | Week 4 | A finding cites the repo's own history and the pilot notices |
| **Habit evidence** | Week 5 | ≥60% of AI merges pass through Ortho unprompted |
| **The teammate effect** | Week 6 | Same-repo joiner reaches value in <2 days |
| **Pilots sell it themselves** | Week 7 | Unprompted, accurate pitches to colleagues |
| **Stranger adoption** | Week 8 | An external dev returns on day 2 without hand-holding |

Not one of these says "Planner complete."

---

## 11. North Star Metric

### **Review Coverage Rate = Ortho-reviewed AI changes ÷ total AI-assisted merges (per pilot, per week)**

Why this beats Daily Active Users:

- **DAU measures touch; coverage measures the habit you actually stated as the goal** — "skipping Ortho should feel risky." Coverage is literally the fraction of times they didn't skip.
- **It's fraud-resistant.** A pilot poking the CLI to be nice inflates DAU; only reviewing real merges moves coverage.
- **It has a natural ceiling that means victory.** Coverage → 100% = Ortho is in the critical path of every AI change. That's the vision sentence, quantified.
- **It gives you the denominator for free** — how much AI-generated code your pilots actually merge — which is market-sizing data every investor will ask for.

Trajectory: W1 baseline (whatever it is) → W3 ≥40% → W5 ≥60% (Go gate) → W7 ≥75%.

Guardrail metric (watched, never optimized): **false-positive rate <20%**. Coverage bought with noisy reviews is borrowed, not earned.

---

## 12. Habit Formation Strategy

**Core principle: don't create a new habit — attach to an existing trigger.** Developers already have a moment of hesitation before committing/PR-ing AI-generated code. That hesitation IS the trigger. `ortho review` gives it an action. (This is the deep reason Review beats Prepare as a wedge: "before starting a task" has no existing trigger; "before merging something I don't fully trust" does.)

**The friction removal ladder** — each rung unlocked only after the previous one earns trust:

1. **Weeks 1–2 — Manual command.** Deliberate, conscious use. Intentional friction is fine here: it makes usage a real signal of demand.
2. **Weeks 3–4 — MCP in-session.** Review without leaving Claude Code. The habit's cost drops to near zero.
3. **Week 5+ — Opt-in pre-commit hook.** Ortho suggests itself at the trigger moment. Only for pilots whose trust is established (they act on ≥50% of findings).
4. **Post-PMF — CI / PR-comment mode.** Fully ambient. Introduced last, because automation of an untrusted reviewer is noise, and noise gets uninstalled.

**The reward loop:** every review ends with a one-line receipt — *"2 issues, 1 missing test — 40 seconds."* Visible value, every run. And the compounding reward: memory-cited findings make week 6's reviews visibly smarter than week 1's, which is the anti-novelty-cliff mechanic no static tool has.

**Abandonment defense:** the moment a pilot's coverage drops two weeks running, a 1:1 happens within 24 hours. Churn at n=5 is not a metric; it's an emergency.

---

## 13. Pilot Feedback Strategy

- **Behavior over opinions.** Logs first, words second. A pilot who praises Ortho but hasn't run it in 5 days is churned.
- **Daily async, weekly deep.** One-line Slack check-ins daily ("did Ortho run today? any noise?"); optional 30-min call Fridays. Never make pilots schedule meetings to use a tool.
- **Verdict capture is product, not research.** Every finding gets a one-keystroke verdict (real / noise) — this doubles as ContextHub training data. Feedback collection literally builds the moat.
- **The two questions that matter, asked at weeks 5 and 7:** "If Ortho vanished tomorrow, how disappointed?" and "Describe Ortho to a colleague in your own words."
- **Feature-request quarantine:** everything goes to a public backlog with "after week 8" stamped on it. In weeks 1–7 you say no to everything except the wedge. Pilots respect focus; they churn on bloat too.

---

## 14. Product-Market Fit Framework

Four signals, evaluated at weeks 5 and 7:

| Signal | Measure | PMF threshold |
|---|---|---|
| **Habit** | Review Coverage Rate | ≥60% (W5) → ≥75% (W7) |
| **Dependence** | "Very disappointed" if gone | ≥40% of pilots |
| **Trust** | Act-on rate for findings; FP rate | ≥50% acted on; FP <20% |
| **Pull** | Unprompted referrals / teammate invites | ≥2 by W7 |

Interpretation discipline: **any single strong signal can be politeness; three of four is PMF.** And one hard rule: if you catch yourself explaining away a missed threshold ("they were busy that week"), the threshold was missed. Write the miss down and act on it.

---

## 15. Competitive Moat Evolution — ContextHub Is the Company

You asked whether ContextHub should come earlier. **Yes — earlier than you proposed, and in a different role than you imagined.**

The mistake in the original plan was treating ContextHub as a *feature to schedule*. It's not a feature. It's the accumulation layer, and accumulation has only one requirement: **be running while usage happens.** Every week ContextHub isn't capturing is moat you can never recover — you can rebuild code, you cannot rebuild three months of review verdicts.

**The moat compounds in four phases:**

1. **Weeks 1–4 — Capture (silent).** Every review, finding, verdict, and indexed ADR lands in ContextHub. Zero user-facing surface. Cost: ~1 day of engineering.
2. **Weeks 4–8 — Cite (visible).** Reviews reference the memory ("per ADR-015"; "you rejected this pattern before"). This is when the moat becomes *felt* — Ortho reviews get smarter while every competitor's stay static.
3. **Months 3–6 — Share (team memory).** One repo's memory serves every developer in it. New teammate onboards into accumulated judgment. Switching cost becomes: "leave Ortho, lose everything it learned about us."
4. **Months 6–12 — Span (organizational memory).** Across repos, across tools (Cursor AND Claude Code), across time. At this point "which coding assistant should we use?" and "should we drop Ortho?" become unrelated questions — which is exactly the strategic position you described: *the coding model is replaceable; the intelligence is not.*

The honest caveat: repository intelligence (graphs, symbols) is genuinely copyable — assume Anthropic and Cursor will have equivalents. Verdict-and-decision memory earned through daily use is not copyable, because it requires having been there. That's why the roadmap ships the wedge to *generate* usage and captures memory to *keep* it.

---

## 16. Long-Term Product Vision

- **Year 0 (this roadmap):** the reviewer that knows your repo. Two commands, one memory, five→fifteen devout users.
- **Year 1:** the team's engineering memory. Shared ContextHub per repo; PR-native review; Cursor + Claude Code both supported; the teammate effect as the growth loop. Pricing lands here (per-seat, team plan) — the memory is what's worth paying for.
- **Year 2:** the intelligence layer of AI-assisted engineering. Prepare returns — not as a manual command, but as MCP tools any coding agent calls to ask "what should I know before touching this code?" The five-stage vision realized in its honest form: not a pipeline you run, but a memory every AI tool consults before writing and every merge consults before shipping.

The through-line: **you are not building a better session. You are building the thing that persists between sessions.**

---

## 17. Final Founder Verdict

### 1. If I were CEO of Ortho, would I follow this roadmap exactly?

**Weeks 1–5: yes, to the letter** — including the pre-committed kill criteria, which are the part most founders quietly delete. **Weeks 6–8: as written intent, not scripture.** If week 3's data surprises us (say, Prepare shows shocking pull), weeks 4–8 get rewritten around the surprise — and that would be the roadmap *working*, not failing. A pilot roadmap's job is to make the decision gates unavoidable, not to predict the future.

### 2. If not, what would I change?

Two places I'd push even harder than this document does:

- **I'd consider cutting Prepare from week 1 entirely** and shipping Review alone, adding Prepare in week 2 only if pilots *ask* for pre-generation help. I kept the week-2 experiment because it costs two days against infrastructure you already own — but if week 1 runs hot, skip it and let demand pull it in.
- **I'd pressure-test the pilot bench in week 1, not week 6.** Five pilots is a thin margin; one ghost and your data wobbles. Line up 2–3 backup pilots now, before you need them.

And one thing I'd resist changing even under pressure: the FP-rate guardrail. Every review tool that died, died of noise. When a pilot asks for "more thorough" review in week 3, the answer is no until precision is proven.

### 3. One shot at making Ortho indispensable — what do I build first?

**`ortho review` that cites the repository's own engineering decisions.**

Not review — memory-cited review. The moment a developer sees *"⚠ this reintroduces the pattern you rejected in ADR-015, and similar code in auth/middleware.py handles it differently"* — that's the moment Ortho stops being a tool and becomes a colleague who's been on the team longer than they have. No coding assistant can say that sentence, because no coding assistant was there when the decision was made.

Ortho was. That's the company.

Everything else — Prepare, MCP, Verifier, five stages, A2A — is distribution and packaging for that one sentence.
