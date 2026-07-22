# X/Twitter Content Plan — 2 Weeks from Zero Followers

## The reality at 0 followers

Broadcasting to 0 followers doesn't work. The strategy that works:
1. **Replies** — get into existing conversations (your replies show up in the thread, which has an audience)
2. **Demo content** — the GIF/video does the work, not the follower count
3. **#buildinpublic** — this community actively engages with new builders
4. **Relevant hashtags** — #devtools, #python, #aidev surface to people searching

A single good reply on a thread with 500 likes can get you 50+ profile visits. That's how you build from zero.

---

## Week 1 — Launch & Engage

### Day 1 (today) — The launch thread

Post this as a thread (reply to your own tweets to chain them):

**Tweet 1/6:**
```
I've been shipping a lot of AI-generated code.

The problem: AI tools have no idea what my architecture is.

They write code that looks right but violates layer boundaries, introduces cycles, or couples things that shouldn't be coupled.

So I built Ortho to catch it before it merges. 🧵
```

**Tweet 2/6:**
```
Here's what it looks like in practice:

[attach ortho_demo.gif here]

ortho guardrails scans your repo, builds a real architecture model, and shows you exactly what the AI got wrong — with the actual line of evidence, not just "violation detected".
```

**Tweet 3/6:**
```
The part I find most useful: the feedback loop.

When you reject a finding:
→ ortho feedback reject "services/order.py bloat" --reason "tracked in #4821"

Next scan:
→ "Rejected 2026-07-15: tracked in #4821"

The AI stops suggesting changes to things you've already decided.
```

**Tweet 4/6:**
```
It's fully local-first.

Your source never goes to a third-party server.
Zero telemetry. One SQLite file in your repo root.

For teams under SOC2, HIPAA, or any IP restriction — this means you can actually use it where cloud tools are off the table.
```

**Tweet 5/6:**
```
Works as:
• CLI (ortho guardrails, ortho decide, ortho plan, ortho refactor)
• MCP server — Claude can call it directly during a coding session

Currently Python primary, TypeScript secondary.

Install in one command:
Windows: irm https://adithyak3106.github.io/Ortho-community/install.ps1 | iex
Mac/Linux: git clone https://github.com/AdithyaK3106/Ortho.git && cd Ortho && ./install.sh
```

**Tweet 6/6:**
```
Building this in public.

If you're shipping AI-generated code and hitting architecture problems, I'd love to hear what you're dealing with.

GitHub: https://github.com/AdithyaK3106/Ortho

#buildinpublic #devtools #python #aidev
```

---

### Day 2–3 — Reply to relevant threads

Search X for these and reply to any tweets with 50+ likes:

**Search terms:**
- "Copilot architecture"
- "Claude Code violated"
- "AI generated code review"
- "AI coding tool breaks"
- "code review AI"
- "local LLM code review"
- "CodeRabbit alternative"
- "AI code quality"

**Reply formula:** Add genuine value first, then mention Ortho only if directly relevant.

Example reply to someone complaining about AI-generated code quality:
```
Same problem. The AI doesn't know your layer boundaries exist.

We built something for this — scans locally, shows the actual violation with the line of evidence. Happy to share if useful: github.com/AdithyaK3106/Ortho
```

---

### Day 4 — Build-in-public update

```
Week 1 building Ortho in public:

✓ Shipped the GitHub README with a real terminal demo
✓ First installs from people I've never met (hopefully!)
✓ Working on: [whatever you're actually working on]

Honest question for devs shipping AI code: do you catch architecture violations before or after they merge?

#buildinpublic #devtools
```

---

### Day 5 — Technical content thread

This kind of content gets shared by developers because it's genuinely useful.

**Tweet 1/4:**
```
How do you detect architecture violations in a Python repo programmatically?

(Thread on what we learned building Ortho's layer detection 🧵)
```

**Tweet 2/4:**
```
Naive approach: lint for import patterns.

Problem: import linting is file-level. It can tell you "this module imports from that module" but not "this import crosses a layer boundary that your architecture defines."

You need a cross-file model.
```

**Tweet 3/4:**
```
What we actually do:

1. Parse every file with tree-sitter → extract all import edges
2. Build a directed graph of the whole codebase
3. Run topological sort → implicit layer ordering emerges from the graph
4. Flag edges that go "upward" in the layer order

No config files. No manual layer definitions.
```

**Tweet 4/4:**
```
The hard part: confidence.

Same import graph, different repos → different layer interpretations.

We added vocabulary scoring (dir names like "api/", "db/", "services/") and framework fingerprinting as extra signals.

Result: 92% accuracy on 9 real repos.

Code: github.com/AdithyaK3106/Ortho
```

---

## Week 2 — Double down on what worked

### Day 8 — Engagement recap

```
Ortho update — week 2:

[actual numbers: GitHub stars, installs, comments, whatever you have]

Most common question so far: [answer it here]

What I'm fixing next: [be specific]

#buildinpublic
```

### Day 9 — The "why local-first" take

```
Hot take: sending your source code to a third-party AI reviewer is a bigger risk than the bugs it catches.

For most companies under SOC2 or with any IP sensitivity, tools like CodeRabbit and Greptile are off the table before you even compare features.

"Local-first" isn't a nice-to-have. For a lot of teams it's the only option.

Ortho runs entirely on your machine: github.com/AdithyaK3106/Ortho
```

### Day 10 — Show a real decision

```
Here's a real ortho decide output:

[screenshot of `ortho decide "add Redis caching to the API layer"` from your terminal]

This is why I built the decision support feature — not just "here are your violations" but "here's what will break if you do X and here's the safer path."
```

### Day 11 — Reply day

Spend 30 minutes replying to threads (not posting). This is often more effective than original content at 0 followers.

Search: "architecture review", "code quality AI", "#buildinpublic devtools"

### Day 12 — Feedback loop demo

```
The feature I'm most proud of in Ortho:

When you reject a finding → it remembers why.

[show before/after screenshots:
Before: "✗ Layer boundary violation: services/order.py"
After:  "⊘ Rejected 2026-07-15: legacy code, tracked in #4821, not touching it"]

The AI stops suggesting the same thing you already said no to.
```

### Day 14 — End of week 2 update

```
2 weeks of building Ortho in public. Honest update:

What worked: [be specific]
What didn't: [be honest]
What surprised me: [genuine insight]

Next: [real next step]

#buildinpublic
```

---

## Accounts to follow and engage with (they reply to builders)

- @swyx — builds in public, huge DevRel audience
- @levelsio — #buildinpublic OG, engages with indie builders
- @t3dotgg — TypeScript/dev tools audience
- @Austen — posts about AI devtools regularly
- @simonw — Simon Willison, Python + AI tools, replies to technical content
- @GergelyOrosz — The Pragmatic Engineer, posts about AI coding tools

**Strategy:** reply to their threads with genuine insights. Don't pitch Ortho. Build the relationship first.

---

## What NOT to do

- Don't quote-tweet your own stuff (looks desperate at 0 followers)
- Don't use more than 2-3 hashtags (looks spammy)
- Don't reply to every thread with a link to Ortho (gets you muted)
- Don't post more than once/day in the first week
- Don't delete tweets that get no engagement — just keep going
