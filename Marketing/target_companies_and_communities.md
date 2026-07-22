# Target Companies & Developer Communities

**Purpose:** Day 1-4 research. Use this to build the 50-company outreach list and identify where to post in Week 2.
**Last Updated:** 2026-07-21

---

## PART 1: TARGET COMPANY CRITERIA & SCORING

### Qualification Criteria (must have ALL of these)

| Criterion | How to Check |
|---|---|
| 30–300 engineers | LinkedIn company page → employee count filter, or Glassdoor |
| Python/TypeScript primary stack | GitHub org page, job postings, tech blog, StackShare |
| Actively shipping AI-generated code | Job posts mentioning "Claude Code", "Copilot", "Cursor", "AI coding", "LLM"; engineering blog posts; LinkedIn posts from engineers |
| Architecture worth protecting | Non-trivial product (not a 3-file script); layered or modular structure implied by role descriptions (Staff Eng, Principal Eng, Architect titles exist) |

### Disqualification Criteria (exclude if ANY apply)

| Criterion | Reason |
|---|---|
| Pure Go/Java/Ruby/Rust shop (no Python) | Ortho Python-primary; don't waste a conversation on a language gap |
| <20 engineers | No budget, no architecture problem yet |
| Consumer app with no enterprise/compliance angle | Harder sell; deprioritize |
| Already publicly using CodeRabbit or Greptile | They've already solved the problem (or think they have); harder to displace |

### Bonus Signal (increases priority)

| Signal | Score |
|---|---|
| SOC2 Type II or HIPAA mentioned on website | +3 |
| Job posting explicitly mentions "AI code review" or "AI-generated code quality" | +3 |
| Engineering blog post about AI coding challenges | +2 |
| CTO/VP Eng active on LinkedIn (posts regularly) | +2 |
| Open source Python repos with real architecture (not toy projects) | +1 |
| Uses Claude Code or mentions Anthropic in tech stack | +2 |

**Priority threshold:** Score ≥ 3 = top-priority outreach (do first 25). Score 1-2 = second wave (days 4-5).

---

## PART 2: WHERE TO FIND TARGETS

### LinkedIn Search Strings

```
(1) FinTech targets:
Title: "VP Engineering" OR "CTO" OR "Head of Engineering"
Industry: "Financial Services" OR "Insurance"
Company size: 51-200 employees
Keywords: "Python" OR "AI" OR "Copilot" OR "Claude"

(2) HealthTech targets:
Title: "VP Engineering" OR "CTO" OR "Engineering Manager"
Industry: "Hospital & Health Care" OR "Health, Wellness & Fitness" OR "Medical Devices"
Company size: 51-500 employees

(3) B2B SaaS targets:
Title: "VP Engineering" OR "CTO" OR "Staff Engineer" OR "Principal Engineer"
Industry: "Computer Software" OR "Information Technology and Services"
Company size: 51-200 employees
Keywords: "Claude Code" OR "GitHub Copilot" OR "Cursor" OR "AI coding"
```

### Other Sources

- **Y Combinator portfolio (ycombinator.com/companies):** Filter by "B2B", "Enterprise", active batches. Many 30-200 person companies with Python stacks, SOC2 pursuits.
- **Crunchbase:** Filter by funding stage (Series A/B = right size), industry, location.
- **AngelList / Wellfound:** Jobs mentioning AI coding tools.
- **GitHub:** Search for companies with Python orgs, active engineering teams, real architecture.
- **BuiltWith / StackShare:** Find Python + AI tooling signal.

---

## PART 3: COMPANY LIST TEMPLATE

Copy into a spreadsheet. Target: 50 companies, prioritized by score.

| # | Company | Website | Size (est.) | Stack | Compliance Signal | AI Tool Signal | Priority Score | Decision Maker | LinkedIn URL | Notes |
|---|---------|---------|-------------|-------|------------------|----------------|----------------|---------------|-------------|-------|
| 1 | | | | | | | | | | |
| 2 | | | | | | | | | | |
| ... | | | | | | | | | | |

---

## PART 4: DEVELOPER COMMUNITIES

These are the 5 communities to target in Week 2 (Days 10-14). Researched for best-fit channels.

---

### Community 1: Hacker News

**URL:** https://news.ycombinator.com
**Post format:** Show HN (Week 2, Day 8 — see `show_hn_post.md`)
**Why:** Highest density of technically sophisticated readers who make tooling decisions. A good Show HN stays visible for 24-48 hours and drives long-tail inbound for weeks.
**How to engage:** Post at 9am ET Monday. Respond to every comment within 2 hours. Be honest about limitations — HN rewards intellectual honesty, punishes marketing-speak.
**Subreddits/channels:** N/A — it's a single feed.
**Expected reach:** 500–5,000 views for a mid-tier Show HN.

---

### Community 2: The Pragmatic Engineer Community (Slack)

**URL:** https://pragmaticengineer.com (Slack invite via newsletter)
**Post target channel:** #tools, #ai-engineering, or equivalent
**Why:** Gergely Orosz's community is dense with senior engineers and EMs at exactly the right company sizes. Members are tool-evaluators, not just readers.
**Message framing:** Problem-first. "Has anyone solved the AI-code-violates-architecture problem? We built something local-first — happy to share." Not a pitch.
**Note:** Join the community first (Week 1 Day 4), participate in unrelated threads before posting about Ortho. Don't spam.

---

### Community 3: Software Architecture Slack (or equivalent)

**Options:**
- **Software Architecture Slack** — search for invite links on Twitter/X or Google "software architecture slack community"
- **Dev.to community** — https://dev.to — post an article version of the Show HN
- **Architecture Notes community** — follow/engage on Substack, then reach out to readers

**Post target channel:** #tools, #architecture-review, #ai
**Why:** Self-selecting audience of engineers who care about architecture — exactly the people who will feel Ortho's pain.
**Message framing:** "We built a tool that validates AI-generated code against your actual architecture model. Looking for teams to try it. Here's what it found on flask."

---

### Community 4: r/ExperiencedDevs (Reddit)

**URL:** https://reddit.com/r/ExperiencedDevs
**Post format:** Text post, problem-first
**Why:** 180k+ experienced engineers. Skeptical but fair — if it's genuinely useful, they'll upvote and comment. Not a place for marketing.
**Post title options:**
- "What does your team do when AI-generated code violates your architecture?"
- "We scanned 9 open-source Python repos for architecture violations introduced by AI — here's what we found"
**Rules check:** r/ExperiencedDevs allows tool sharing if it's genuine and not spam. Frame as "we built this to solve our own problem" — not a product pitch.
**Best time to post:** Tuesday–Thursday, 10am–2pm EST.

---

### Community 5: r/devops + r/programming

**URL:** https://reddit.com/r/devops | https://reddit.com/r/programming
**Post format:** Same as r/ExperiencedDevs — data/problem first
**Why:** r/devops for the "this breaks our CI/CD pipeline" angle; r/programming for general dev audience.
**Caution:** r/programming has stricter self-promotion rules. Frame as sharing findings, not pitching a product. Link to a GitHub repo or write-up, not a sales page.

**Backup communities (if above don't gain traction):**
- **dev.to** — publish a technical post about the scanning methodology
- **Indie Hackers** — good for founder-to-founder outreach
- **Engineering Discord servers** — search for active ones via disboard.org
- **Local engineering meetups** — Meetup.com, Eventbrite for in-person events

---

## PART 5: WEEK 1 OUTREACH CHECKLIST

**Day 1:**
- [ ] Export target criteria into spreadsheet (use template above)
- [ ] Identify first 10 companies manually using LinkedIn search
- [ ] Send 10 connection requests (personalized notes, Variant A/B/C based on industry)

**Day 2:**
- [ ] Find 10 more companies
- [ ] Send 10 more connection requests
- [ ] Join The Pragmatic Engineer Slack (if not already)

**Day 3:**
- [ ] Find 10 more companies
- [ ] Send 10 more connection requests
- [ ] Participate in 1-2 non-Ortho threads in Pragmatic Engineer Slack

**Day 4:**
- [ ] Find 10 more companies
- [ ] Send 10 more connection requests
- [ ] Research and join 1-2 more communities from the list above

**Day 5-7:**
- [ ] Final 10 companies identified (50 total)
- [ ] Send remaining 10 connection requests
- [ ] Begin sending Message 1 to Week 1 connections that accepted
