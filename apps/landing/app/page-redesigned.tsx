'use client'

import { motion } from 'framer-motion'
import { useScroll, useTransform } from 'framer-motion'
import { useRef } from 'react'

/**
 * ORTHO LANDING PAGE — VERSION 2.0
 *
 * Evolution of existing design:
 * - Preserve: Black background, warm amber accent, serif typography, monospace UI, thin borders
 * - Improve: Messaging (outcomes over technical), spacing, hierarchy, subtle motion
 * - Keep the soul: Editorial, engineering-first, terminal aesthetic, brutalist minimalism
 */

// ============================================================================
// SECTION 1: NAVBAR
// ============================================================================

function Navbar() {
  return (
    <motion.nav
      className="fixed top-0 w-full z-50 border-b border-amber-900/30"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      style={{ background: 'rgba(0, 0, 0, 0.8)', backdropFilter: 'blur(8px)' }}
    >
      <div className="max-w-7xl mx-auto px-8 py-4 flex justify-between items-center">
        <a href="/" className="text-lg font-bold tracking-widest text-white" style={{ fontFamily: 'monospace' }}>
          ◆ ORTHO
        </a>
        <div className="flex gap-12 items-center">
          <a href="#problem" className="text-xs text-gray-400 hover:text-white tracking-wide uppercase">
            Problem
          </a>
          <a href="#solution" className="text-xs text-gray-400 hover:text-white tracking-wide uppercase">
            Solution
          </a>
          <a href="#gates" className="text-xs text-gray-400 hover:text-white tracking-wide uppercase">
            ASES
          </a>
          <button
            onClick={() => window.open('https://github.com/urbra/ortho', '_blank')}
            className="text-xs text-gray-400 hover:text-white tracking-wide uppercase"
          >
            GitHub
          </button>
          <motion.button
            onClick={() => window.location.href = 'mailto:urbrain369@gmail.com?subject=Ortho%20Beta%20Access'}
            className="px-4 py-2 text-xs font-bold tracking-wide uppercase"
            style={{ background: '#FFA500', color: '#000' }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Join Beta
          </motion.button>
        </div>
      </div>
    </motion.nav>
  )
}

// ============================================================================
// SECTION 2: HERO
// ============================================================================

function HeroSection() {
  const ref = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start start', 'end center'],
  })

  const opacity = useTransform(scrollYProgress, [0, 0.4], [1, 0])

  return (
    <motion.section
      ref={ref}
      className="relative min-h-screen flex items-center pt-20 px-8 md:px-16 bg-black overflow-hidden"
      style={{ opacity }}
    >
      {/* Subtle grid */}
      <div className="absolute inset-0 opacity-5" style={{
        backgroundImage: 'linear-gradient(rgba(255,165,0,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,165,0,0.1) 1px, transparent 1px)',
        backgroundSize: '50px 50px'
      }} />

      <div className="relative z-10 max-w-7xl w-full grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
        {/* Left: Headline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="text-xs font-bold tracking-widest text-amber-500 uppercase mb-8">
            § Phase 3 Complete • 252 / 70 / 42 Tests
          </div>

          <h1 className="text-7xl md:text-8xl font-serif leading-tight mb-8 text-white">
            Scan first.
            <br />
            <span style={{ color: '#FFA500' }}>Ask once.</span>
            <br />
            Ship confident.
          </h1>

          <p className="text-sm leading-relaxed text-gray-400 mb-12 max-w-md" style={{ fontFamily: 'monospace' }}>
            Ortho is an AI engineering platform. It helps your AI understand your repository, understand your architecture, and assemble precise context—so the LLM works with evidence, not guesses.
          </p>

          <div className="flex gap-4">
            <motion.button
              onClick={() => window.location.href = 'mailto:urbrain369@gmail.com?subject=Ortho%20Beta%20Access'}
              className="px-6 py-3 text-xs font-bold tracking-wide uppercase"
              style={{ background: '#FFA500', color: '#000', border: '1px solid #FFA500' }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Join the Beta →
            </motion.button>
            <motion.button
              onClick={() => window.open('https://github.com/urbra/ortho', '_blank')}
              className="px-6 py-3 text-xs font-bold tracking-wide uppercase border border-gray-600 text-white hover:border-amber-500 hover:text-amber-500"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              View GitHub
            </motion.button>
          </div>
        </motion.div>

        {/* Right: Terminal */}
        <motion.div
          className="border border-amber-900/50 p-6 font-mono text-xs leading-relaxed h-96 overflow-y-auto"
          style={{ background: 'rgba(0,0,0,0.6)', color: '#fff' }}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <div className="mb-4 text-gray-500"># User request</div>
          <div className="mb-4 text-white">
            <span style={{ color: '#FFA500' }}>{'$'}</span> ortho context "Add authentication"
          </div>

          <div className="mb-4 text-gray-500"># Repository scanned</div>
          <div className="mb-2 text-green-500">✓ existing auth middleware found</div>
          <div className="mb-2 text-green-500">✓ auth flow identified (session-based)</div>
          <div className="mb-4 text-green-500">✓ architecture pattern: MVC + middleware</div>

          <div className="mb-4 text-gray-500"># Recommended files</div>
          <div className="mb-1 text-blue-400">→ src/middleware/auth.ts</div>
          <div className="mb-1 text-blue-400">→ src/lib/session.ts</div>
          <div className="mb-4 text-blue-400">→ src/routes/protected.ts</div>

          <div className="mb-4 text-gray-500"># Reasoning</div>
          <div className="text-amber-400">All files follow existing patterns. Zero breaking changes.</div>
        </motion.div>
      </div>
    </motion.section>
  )
}

// ============================================================================
// SECTION 3: PROBLEM
// ============================================================================

function ProblemSection() {
  const problems = [
    {
      title: 'AI forgets your project.',
      desc: 'Without context, generated code ignores patterns and existing implementations.'
    },
    {
      title: 'AI edits the wrong files.',
      desc: 'Suggestions miss dependencies, create conflicts, violate your architecture.'
    },
    {
      title: 'AI breaks your architecture.',
      desc: 'Generated code introduces circular imports or violates layer boundaries.'
    },
    {
      title: 'AI repeats mistakes.',
      desc: 'Every conversation starts from zero. No memory of past decisions or patterns.'
    }
  ]

  return (
    <section className="relative py-32 px-8 md:px-16 bg-black border-t border-amber-900/30" id="problem">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <div className="text-xs font-bold tracking-widest text-amber-500 uppercase mb-8">§ 01 — The Problem</div>
            <h2 className="text-5xl md:text-6xl font-serif leading-tight text-white mb-8">
              AI-assisted development
              <br />
              <em style={{ fontStyle: 'italic', color: '#FFA500' }}>is a broken loop.</em>
            </h2>
            <p className="text-sm text-gray-400 leading-relaxed" style={{ fontFamily: 'monospace' }}>
              Four failure modes appear in every team. Ortho addresses each at the source—before the LLM is called.
            </p>
          </motion.div>

          <div className="space-y-12">
            {problems.map((problem, i) => (
              <motion.div
                key={i}
                className="border-l-2 border-amber-900/50 pl-6"
                initial={{ opacity: 0, x: 10 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <h3 className="text-lg font-serif text-white mb-2">{problem.title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed" style={{ fontFamily: 'monospace' }}>
                  {problem.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 4: PIPELINE
// ============================================================================

function PipelineSection() {
  const steps = [
    { num: '01', name: 'Ask', detail: 'User Request' },
    { num: '02', name: 'Understand', detail: 'Scan Repository' },
    { num: '03', name: 'Retrieve', detail: 'Assemble Context' },
    { num: '04', name: 'Reason', detail: 'Architecture Analysis' },
    { num: '05', name: 'Generate', detail: 'LLM Inference' },
    { num: '06', name: 'Verify', detail: 'Evidence Check' },
    { num: '07', name: 'Approve', detail: 'Human Gate' },
    { num: '08', name: 'Ship', detail: 'Committed' },
  ]

  return (
    <section className="relative py-32 px-8 md:px-16 bg-black border-t border-amber-900/30">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-20"
        >
          <div className="text-xs font-bold tracking-widest text-amber-500 uppercase mb-8">§ 02 — The Pipeline</div>
          <h2 className="text-5xl md:text-6xl font-serif text-white mb-4">
            Nine steps between <em style={{ fontStyle: 'italic', color: '#FFA500' }}>intent</em> and <em style={{ fontStyle: 'italic', color: '#FFA500' }}>result</em>.
          </h2>
          <p className="text-sm text-gray-400" style={{ fontFamily: 'monospace' }}>
            No LLM call happens until context is ready. Routing, selection, and ranking are pure engineering—deterministic, cheap, auditable.
          </p>
        </motion.div>

        {/* Table layout */}
        <div className="border border-amber-900/50 divide-y divide-amber-900/50">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              className="grid grid-cols-5 gap-4 px-6 py-4"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              style={{ background: i % 2 === 0 ? 'rgba(0,0,0,0.3)' : 'transparent' }}
            >
              <div className="text-xs text-amber-500 font-bold">{step.num}</div>
              <div className="text-xs text-gray-500 uppercase">Step</div>
              <div className="col-span-2 text-sm font-serif text-white">{step.name}</div>
              <div className="text-xs text-gray-500">{step.detail}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 5: SOLUTION
// ============================================================================

function SolutionSection() {
  const pillars = [
    {
      phase: 'Phase 2',
      title: 'Repository Intelligence',
      desc: 'AST parsing via tree-sitter. Symbols, imports, call-graph, incremental indexing.'
    },
    {
      phase: 'Phase 2',
      title: 'ContextHub',
      desc: 'Persistent engineering knowledge. Full-text (BM25) + semantic (sqlite-vec) + RRF fusion.'
    },
    {
      phase: 'Phase 2',
      title: 'Architectural Intelligence',
      desc: 'Pattern detection, layer analysis, blast-radius reasoning, tech-debt scoring, ADR awareness.'
    },
    {
      phase: 'Phase 3',
      title: 'Engineering Orchestration',
      desc: 'Intent router, agent + skill registry, workflow executor, human approval gates.'
    },
    {
      phase: 'Phase 4',
      title: 'Token Optimizer',
      desc: 'Intent-aware renaming, semantic dedup, graph expansion, per-model budget adapter.'
    }
  ]

  return (
    <section className="relative py-32 px-8 md:px-16 bg-black border-t border-amber-900/30" id="solution">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-20"
        >
          <div className="text-xs font-bold tracking-widest text-amber-500 uppercase mb-8">§ 03 — Five Pillars</div>
          <h2 className="text-5xl md:text-6xl font-serif text-white">
            Small, composable,
            <br />
            <em style={{ fontStyle: 'italic', color: '#FFA500' }}>independently useful.</em>
          </h2>
          <p className="text-sm text-gray-400 mt-8 max-w-2xl" style={{ fontFamily: 'monospace' }}>
            Each pillar does one job. Together they answer: what exists, what should change, and how to verify the change is correct.
          </p>
        </motion.div>

        <div className="space-y-6">
          {pillars.map((pillar, i) => (
            <motion.div
              key={i}
              className="border border-amber-900/50 p-6"
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              style={{ background: 'rgba(0,0,0,0.4)' }}
            >
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">Phase</div>
                  <div className="text-sm font-serif text-amber-500">{pillar.phase}</div>
                </div>
                <div className="md:col-span-2">
                  <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">Pillar</div>
                  <div className="text-base font-serif text-white">{pillar.title}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">What it does</div>
                  <div className="text-xs text-gray-400" style={{ fontFamily: 'monospace' }}>{pillar.desc}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 6: ASES
// ============================================================================

function ASESSection() {
  const gates = [
    { num: '01', name: 'PLAN', role: 'PLANNER', desc: 'Specification' },
    { num: '02', name: 'ARCHITECT', role: 'ARCHITECT', desc: 'Design Review' },
    { num: '03', name: 'BUILD', role: 'BUILDER', desc: 'Implementation' },
    { num: '04', name: 'TEST', role: 'TEST-DESIGNER', desc: 'Verification' },
    { num: '05', name: 'VERIFY', role: 'VERIFIER', desc: 'Evidence' },
    { num: '06', name: 'REVIEW', role: 'REVIEWER', desc: 'Approval' },
  ]

  return (
    <section className="relative py-32 px-8 md:px-16 bg-black border-t border-amber-900/30" id="gates">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-20"
        >
          <div className="text-xs font-bold tracking-widest text-amber-500 uppercase mb-8">§ 04 — ASES Methodology</div>
          <h2 className="text-5xl md:text-6xl font-serif text-white mb-4">
            Six gates.
            <br />
            <em style={{ fontStyle: 'italic', color: '#FFA500' }}>No self-validated code ever ships.</em>
          </h2>
          <p className="text-sm text-gray-400 max-w-2xl" style={{ fontFamily: 'monospace' }}>
            ASES is the process used to build Ortho. Every feature crosses these gates. Tests run. Logs are the evidence.
          </p>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-16">
          {gates.map((gate, i) => (
            <motion.div
              key={i}
              className="border border-amber-900/50 p-4"
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              style={{ background: 'rgba(0,0,0,0.6)' }}
            >
              <div className="text-xs text-amber-500 font-bold mb-2">{gate.num}</div>
              <div className="text-sm font-serif text-white mb-1">{gate.name}</div>
              <div className="text-xs text-gray-500 uppercase tracking-wide">{gate.role}</div>
            </motion.div>
          ))}
        </div>

        <motion.div
          className="border border-amber-900/50 p-8"
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          style={{ background: 'rgba(0,0,0,0.4)' }}
        >
          <h3 className="text-base font-serif text-white mb-6">Core Principles</h3>
          <div className="space-y-3">
            {[
              'Evidence is more trustworthy than confidence.',
              'Planning is more valuable than rushing.',
              'Architecture should guide implementation.',
              'Repository understanding precedes code generation.',
              'Human approval is the final authority.',
              'Every decision leaves a traceable artifact.',
            ].map((principle, i) => (
              <div key={i} className="flex gap-3">
                <span style={{ color: '#FFA500' }}>◆</span>
                <span className="text-sm text-gray-300">{principle}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 7: CLI
// ============================================================================

function CLISection() {
  return (
    <section className="relative py-32 px-8 md:px-16 bg-black border-t border-amber-900/30">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <div className="text-xs font-bold tracking-widest text-amber-500 uppercase mb-8">§ 05 — The CLI</div>
          <h2 className="text-5xl md:text-6xl font-serif text-white mb-4">
            A thin wrapper.
            <br />
            <em style={{ fontStyle: 'italic', color: '#FFA500' }}>Rigorous underneath.</em>
          </h2>
          <p className="text-sm text-gray-400 max-w-2xl" style={{ fontFamily: 'monospace' }}>
            The CLI is your entry point. Everything runs locally, in .ortho/ inside your project.
          </p>
        </motion.div>

        <motion.div
          className="grid grid-cols-1 lg:grid-cols-2 gap-8"
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          {/* Left: Commands */}
          <div className="border border-amber-900/50 p-6" style={{ background: 'rgba(0,0,0,0.6)' }}>
            <div className="font-mono text-xs leading-relaxed text-gray-300">
              <div className="text-amber-500 mb-4">$ ortho scan</div>
              <div className="text-gray-500 ml-4">→ index your repository</div>

              <div className="text-amber-500 mt-4 mb-4">$ ortho analyze</div>
              <div className="text-gray-500 ml-4">→ detect architecture pattern</div>

              <div className="text-amber-500 mt-4 mb-4">$ ortho analyze --impact</div>
              <div className="text-gray-500 ml-4">→ show blast radius</div>

              <div className="text-amber-500 mt-4 mb-4">$ ortho context search</div>
              <div className="text-gray-500 ml-4">→ hybrid BM25 + semantic search</div>
            </div>
          </div>

          {/* Right: Output */}
          <div className="border border-amber-900/50 p-6 font-mono text-xs leading-relaxed overflow-y-auto" style={{ background: 'rgba(0,0,0,0.6)', color: '#0f0' }}>
            <div className="text-gray-500">ortho{'>'} analyze</div>
            <div className="mt-2 text-green-500">✓ Repository scanned</div>
            <div className="text-green-500">✓ Architecture detected: LAYERED</div>
            <div className="text-green-500">✓ Confidence: 0.87</div>
            <div className="mt-2 text-gray-400">Layers detected: 3</div>
            <div className="text-gray-400">Circular deps: 0</div>
            <div className="text-gray-400">Tech-debt: 0.2 / module</div>
            <div className="mt-2 text-green-500">✓ Report: .ortho/reports/architecture-2026-07-03.md</div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 8: COMPARISON
// ============================================================================

function ComparisonSection() {
  const rows = [
    { metric: 'Context quality', traditional: 'Vague – user must summarize', ortho: 'Precise – scanned + indexed' },
    { metric: 'Architecture understanding', traditional: 'Zero', ortho: 'Complete – 5 pillars' },
    { metric: 'Blast-radius awareness', traditional: 'No', ortho: 'Yes – with confidence bands' },
    { metric: 'ADR compliance', traditional: 'No tracking', ortho: 'Automatic cross-reference' },
    { metric: 'Technical-debt visibility', traditional: 'None', ortho: 'Scored per module' },
    { metric: 'Evidence artifacts', traditional: 'None', ortho: 'Full logs per decision' },
    { metric: 'Human approval', traditional: 'Optional', ortho: 'Required at gates 1, 5, 6' },
  ]

  return (
    <section className="relative py-32 px-8 md:px-16 bg-black border-t border-amber-900/30">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <div className="text-xs font-bold tracking-widest text-amber-500 uppercase mb-8">§ 06 — The Difference</div>
          <h2 className="text-5xl md:text-6xl font-serif text-white">
            Traditional AI vs.
            <br />
            <span style={{ color: '#FFA500' }}>Ortho.</span>
          </h2>
        </motion.div>

        <div className="border border-amber-900/50 divide-y divide-amber-900/50">
          {rows.map((row, i) => (
            <motion.div
              key={i}
              className="grid grid-cols-1 md:grid-cols-3 gap-4 px-6 py-4"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              style={{ background: i % 2 === 0 ? 'rgba(0,0,0,0.2)' : 'transparent' }}
            >
              <div className="text-sm font-serif text-white">{row.metric}</div>
              <div className="text-xs text-gray-400">
                <span style={{ color: '#FFA500' }}>✗</span> {row.traditional}
              </div>
              <div className="text-xs text-gray-300">
                <span style={{ color: '#10b981' }}>✓</span> {row.ortho}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 9: ROADMAP
// ============================================================================

function RoadmapSection() {
  const phases = [
    { phase: 'Phase 1', title: 'Foundation', status: 'SHIPPED', color: '#10b981' },
    { phase: 'Phase 2', title: 'Reasoning', status: 'SHIPPED', color: '#10b981' },
    { phase: 'Phase 3', title: 'Execution', status: 'IN PROGRESS', color: '#FFA500' },
    { phase: 'Phase 4', title: 'Optimization', status: 'PLANNED', color: '#666' },
  ]

  return (
    <section className="relative py-32 px-8 md:px-16 bg-black border-t border-amber-900/30">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <div className="text-xs font-bold tracking-widest text-amber-500 uppercase mb-8">§ 07 — Roadmap</div>
          <h2 className="text-5xl md:text-6xl font-serif text-white mb-4">
            Four phases.
            <br />
            <em style={{ fontStyle: 'italic', color: '#FFA500' }}>Two shipped.</em>
          </h2>
          <p className="text-sm text-gray-400" style={{ fontFamily: 'monospace' }}>
            We're honest about scope. Phases 1–2 are live and tested. Phase 3 is in progress. Phase 4 comes after.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {phases.map((p, i) => (
            <motion.div
              key={i}
              className="border border-amber-900/50 p-6"
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              style={{ background: 'rgba(0,0,0,0.4)' }}
            >
              <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">{p.phase}</div>
              <div className="text-base font-serif text-white mb-4">{p.title}</div>
              <div className="px-2 py-1 text-xs font-bold uppercase text-center" style={{ background: p.color, color: '#000' }}>
                {p.status}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 10: FINAL CTA
// ============================================================================

function FinalCTASection() {
  return (
    <section className="relative py-32 px-8 md:px-16 bg-black border-t border-amber-900/30">
      <div className="max-w-5xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-5xl md:text-6xl font-serif text-white mb-8 leading-tight">
            Ready to build software
            <br />
            with AI that understands
            <br />
            your project?
          </h2>

          <div className="flex flex-col md:flex-row gap-4 justify-center mt-12">
            <motion.button
              onClick={() => window.location.href = 'mailto:urbrain369@gmail.com?subject=Ortho%20Beta%20Access'}
              className="px-8 py-4 text-xs font-bold tracking-widest uppercase"
              style={{ background: '#FFA500', color: '#000', border: '1px solid #FFA500' }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Join the Beta
            </motion.button>
            <motion.button
              onClick={() => window.open('https://github.com/urbra/ortho', '_blank')}
              className="px-8 py-4 text-xs font-bold tracking-widest uppercase border border-gray-600 text-white hover:border-amber-500 hover:text-amber-500"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              View GitHub
            </motion.button>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

// ============================================================================
// FOOTER
// ============================================================================

function Footer() {
  return (
    <footer className="border-t border-amber-900/30 py-12 px-8 md:px-16 bg-black">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          <div>
            <h4 className="text-xs font-bold text-amber-500 uppercase tracking-widest mb-4">Product</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-xs text-gray-400 hover:text-white">Features</a></li>
              <li><a href="#" className="text-xs text-gray-400 hover:text-white">Pricing</a></li>
              <li><a href="#" className="text-xs text-gray-400 hover:text-white">Roadmap</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-xs font-bold text-amber-500 uppercase tracking-widest mb-4">Resources</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-xs text-gray-400 hover:text-white">Docs</a></li>
              <li><a href="#" className="text-xs text-gray-400 hover:text-white">API</a></li>
              <li><a href="https://github.com/urbra/ortho" target="_blank" className="text-xs text-gray-400 hover:text-white">GitHub</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-xs font-bold text-amber-500 uppercase tracking-widest mb-4">Company</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-xs text-gray-400 hover:text-white">About</a></li>
              <li><a href="#" className="text-xs text-gray-400 hover:text-white">Blog</a></li>
              <li><a href="#" className="text-xs text-gray-400 hover:text-white">Contact</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-xs font-bold text-amber-500 uppercase tracking-widest mb-4">Legal</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-xs text-gray-400 hover:text-white">Privacy</a></li>
              <li><a href="#" className="text-xs text-gray-400 hover:text-white">Terms</a></li>
              <li><a href="#" className="text-xs text-gray-400 hover:text-white">Security</a></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-amber-900/30 pt-8 text-center text-xs text-gray-500" style={{ fontFamily: 'monospace' }}>
          <p>© 2026 Ortho — v3 Preview</p>
          <p className="mt-2 text-gray-600">Local-first. Engineered. No guesses.</p>
        </div>
      </div>
    </footer>
  )
}

// ============================================================================
// MAIN EXPORT
// ============================================================================

export default function HomeRedesigned() {
  return (
    <main className="bg-black text-white relative">
      <Navbar />
      <HeroSection />
      <ProblemSection />
      <PipelineSection />
      <SolutionSection />
      <ASESSection />
      <CLISection />
      <ComparisonSection />
      <RoadmapSection />
      <FinalCTASection />
      <Footer />
    </main>
  )
}
