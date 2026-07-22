# LinkedIn Outreach Sequences — Ortho Pilot Recruitment

## INSTALL LINKS (include in messages when relevant)

**Windows:**
```
irm https://adithyak3106.github.io/Ortho-community/install.ps1 | iex
```
**macOS / Linux:**
```
git clone https://github.com/AdithyaK3106/Ortho.git && cd Ortho && ./install.sh
```
**GitHub:** https://github.com/AdithyaK3106/Ortho

---

**Goal:** 5 pilot companies in 30 days
**Target:** Engineering leads (VP Eng, CTO, Staff/Principal Eng) at 30–300 person companies
**Sending cadence:** Connection request → Wait 2-3 days → Message 1 → Wait 5 days → Follow-up

---

## HOW TO FIND TARGETS

Search on LinkedIn:
- Title: "VP Engineering" OR "CTO" OR "Head of Engineering" OR "Staff Engineer" OR "Principal Engineer"
- Company size: 51–500 employees
- Industry: Software, Financial Services, Healthcare Technology, Insurance Technology
- Recent activity signals to look for:
  - Job postings mentioning "Claude Code", "Copilot", "Cursor", "AI coding"
  - Company blog posts about AI adoption
  - Personal posts about AI-generated code, code quality, architecture
  - SOC2 Type II / HIPAA mentioned on company website

**Daily target:** 10 connection requests/day for 5 days = 50 total by end of Week 1

---

## VARIANT A: FINTECH / INSURTECH

*Use for: Companies in payments, lending, insurance, banking technology*
*Compliance signal: SOC2 Type II, PCI-DSS, state insurance regulations*

### Connection Request Note (≤300 chars)
```
Hi [Name] — saw [Company] is investing in AI coding tools. Building Ortho,
a local-first architecture reviewer for AI-generated code (source never
leaves your machine). Thought it might be relevant given FinTech compliance
constraints. Happy to share more if useful.
```

### Message 1 (send 2-3 days after connection accepted)
Subject: AI-generated code + FinTech compliance

```
Hi [Name],

Quick context on why I reached out: Ortho scans a Python repo and catches
architecture violations in AI-generated code — layer boundary violations,
circular dependencies, coupling issues — with real evidence, not just
heuristics.

The reason I thought of [Company] specifically: most code review tools
(CodeRabbit, Greptile, Qodo) are cloud-based, which means your source
goes to their servers. For a FinTech under SOC2 or PCI-DSS scope, that's
often a non-starter before any feature comparison.

Ortho is entirely local. The only file it writes is `.ortho/ortho.db` in
your repo root. No network calls during scan. No account. No API key.

I'm looking for 5 engineering teams to run it on a real internal repo for
30 days and give honest feedback. In exchange: free access, personal
onboarding call, direct line to me for any issues.

Would it be worth a 20-minute call to see if it's a fit for [Company]?

— Adithya
urbrain369@gmail.com
```

### Follow-up (send 5 days after Message 1, no reply)
```
Hi [Name] — following up in case this got buried.

If AI-generated code violating your architecture is already a felt pain,
Ortho's probably worth 20 minutes. If it's not yet a problem, totally
understand — probably too early.

Either way, happy to share what we've found scanning flask, requests, and
click if that's useful context. Just reply and I'll send it over.

— Adithya
```

---

## VARIANT B: HEALTHTECH / MEDTECH

*Use for: EHR, health data, medical devices software, telehealth*
*Compliance signal: HIPAA, HITRUST, FDA 21 CFR Part 11*

### Connection Request Note (≤300 chars)
```
Hi [Name] — noticed [Company] is shipping AI-assisted code. Building Ortho,
a local-first architecture reviewer — source never leaves your machine,
which matters for HIPAA scope. Would love to share what we've built if
relevant to your team.
```

### Message 1 (send 2-3 days after connection accepted)
```
Hi [Name],

I'm building Ortho — it scans a Python codebase, builds a real architecture
model (call graph, import graph, layer detection), and finds violations in
AI-generated code before they merge. Every finding cites the actual
import edge or cycle chain, not just a pattern match.

For HealthTech teams: the reason I'm reaching out specifically is that
every major AI code review tool right now sends your source to a
third-party cloud. Under HIPAA, even if your repo doesn't contain PHI
directly, the audit trail concern is real. Ortho doesn't do that. It
runs on your machine, writes one SQLite file locally, and nothing leaves.

Also useful: Ortho has a memory layer. When your team rejects a finding
("this is intentional, it's a known tradeoff"), it stores that decision.
Next scan, instead of repeating the same alert, it says "Rejected
2026-07-10: [your reason]." The AI coding tool doesn't have to re-learn
your constraints every session.

I'm looking for 5 engineering teams for a 30-day pilot. No cost. I do
a 30-minute onboarding call with you, you run it on a real repo, you
tell me what's wrong.

Is [Company] the right fit? Happy to jump on a quick call.

— Adithya
urbrain369@gmail.com
```

### Follow-up (send 5 days after Message 1, no reply)
```
Hi [Name] — just a quick follow-up.

If AI code quality and local-first compliance is already on your radar,
I'd love to show you what Ortho does on a 20-minute call.

If the timing's off, no worries at all — I'll check back in when we
launch publicly.

— Adithya
```

---

## VARIANT C: B2B SAAS (no hard compliance requirement, but IP-sensitive)

*Use for: Developer tools, data platforms, infrastructure SaaS, enterprise software*
*Signal: Engineering blog posts about architecture, job posts mentioning Claude Code/Copilot*

### Connection Request Note (≤300 chars)
```
Hi [Name] — [Company]'s engineering posts on AI adoption caught my eye.
Building Ortho, a local-first tool that catches architecture violations in
AI-generated code before they merge. Thought it might be worth a quick
conversation given where your team is headed.
```

### Message 1 (send 2-3 days after connection accepted)
```
Hi [Name],

I'm building Ortho — it scans a Python repo and catches architecture
violations that AI coding tools introduce: layer boundary crossings,
circular dependencies, bloat hotspots. Every finding comes with real
evidence — the actual import edge, the cycle chain, the line counts —
so your team can verify it's real before acting on it.

The thing that differentiates it from CodeRabbit or similar: Ortho is
entirely local. No source leaves your machine. For teams that care about
IP (which is most SaaS companies, honestly) and don't want a third-party
vendor ingesting their codebase, that matters.

There's also a feedback loop: when you reject a finding, Ortho stores
why. Next scan, instead of repeating the same alert, it tells the AI
"we rejected this pattern on [date] for [reason]." The AI stops
suggesting what you've already said no to.

I'm looking for 5 engineering teams to pilot this over 30 days — free
access, onboarding call, direct feedback loop with me. What I ask in
return: run it on a real repo and tell me honestly what's wrong.

Worth a 20-minute call to see if it fits [Company]?

— Adithya
urbrain369@gmail.com
```

### Follow-up (send 5 days after Message 1, no reply)
```
Hi [Name] — following up quickly.

If AI-generated code violating your architecture is a real problem at
[Company], Ortho's probably worth 20 minutes of your time. If you're not
shipping enough AI-assisted code yet for it to matter, probably too early.

Happy to send you a scan of a well-known Python repo (flask, requests,
click) so you can see what the output looks like before committing to a call.

— Adithya
```

---

## TRACKING SHEET

Use this to track outreach. Copy into a spreadsheet.

| Name | Company | Industry | Variant | Connection Sent | Accepted | Msg 1 Sent | Reply | Follow-up Sent | Status |
|------|---------|----------|---------|----------------|----------|------------|-------|----------------|--------|
| | | | | | | | | | |

Status options: `Sent` → `Connected` → `Replied` → `Call Booked` → `Pilot` → `No` → `Later`

---

## NOTES

- **Personalize the connection note every time** — mention one specific thing about their company or post. Generic connection requests get ignored.
- **Don't pitch in the connection request** — just establish relevance. The pitch is Message 1.
- **50 chars matters on mobile** — the first ~50 chars of your message is all they see in the notification. Lead with the most compelling line.
- **Reply speed matters** — if someone replies, respond within 2 hours. Speed signals you're real, not a bot.
- **Track everything** — even a "not now" is useful data for retargeting in 60 days.
