'use client'

import { motion } from 'framer-motion'
import { useRef } from 'react'

/**
 * ORTHO LANDING PAGE — EXACT VISUAL REPRODUCTION
 *
 * Faithfully recreates the design language from screenshots:
 * - Editorial serif headlines (huge, left-aligned)
 * - Monospace labels and terminal output
 * - Thin borders, minimal decoration
 * - Large asymmetrical whitespace
 * - Dark background with warm amber accents
 * - Terminal green for success states
 * - Grid-based composition with architectural precision
 */

function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-black border-b border-amber-900/20">
      <div className="max-w-full px-8 py-4 flex justify-between items-center">
        <div className="flex gap-4 items-center">
          <span className="text-amber-600 text-sm">◆</span>
          <a href="/" className="text-white font-serif text-sm tracking-tight">
            ortho.
          </a>
        </div>

        <div className="flex gap-8 items-center text-xs tracking-widest uppercase text-gray-500 hover:text-gray-300">
          <a href="#" className="hover:text-amber-600">Problem</a>
          <a href="#" className="hover:text-amber-600">Architecture</a>
          <a href="#" className="hover:text-amber-600">Pillars</a>
          <a href="#" className="hover:text-amber-600">ASES</a>
          <a href="#" className="hover:text-amber-600">CLI</a>
          <a href="#" className="hover:text-amber-600">Roadmap</a>
        </div>

        <div className="flex gap-3 items-center">
          <a href="https://github.com/urbra/ortho" target="_blank" className="text-gray-400 hover:text-white text-xs">GitHub</a>
          <button className="bg-amber-500 text-black px-4 py-1.5 text-xs font-bold hover:bg-amber-400">
            JOIN BETA →
          </button>
        </div>
      </div>
    </nav>
  )
}

function HeroSection() {
  return (
    <section className="bg-black pt-20 pb-32 px-8 border-b border-amber-900/20">
      <div className="max-w-7xl mx-auto grid grid-cols-2 gap-20">
        {/* Left column */}
        <div>
          <div className="text-amber-600 text-xs mb-12 tracking-widest uppercase">
            § Phase 3 Complete • 252 / 70 / 42 Tests
          </div>

          <h1 className="text-7xl font-serif leading-none mb-8 text-white">
            Scan first.
            <br />
            <span className="text-amber-500">Ask once.</span>
            <br />
            Ship confident.
          </h1>

          <p className="text-sm text-gray-400 leading-relaxed mb-12 max-w-sm">
            Ortho is an AI engineering platform. It reads your repository, understands your architecture, and assembles precise context—so the LLM works with evidence, not guesses.
          </p>

          <div className="flex gap-4 mb-8">
            <button className="border border-amber-600 bg-amber-600 text-black px-6 py-2 text-xs font-bold tracking-wider uppercase hover:bg-amber-500">
              JOIN THE BETA →
            </button>
            <button className="border border-gray-600 text-gray-300 px-6 py-2 text-xs font-bold tracking-wider uppercase hover:border-amber-600 hover:text-amber-600">
              SEE THE ARCHITECTURE
            </button>
          </div>

          <div className="space-y-2 text-xs text-gray-500 tracking-widest">
            <div>▪ REAL-FIRST • SOLICIT</div>
            <div>▪ MODEL-AGNOSTIC</div>
          </div>
        </div>

        {/* Right column - Terminal */}
        <div className="bg-black/60 border border-gray-800 p-4 font-mono text-xs">
          <div className="text-gray-600 mb-4">
            ORTHO · SCAN              ORTHO ANALY...     ORTHO CONTEN...
          </div>

          <div className="space-y-2">
            <div className="text-amber-600">▸ ortho> scan</div>
            <div className="text-gray-600 ml-6">→ detecting languages...</div>
            <div className="text-gray-600 ml-6">→ parsing 2,244 files via tree-sitter</div>
            <div className="text-gray-600 ml-6">→ 5,124 symbols extracted</div>
            <div className="text-green-500 ml-6">✓ 2,312 imports resolved</div>
            <div className="text-green-500 ml-6">✓ 1,684 call-graph edges built</div>
            <div className="text-gray-600 ml-6">storage → .ortho/ortho.db (42.2 MB)</div>
            <div className="text-gray-600 ml-6">sectors → .ortho/vectors.db (12.7 MB)</div>
            <div className="text-green-500 ml-6">scan complete in 4.31s</div>
          </div>
        </div>
      </div>

      {/* Metrics row */}
      <div className="max-w-7xl mx-auto mt-16 grid grid-cols-4 gap-px border border-amber-900/20 divide-x divide-amber-900/20">
        <div className="border-l border-amber-900/20 p-6">
          <div className="text-3xl font-serif text-white">12,847</div>
          <div className="text-xs text-gray-500 mt-2">SYMBOLS / PKG</div>
        </div>
        <div className="p-6">
          <div className="text-3xl font-serif text-white">4.31S</div>
          <div className="text-xs text-gray-500 mt-2">SCAN TIME</div>
        </div>
        <div className="p-6">
          <div className="text-3xl font-serif text-white">≈ 20%</div>
          <div className="text-xs text-gray-500 mt-2">TECH-DEBT</div>
        </div>
        <div className="p-6">
          <div className="text-3xl font-serif text-white">6</div>
          <div className="text-xs text-gray-500 mt-2">QUALITY GATES</div>
        </div>
      </div>
    </section>
  )
}

function ProblemSection() {
  return (
    <section className="bg-black pt-32 pb-32 px-8 border-b border-amber-900/20">
      <div className="max-w-7xl mx-auto grid grid-cols-2 gap-20">
        {/* Left */}
        <div>
          <div className="text-amber-600 text-xs mb-8 tracking-widest uppercase">
            § 01 — The Problem
          </div>

          <h2 className="text-5xl font-serif leading-tight mb-6 text-white">
            AI-assisted development
            <br />
            <em className="italic text-amber-500">is a broken loop.</em>
          </h2>

          <p className="text-sm text-gray-400 leading-relaxed">
            Four failure modes appear in every team. Ortho addresses each one at the source—before the LLM is called, not after.
          </p>
        </div>

        {/* Right - Problem cards */}
        <div className="space-y-8">
          <div className="border-l-2 border-amber-900/50 pl-6">
            <h3 className="text-amber-600 text-xs mb-2 tracking-widest uppercase font-bold">Failure</h3>
            <h4 className="text-white font-serif text-lg mb-2">Poor Context</h4>
            <p className="text-gray-500 text-sm">Engineers hand-summarize code into an LLM prompt. Summaries are lossy. The model generates code that conflicts with existing patterns.</p>
          </div>

          <div className="border-l-2 border-amber-900/50 pl-6">
            <h3 className="text-amber-600 text-xs mb-2 tracking-widest uppercase font-bold">Failure</h3>
            <h4 className="text-white font-serif text-lg mb-2">No Verification</h4>
            <p className="text-gray-500 text-sm">LLM output is trusted but never validated. Bugs slip through. They surface in production. Nobody can explain why the AI chose this.</p>
          </div>

          <div className="border-l-2 border-amber-900/50 pl-6">
            <h3 className="text-amber-600 text-xs mb-2 tracking-widest uppercase font-bold">Failure</h3>
            <h4 className="text-white font-serif text-lg mb-2">Token Waste</h4>
            <p className="text-gray-500 text-sm">Context is bloated because retrieval is naive. You pay for tokens the model ignores—while still missing the pieces it needs.</p>
          </div>

          <div className="border-l-2 border-amber-900/50 pl-6">
            <h3 className="text-amber-600 text-xs mb-2 tracking-widest uppercase font-bold">Failure</h3>
            <h4 className="text-white font-serif text-lg mb-2">Architecture Blindness</h4>
            <p className="text-gray-500 text-sm">The AI doesn't know your layers, service boundaries, or ADRs. It suggests changes that quietly violate your architecture and add debt.</p>
          </div>
        </div>
      </div>
    </section>
  )
}

function PipelineSection() {
  const steps = [
    { num: '01', stage: 'Stage', desc: 'User Request' },
    { num: '02', stage: 'Intent Router', desc: 'Semantic router → pure LLM' },
    { num: '03', stage: 'Selector Engine', desc: 'Pure Python scoring' },
    { num: '04', stage: 'Context Assembly', desc: 'Pillars 1–2–3' },
    { num: '05', stage: 'Token Optimizer', desc: 'Rank + dedupe + budget' },
    { num: '06', stage: 'LLM Call', desc: 'Claude / GPT / Gemini / local' },
    { num: '07', stage: 'Evidence', desc: 'Logs, tests, artifacts' },
    { num: '08', stage: 'Approval Gate', desc: 'Human sign-off' },
    { num: '09', stage: 'Result', desc: 'Committed + traceable' },
  ]

  return (
    <section className="bg-black pt-32 pb-32 px-8 border-b border-amber-900/20">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16">
          <div className="text-amber-600 text-xs mb-8 tracking-widest uppercase">
            § 02 — The Pipeline
          </div>
          <h2 className="text-5xl font-serif leading-tight text-white mb-4">
            Nine steps between <em className="italic text-amber-500">intent</em> and <em className="italic text-amber-500">result</em>.
          </h2>
          <p className="text-sm text-gray-400">
            No LLM call happens until context is ready. Routing, selection, and ranking are pure engineering—deterministic, cheap, auditable.
          </p>
        </div>

        {/* Table */}
        <div className="border border-gray-800 divide-y divide-gray-800">
          {steps.map((step, i) => (
            <div
              key={i}
              className="grid grid-cols-5 gap-4 px-6 py-4"
              style={{ background: i % 2 === 0 ? 'rgba(0,0,0,0.3)' : 'transparent' }}
            >
              <div className="text-amber-600 font-bold text-sm">{step.num}</div>
              <div className="text-gray-600 text-xs uppercase tracking-widest">Stage</div>
              <div className="col-span-2 text-white font-serif">{step.stage}</div>
              <div className="text-gray-600 text-xs uppercase tracking-widest">{step.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function PillarsSection() {
  return (
    <section className="bg-black pt-32 pb-32 px-8 border-b border-amber-900/20">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16">
          <div className="text-amber-600 text-xs mb-8 tracking-widest uppercase">
            § 03 — Five Pillars
          </div>
          <h2 className="text-5xl font-serif leading-tight text-white mb-4">
            Small, composable, <em className="italic text-amber-500">independently useful.</em>
          </h2>
          <p className="text-sm text-gray-400 max-w-2xl">
            Each pillar does one job. Together they answer: what exists, what should change, and how to verify the change is correct.
          </p>
        </div>

        {/* Pillars Grid - 2x3 layout with one spanning */}
        <div className="grid grid-cols-2 gap-6">
          {/* Pillar 1 */}
          <div className="border border-gray-800 p-6 bg-black/40">
            <div className="text-xs text-gray-600 uppercase tracking-widest mb-2">◆ Live • Phase 2</div>
            <h3 className="text-white font-serif text-lg mb-3">Repository Intelligence</h3>
            <p className="text-gray-500 text-sm">AST parsing via tree-sitter. Symbols, imports, call-graph, incremental indexing.</p>
            <ul className="text-xs text-gray-600 mt-4 space-y-1">
              <li>▪ tree-sitter AST</li>
              <li>▪ call-graph builder</li>
              <li>▪ git-diff incremental scan</li>
            </ul>
          </div>

          {/* Pillar 2 */}
          <div className="border border-gray-800 p-6 bg-black/40">
            <div className="text-xs text-gray-600 uppercase tracking-widest mb-2">◆ Live • Phase 2</div>
            <h3 className="text-white font-serif text-lg mb-3">ContextHub</h3>
            <p className="text-gray-500 text-sm">Persistent engineering knowledge. Full-text (BM25) + semantic (sqlite-vec) + RRF fusion.</p>
            <ul className="text-xs text-gray-600 mt-4 space-y-1">
              <li>▪ type artifacts • ADR / memo / conversation</li>
              <li>▪ hybrid search</li>
              <li>▪ project memory</li>
            </ul>
          </div>

          {/* Pillar 3 - Full width */}
          <div className="border border-gray-800 p-6 bg-black/40 col-span-2">
            <div className="text-xs text-gray-600 uppercase tracking-widest mb-2">◆ Live • Phase 2</div>
            <h3 className="text-white font-serif text-lg mb-3">Architectural Intelligence</h3>
            <p className="text-gray-500 text-sm">Pattern detection, layer analysis, blast-radius reasoning, tech-debt scoring, ADR compliance.</p>
            <ul className="text-xs text-gray-600 mt-4 space-y-1">
              <li>▪ layered / hexagonal / mvc / microservices</li>
              <li>▪ circular-dep detection</li>
              <li>▪ impact analysis</li>
            </ul>
          </div>

          {/* Pillar 4 */}
          <div className="border border-gray-800 p-6 bg-black/40">
            <div className="text-xs text-amber-600 uppercase tracking-widest mb-2">■ Phase 3 • Week 15–22</div>
            <h3 className="text-white font-serif text-lg mb-3">Engineering Orchestration</h3>
            <p className="text-gray-500 text-sm">Intent router, agent + skill registry, workflow executor, human approval gates.</p>
            <ul className="text-xs text-gray-600 mt-4 space-y-1">
              <li>▪ agents + skills/agents</li>
              <li>▪ skills + . skills</li>
              <li>▪ ortho run "intent"</li>
            </ul>
          </div>

          {/* Pillar 5 */}
          <div className="border border-gray-800 p-6 bg-black/40">
            <div className="text-xs text-amber-600 uppercase tracking-widest mb-2">■ Phase 4 • Week 23–28</div>
            <h3 className="text-white font-serif text-lg mb-3">Token Optimizer</h3>
            <p className="text-gray-500 text-sm">Intent-aware renaming, semantic dedup, graph expansion, per-model budget adapter.</p>
            <ul className="text-xs text-gray-600 mt-4 space-y-1">
              <li>▪ hard token ceiling</li>
              <li>▪ context compression</li>
              <li>▪ per-model strategy</li>
            </ul>
          </div>
        </div>

        {/* Footer note */}
        <div className="mt-12 border-t border-gray-800 pt-8 text-xs text-gray-600">
          <p>Frontend Preview Only. Please wake servers to enable backend functionality. <a href="#" className="text-amber-600 hover:underline">Wake up servers</a></p>
        </div>
      </div>
    </section>
  )
}

function ASESSection() {
  return (
    <section className="bg-black pt-32 pb-32 px-8 border-b border-amber-900/20">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16">
          <div className="text-amber-600 text-xs mb-8 tracking-widest uppercase">
            § 04 — ASES Methodology
          </div>
          <h2 className="text-5xl font-serif leading-tight text-white mb-4">
            Six gates. <em className="italic text-amber-500">No self-validated code ever ships.</em>
          </h2>
          <p className="text-sm text-gray-400">
            ASES is the process used to build Ortho. Every feature crosses these gates. Tests run. Logs are the evidence.
          </p>
        </div>

        {/* Gates */}
        <div className="grid grid-cols-6 gap-4 mb-12 border border-gray-800 divide-x divide-gray-800">
          {['01', '02', '03', '04', '05', '06'].map((gate, i) => (
            <div key={i} className="p-4 text-center border-l border-gray-800 first:border-l-0">
              <div className="text-amber-600 font-bold mb-2">{gate}</div>
              <div className="text-white font-serif text-sm mb-1">
                {['Plan', 'Architect', 'Build', 'Test', 'Review', 'Ship'][i]}
              </div>
              <div className="text-xs text-gray-600 uppercase tracking-widest">
                {['Planner', 'Architect', 'Builder', 'Test-Designer', 'Verifier', 'Reviewer'][i]}
              </div>
            </div>
          ))}
        </div>

        {/* Core principles */}
        <div className="border border-gray-800 p-8 bg-black/40">
          <h3 className="text-white font-serif text-lg mb-6">Core principles</h3>
          <div className="space-y-3 text-sm">
            {[
              'Evidence is more trustworthy than confidence.',
              'Planning is more valuable than rushing.',
              'Architecture should guide implementation.',
              'Repository understanding precedes code generation.',
              'Human approval is the final authority.',
              'Every decision leaves a traceable artifact.',
            ].map((principle, i) => (
              <div key={i} className="flex gap-3">
                <span className="text-amber-600 flex-shrink-0">▪ 01</span>
                <span className="text-gray-400">{principle}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="mt-12 grid grid-cols-3 gap-4 border border-gray-800 divide-x divide-gray-800">
          <div className="p-6 text-center">
            <div className="text-3xl font-serif text-amber-600">252</div>
            <div className="text-xs text-gray-600 mt-2 uppercase">Tests passed</div>
          </div>
          <div className="p-6 text-center">
            <div className="text-3xl font-serif text-amber-600">70</div>
            <div className="text-xs text-gray-600 mt-2 uppercase">Edge cases</div>
          </div>
          <div className="p-6 text-center">
            <div className="text-3xl font-serif text-amber-600">42</div>
            <div className="text-xs text-gray-600 mt-2 uppercase">Regression tests</div>
          </div>
        </div>
      </div>
    </section>
  )
}

function CLISection() {
  return (
    <section className="bg-black pt-32 pb-32 px-8 border-b border-amber-900/20">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16">
          <div className="text-amber-600 text-xs mb-8 tracking-widest uppercase">
            § 05 — The CLI
          </div>
          <h2 className="text-5xl font-serif leading-tight text-white mb-4">
            A thin wrapper. <em className="italic text-amber-500">Rigorous underneath.</em>
          </h2>
          <p className="text-sm text-gray-400">
            The CLI is your entry point. Everything runs locally, in .ortho/ inside your project.
          </p>
        </div>

        {/* CLI Demo */}
        <div className="grid grid-cols-2 gap-6">
          {/* Left - Commands */}
          <div className="border border-gray-800 p-6 font-mono text-xs bg-black/60">
            <div className="text-gray-600">$ commands</div>
            <div className="mt-4 space-y-2">
              <div className="text-amber-600">◆ ortho scan</div>
              <div className="text-gray-600 ml-6">→ scanning repository</div>

              <div className="text-amber-600 mt-4">◆ ortho analyze</div>
              <div className="text-gray-600 ml-6">→ run architecture report</div>

              <div className="text-amber-600 mt-4">◆ ortho analyze --impact</div>
              <div className="text-gray-600 ml-6">→ show blast radius on code architecture</div>

              <div className="text-amber-600 mt-4">◆ ortho context search</div>
              <div className="text-gray-600 ml-6">→ hybrid BM25 + semantic search</div>
            </div>
          </div>

          {/* Right - Output */}
          <div className="border border-gray-800 p-6 font-mono text-xs bg-black/60">
            <div className="text-amber-600">ortho> analyze</div>
            <div className="mt-2 text-green-500">▸ detecting architecture style...</div>
            <div className="text-green-500">✓ style: LAYERED    confidence: 0.87</div>
            <div className="text-green-500">✓ layers detected: 3    (data / business / presentation)</div>
            <div className="text-green-500">✓ subsystems detected: 5</div>

            <div className="text-gray-600 mt-4">circular deps: → 2 detected - see report</div>
            <div className="text-gray-600">tech debt (avg): 0.2 / module</div>
            <div className="text-gray-600">ADR compliance: 7/7 ADRs cross-referenced</div>

            <div className="text-amber-600 mt-4">report → .ortho/reports/architecture-2026-07-03.md</div>
            <div className="text-amber-600">ortho ▪</div>
          </div>
        </div>
      </div>
    </section>
  )
}

function ComparisonSection() {
  return (
    <section className="bg-black pt-32 pb-32 px-8 border-b border-amber-900/20">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16">
          <div className="text-amber-600 text-xs mb-8 tracking-widest uppercase">
            § 06 — The Difference
          </div>
          <h2 className="text-5xl font-serif leading-tight text-white">
            Traditional AI vs. <span className="text-amber-500">Ortho.</span>
          </h2>
        </div>

        {/* Comparison Table */}
        <div className="border border-gray-800 divide-y divide-gray-800">
          {[
            { metric: 'Context quality', traditional: 'Vague – user must summarize', ortho: 'Precise – scanned + indexed' },
            { metric: 'Architecture understanding', traditional: 'Zero', ortho: 'Complete – 5 pillars' },
            { metric: 'Blast-radius awareness', traditional: 'No', ortho: 'Yes – with confidence bands' },
            { metric: 'ADR compliance', traditional: 'No tracking', ortho: 'Automatic cross-reference' },
            { metric: 'Technical-debt visibility', traditional: 'None', ortho: 'Scored per module' },
            { metric: 'Evidence artifacts', traditional: 'None', ortho: 'Full logs per decision' },
            { metric: 'Human approval', traditional: 'Optional', ortho: 'Required at gates 1, 5, 6' },
            { metric: 'Token efficiency', traditional: 'Low – context bloat', ortho: 'High – ranked + deduped' },
            { metric: 'Circular-dep detection', traditional: 'No', ortho: 'Yes' },
            { metric: 'Code-reuse discovery', traditional: 'No', ortho: 'Yes – AST-based' },
            { metric: 'Incremental indexing', traditional: 'No', ortho: 'Yes – git-diff based' },
          ].map((row, i) => (
            <div
              key={i}
              className="grid grid-cols-3 gap-4 px-6 py-4"
              style={{ background: i % 2 === 0 ? 'rgba(0,0,0,0.2)' : 'transparent' }}
            >
              <div className="text-white font-serif">{row.metric}</div>
              <div className="text-gray-500 text-sm">
                <span className="text-amber-600">✗</span> {row.traditional}
              </div>
              <div className="text-gray-300 text-sm">
                <span className="text-green-500">✓</span> {row.ortho}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function RoadmapSection() {
  return (
    <section className="bg-black pt-32 pb-32 px-8 border-b border-amber-900/20">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16">
          <div className="text-amber-600 text-xs mb-8 tracking-widest uppercase">
            § 07 — Roadmap
          </div>
          <h2 className="text-5xl font-serif leading-tight text-white mb-4">
            Four phases. <em className="italic text-amber-500">Two shipped.</em>
          </h2>
          <p className="text-sm text-gray-400">
            We're honest about scope. Phases 1–2 are live and tested. Phase 3 is in progress. Phase 4 comes after.
          </p>
        </div>

        {/* Phase cards */}
        <div className="grid grid-cols-4 gap-6">
          {[
            { phase: 'Phase 1', title: 'Foundation', weeks: 'Weeks 1 – 8', status: '✓ Shipped', statusColor: 'bg-green-600' },
            { phase: 'Phase 2', title: 'Reasoning', weeks: 'Weeks 9 – 14', status: '✓ Shipped', statusColor: 'bg-green-600' },
            { phase: 'Phase 3', title: 'Execution', weeks: 'Weeks 15 – 22', status: '■ In progress', statusColor: 'bg-amber-600' },
            { phase: 'Phase 4', title: 'Optimization', weeks: 'Weeks 23 – 28', status: '◆ Planned', statusColor: 'bg-gray-600' },
          ].map((p, i) => (
            <div key={i} className="border border-gray-800 p-6 bg-black/40">
              <div className="text-xs text-gray-600 uppercase tracking-widest mb-2">{p.phase}</div>
              <h3 className="text-white font-serif text-lg mb-3">{p.title}</h3>
              <p className="text-xs text-gray-600 mb-6">{p.weeks}</p>
              <div className={`${p.statusColor} text-black text-xs font-bold px-2 py-1 w-fit`}>
                {p.status}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function CTA() {
  return (
    <section className="bg-black pt-32 pb-32 px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-5xl font-serif text-white leading-tight mb-8">
            Get access when
            <br />
            <span className="text-amber-500 italic">Phase 3</span>
            {' '}launches.
          </h2>
          <p className="text-sm text-gray-400 max-w-lg mx-auto">
            Ortho's core intelligence (scan · analyze · context) is live now. Join the waitlist to get the orchestration release first, plus the ASES workflow docs.
          </p>
        </div>

        {/* Signup form */}
        <div className="max-w-md mx-auto border border-gray-800 p-8 bg-black/40">
          <div className="space-y-4">
            <input
              type="email"
              placeholder="your@company.dev"
              className="w-full bg-black border border-gray-800 px-4 py-2 text-sm text-gray-300 placeholder-gray-600 focus:border-amber-600 focus:outline-none"
            />
            <select className="w-full bg-black border border-gray-800 px-4 py-2 text-sm text-gray-300 focus:border-amber-600 focus:outline-none">
              <option>Individual Engineer</option>
              <option>Architect</option>
              <option>Engineering Manager</option>
              <option>Founder / CTO</option>
            </select>
            <button className="w-full bg-amber-600 text-black px-4 py-2 text-xs font-bold tracking-widest uppercase hover:bg-amber-500">
              REQUEST ACCESS →
            </button>
          </div>

          <div className="mt-6 border-t border-gray-800 pt-4 text-xs text-gray-600 space-y-1">
            <p>◆ urbra@cybersecurity.com</p>
            <p>◆ Direct contact</p>
            <p>◆ subscribe <strong>ON</strong></p>
          </div>
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="bg-black border-t border-amber-900/20 py-12 px-8">
      <div className="max-w-7xl mx-auto grid grid-cols-4 gap-8 mb-12">
        <div>
          <h4 className="text-xs text-amber-600 font-bold uppercase tracking-widest mb-4">Product</h4>
          <ul className="space-y-2">
            <li><a href="#" className="text-xs text-gray-500 hover:text-white">Features</a></li>
            <li><a href="#" className="text-xs text-gray-500 hover:text-white">Architecture</a></li>
            <li><a href="#" className="text-xs text-gray-500 hover:text-white">Pricing</a></li>
          </ul>
        </div>
        <div>
          <h4 className="text-xs text-amber-600 font-bold uppercase tracking-widest mb-4">Docs</h4>
          <ul className="space-y-2">
            <li><a href="#" className="text-xs text-gray-500 hover:text-white">Getting Started</a></li>
            <li><a href="#" className="text-xs text-gray-500 hover:text-white">Roadmap</a></li>
            <li><a href="#" className="text-xs text-gray-500 hover:text-white">Changelog</a></li>
          </ul>
        </div>
        <div>
          <h4 className="text-xs text-amber-600 font-bold uppercase tracking-widest mb-4">Community</h4>
          <ul className="space-y-2">
            <li><a href="https://github.com/urbra/ortho" className="text-xs text-gray-500 hover:text-white">GitHub</a></li>
            <li><a href="#" className="text-xs text-gray-500 hover:text-white">Discord</a></li>
            <li><a href="#" className="text-xs text-gray-500 hover:text-white">Contact</a></li>
          </ul>
        </div>
        <div>
          <h4 className="text-xs text-amber-600 font-bold uppercase tracking-widest mb-4">Legal</h4>
          <ul className="space-y-2">
            <li><a href="#" className="text-xs text-gray-500 hover:text-white">Privacy Policy</a></li>
            <li><a href="#" className="text-xs text-gray-500 hover:text-white">Terms of Service</a></li>
            <li><a href="#" className="text-xs text-gray-500 hover:text-white">Security</a></li>
          </ul>
        </div>
      </div>

      <div className="border-t border-amber-900/20 pt-8 text-center text-xs text-gray-600">
        <p>© 2026 Ortho – v3 Preview</p>
        <p className="mt-2">Local-first. Engineered. No guesses.</p>
      </div>
    </footer>
  )
}

export default function HomeRedesigned() {
  return (
    <main className="bg-black text-white">
      <Navbar />
      <HeroSection />
      <ProblemSection />
      <PipelineSection />
      <PillarsSection />
      <ASESSection />
      <CLISection />
      <ComparisonSection />
      <RoadmapSection />
      <CTA />
      <Footer />
    </main>
  )
}
