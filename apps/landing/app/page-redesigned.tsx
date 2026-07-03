'use client'

import { motion } from 'framer-motion'
import { useScroll, useTransform } from 'framer-motion'
import { useRef } from 'react'

/**
 * ORTHO LANDING PAGE — PREMIUM, MINIMAL, ENGINEERING-FOCUSED
 *
 * Design philosophy:
 * - Dark (deep black) with warm orange accent
 * - Large typography (serif display for headlines, sans-serif body)
 * - Generous whitespace
 * - Thin borders, subtle grid
 * - One idea per section
 * - Motion for context, not decoration
 * - Trust, clarity, engineering excellence
 */

// ============================================================================
// SECTION 1: NAVBAR
// ============================================================================

function Navbar() {
  return (
    <motion.nav
      className="fixed top-0 w-full z-50 border-b border-slate-800/50 backdrop-blur-sm"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="max-w-7xl mx-auto px-8 py-4 flex justify-between items-center">
        <a href="/" className="text-lg font-semibold tracking-widest text-slate-50">
          ORTHO
        </a>
        <div className="flex gap-8 items-center">
          <a href="#features" className="text-sm text-slate-400 hover:text-slate-200">
            Features
          </a>
          <a href="#how" className="text-sm text-slate-400 hover:text-slate-200">
            How it works
          </a>
          <button
            onClick={() => window.open('https://github.com/urbra/ortho', '_blank')}
            className="text-sm text-slate-400 hover:text-slate-200"
          >
            GitHub
          </button>
          <motion.button
            onClick={() =>
              window.location.href =
                'mailto:urbrain369@gmail.com?subject=Ortho%20Beta%20Access'
            }
            className="px-5 py-2 bg-orange-600 text-white text-sm font-semibold hover:bg-orange-500 transition-colors"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Get Started
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
      className="relative min-h-screen flex items-center pt-20 px-8 md:px-12 bg-slate-950 overflow-hidden"
      style={{ opacity }}
    >
      {/* Subtle grid background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(100,116,139,0.05)_1px,transparent_1px)] bg-[length:50px_50px] pointer-events-none" />

      {/* Accent glow (subtle) */}
      <div className="absolute top-1/2 right-0 w-96 h-96 bg-orange-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-7xl w-full grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        {/* Left: Headline & CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        >
          <h1 className="font-serif text-5xl md:text-7xl leading-tight mb-8 text-slate-50">
            AI shouldn't guess.
          </h1>
          <p className="text-lg text-slate-400 mb-12 max-w-md leading-relaxed">
            Ortho is the engineering brain for AI. It helps your AI understand your
            codebase, architecture, and decisions before generating code.
          </p>
          <div className="flex gap-4">
            <motion.button
              onClick={() =>
                window.location.href =
                  'mailto:urbrain369@gmail.com?subject=Ortho%20Beta%20Access'
              }
              className="px-8 py-3 bg-orange-600 text-white font-semibold hover:bg-orange-500 transition-colors"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Get Started
            </motion.button>
            <motion.button
              onClick={() => window.open('https://github.com/urbra/ortho', '_blank')}
              className="px-8 py-3 border border-slate-700 text-slate-200 font-semibold hover:border-slate-600 hover:bg-slate-900/50 transition-all"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              View GitHub
            </motion.button>
          </div>
        </motion.div>

        {/* Right: Interactive demo */}
        <motion.div
          className="bg-slate-900 border border-slate-800 p-6 font-mono text-sm leading-relaxed h-96 overflow-y-auto"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
        >
          <div className="mb-4">
            <span className="text-slate-500">User:</span>{' '}
            <span className="text-slate-200">Add authentication.</span>
          </div>
          <div className="mb-1"></div>
          <div className="mb-4">
            <span className="text-orange-500">Ortho:</span>
          </div>
          <div className="mb-2">
            <span className="text-green-500">✓</span> Repository scanned
          </div>
          <div className="mb-2">
            <span className="text-green-500">✓</span> Existing auth flow detected
          </div>
          <div className="mb-4">
            <span className="text-green-500">✓</span> Architecture pattern identified
          </div>
          <div className="mb-4">
            <span className="text-orange-500">Recommended files:</span>
            <div className="text-slate-400 ml-4 mt-2">auth.ts</div>
            <div className="text-slate-400 ml-4">middleware.ts</div>
            <div className="text-slate-400 ml-4">session.ts</div>
          </div>
          <div className="mb-2">
            <span className="text-orange-500">Reason:</span>
          </div>
          <div className="text-slate-400">Matches existing architecture.</div>
        </motion.div>
      </div>
    </motion.section>
  )
}

// ============================================================================
// SECTION 3: PROBLEMS
// ============================================================================

function ProblemsSection() {
  const problems = [
    { title: 'AI forgets your project.', desc: 'Without context, generated code ignores patterns and existing implementations.' },
    { title: 'AI changes the wrong files.', desc: 'Recommendations miss dependencies, create conflicts, or violate architecture.' },
    { title: 'AI breaks architecture.', desc: 'Generated code introduces circular deps or violates layer boundaries.' },
    { title: 'AI repeats mistakes.', desc: 'Every conversation starts from zero. No memory of past decisions.' },
  ]

  return (
    <section className="relative py-32 px-8 md:px-12 bg-slate-950">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 md:gap-16">
          {problems.map((problem, i) => (
            <motion.div
              key={i}
              className="border-l-2 border-slate-800 pl-6"
              initial={{ opacity: 0, x: -10 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <h3 className="font-serif text-xl text-slate-50 mb-3">{problem.title}</h3>
              <p className="text-slate-400 text-sm">{problem.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 4: HOW IT WORKS
// ============================================================================

function WorkflowSection() {
  const steps = ['Ask', 'Understand', 'Retrieve', 'Reason', 'Generate', 'Verify', 'Approve', 'Ship']

  return (
    <section className="relative py-32 px-8 md:px-12 bg-slate-900" id="how">
      <div className="max-w-5xl mx-auto">
        <motion.h2
          className="font-serif text-4xl md:text-5xl mb-20 text-center text-slate-50"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          How it works.
        </motion.h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              className="bg-slate-800 border border-slate-700 p-4 text-center text-sm font-semibold text-slate-200"
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              whileHover={{ borderColor: '#ea580c', bg: '#1a1a2e' }}
            >
              {step}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 5: FEATURES
// ============================================================================

function FeaturesSection() {
  const features = [
    { icon: '📚', title: 'Repository Understanding', desc: 'AI learns your codebase automatically.' },
    { icon: '🧠', title: 'Engineering Memory', desc: 'Never repeat project context. ADRs persist.' },
    { icon: '🏛️', title: 'Architecture Awareness', desc: 'Recommendations follow your design patterns.' },
    { icon: '✓', title: 'Evidence-Based Development', desc: 'Every change backed by proof and logs.' },
    { icon: '🔗', title: 'Works With Your AI', desc: 'Claude, Gemini, OpenAI, local models.' },
  ]

  return (
    <section className="relative py-32 px-8 md:px-12 bg-slate-950" id="features">
      <div className="max-w-7xl mx-auto">
        <motion.h2
          className="font-serif text-4xl md:text-5xl mb-20 text-slate-50"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          Five core capabilities.
        </motion.h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          {features.map((feature, i) => (
            <motion.div
              key={i}
              className="bg-slate-900 border border-slate-800 p-8 hover:border-orange-600/50 transition-colors"
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              whileHover={{ y: -4 }}
            >
              <div className="text-3xl mb-4">{feature.icon}</div>
              <h3 className="font-semibold text-slate-50 mb-3">{feature.title}</h3>
              <p className="text-slate-400 text-sm">{feature.desc}</p>
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
    { num: '01', name: 'Plan', role: 'Design' },
    { num: '02', name: 'Architect', role: 'Review' },
    { num: '03', name: 'Build', role: 'Implement' },
    { num: '04', name: 'Test', role: 'Verify' },
    { num: '05', name: 'Review', role: 'Inspect' },
    { num: '06', name: 'Ship', role: 'Deploy' },
  ]

  return (
    <section className="relative py-32 px-8 md:px-12 bg-slate-900">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-20"
        >
          <h2 className="font-serif text-4xl md:text-5xl mb-4 text-slate-50">
            Six gates. Evidence over confidence.
          </h2>
          <p className="text-slate-400 max-w-2xl">
            Every change goes through human approval before production. Every decision is backed by logs.
          </p>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {gates.map((gate, i) => (
            <motion.div
              key={i}
              className="bg-slate-800 border border-slate-700 p-6 text-center"
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              whileHover={{ borderColor: '#ea580c' }}
            >
              <div className="text-xs text-slate-500 mb-2">{gate.num}</div>
              <h3 className="font-semibold text-slate-50 mb-1">{gate.name}</h3>
              <p className="text-xs text-slate-500">{gate.role}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 7: COMPARISON
// ============================================================================

function ComparisonSection() {
  return (
    <section className="relative py-32 px-8 md:px-12 bg-slate-950">
      <div className="max-w-5xl mx-auto">
        <motion.h2
          className="font-serif text-4xl md:text-5xl mb-20 text-center text-slate-50"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          Ortho vs. traditional AI.
        </motion.h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <motion.div
            className="bg-slate-900 border border-slate-800 p-8"
            initial={{ opacity: 0, x: -10 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="font-serif text-xl mb-6 text-slate-50">Traditional AI</h3>
            <ul className="space-y-3">
              {['❌ Guesses without context', '❌ Forgets your project', '❌ Repeats mistakes', '❌ No architecture awareness', '❌ No verification'].map((item, i) => (
                <li key={i} className="text-slate-400 text-sm">
                  {item}
                </li>
              ))}
            </ul>
          </motion.div>

          <motion.div
            className="bg-slate-900 border border-slate-800 p-8"
            initial={{ opacity: 0, x: 10 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
          >
            <h3 className="font-serif text-xl mb-6 text-slate-50">Ortho</h3>
            <ul className="space-y-3">
              {['✓ Understands your codebase', '✓ Remembers decisions', '✓ Learns from patterns', '✓ Architecture-aware', '✓ Evidence-backed'].map((item, i) => (
                <li key={i} className="text-green-500/80 text-sm">
                  {item}
                </li>
              ))}
            </ul>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 8: ROADMAP
// ============================================================================

function RoadmapSection() {
  const phases = [
    { name: 'Foundation', status: 'COMPLETE' },
    { name: 'Reasoning', status: 'COMPLETE' },
    { name: 'Execution', status: 'IN PROGRESS' },
    { name: 'Optimization', status: 'COMING SOON' },
  ]

  return (
    <section className="relative py-32 px-8 md:px-12 bg-slate-900">
      <div className="max-w-5xl mx-auto">
        <motion.h2
          className="font-serif text-4xl md:text-5xl mb-4 text-slate-50"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          Four phases. Two shipped.
        </motion.h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-16">
          {phases.map((phase, i) => (
            <motion.div
              key={i}
              className="bg-slate-800 border border-slate-700 p-6 text-center"
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <h3 className="font-semibold text-slate-50 mb-4">{phase.name}</h3>
              <span
                className={`text-xs font-semibold px-3 py-1 ${
                  phase.status === 'COMPLETE'
                    ? 'bg-green-500/20 text-green-400'
                    : phase.status === 'IN PROGRESS'
                      ? 'bg-orange-500/20 text-orange-400'
                      : 'bg-slate-700 text-slate-400'
                }`}
              >
                {phase.status}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 9: FINAL CTA
// ============================================================================

function FinalCTASection() {
  return (
    <section className="relative py-32 px-8 md:px-12 bg-slate-950">
      <div className="max-w-4xl mx-auto text-center">
        <motion.h2
          className="font-serif text-4xl md:text-5xl leading-tight mb-12 text-slate-50"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          Ready to build software with AI that actually understands your project?
        </motion.h2>

        <motion.div
          className="flex flex-col md:flex-row gap-4 justify-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
        >
          <motion.button
            onClick={() =>
              window.location.href =
                'mailto:urbrain369@gmail.com?subject=Ortho%20Beta%20Access'
            }
            className="px-8 py-4 bg-orange-600 text-white font-semibold hover:bg-orange-500 transition-colors"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Get Started
          </motion.button>
          <motion.button
            onClick={() => window.open('https://github.com/urbra/ortho', '_blank')}
            className="px-8 py-4 border border-slate-700 text-slate-200 font-semibold hover:border-slate-600 hover:bg-slate-900/50 transition-all"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            View GitHub
          </motion.button>
        </motion.div>
      </div>
    </section>
  )
}

// ============================================================================
// SECTION 10: FOOTER
// ============================================================================

function Footer() {
  return (
    <footer className="border-t border-slate-800 py-12 px-8 md:px-12 bg-slate-950">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          <div>
            <h4 className="text-xs font-semibold text-slate-400 mb-4 uppercase tracking-wide">Product</h4>
            <ul className="space-y-2">
              <li>
                <a href="#features" className="text-sm text-slate-400 hover:text-slate-200">
                  Features
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-slate-400 hover:text-slate-200">
                  Pricing
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-slate-400 hover:text-slate-200">
                  Security
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-xs font-semibold text-slate-400 mb-4 uppercase tracking-wide">Docs</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-sm text-slate-400 hover:text-slate-200">
                  Documentation
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-slate-400 hover:text-slate-200">
                  API Reference
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-slate-400 hover:text-slate-200">
                  Guide
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-xs font-semibold text-slate-400 mb-4 uppercase tracking-wide">Community</h4>
            <ul className="space-y-2">
              <li>
                <a href="https://github.com/urbra/ortho" target="_blank" rel="noopener noreferrer" className="text-sm text-slate-400 hover:text-slate-200">
                  GitHub
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-slate-400 hover:text-slate-200">
                  Contact
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-slate-400 hover:text-slate-200">
                  Email
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-xs font-semibold text-slate-400 mb-4 uppercase tracking-wide">Legal</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-sm text-slate-400 hover:text-slate-200">
                  Privacy
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-slate-400 hover:text-slate-200">
                  Terms
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-slate-400 hover:text-slate-200">
                  Cookies
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-800 pt-8 text-center text-sm text-slate-500">
          <p>&copy; 2026 Ortho. Engineered with precision.</p>
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
    <main className="bg-slate-950 text-slate-50">
      <Navbar />
      <HeroSection />
      <ProblemsSection />
      <WorkflowSection />
      <FeaturesSection />
      <ASESSection />
      <ComparisonSection />
      <RoadmapSection />
      <FinalCTASection />
      <Footer />
    </main>
  )
}
