'use client'

import { motion } from 'framer-motion'
import { AlertCircle, Brain, Database, Zap } from 'lucide-react'

const problems = [
  {
    icon: Database,
    title: 'AI Forgets Context',
    description: 'Without repository understanding, every prompt starts from scratch. No continuity, no institutional memory.',
    color: 'blue',
  },
  {
    icon: Brain,
    title: 'Hallucinates Architecture',
    description: 'LLMs can invent patterns that don\'t exist. They make confident statements about structure they\'ve never seen.',
    color: 'purple',
  },
  {
    icon: Zap,
    title: 'Repeats Mistakes',
    description: 'Without analyzing what failed before, the same bugs resurface. Each task starts without learned patterns.',
    color: 'blue',
  },
  {
    icon: AlertCircle,
    title: 'No Engineering Memory',
    description: 'Decisions, ADRs, and lessons learned vanish. Next time? Same decisions get made again.',
    color: 'purple',
  },
]

const solutions = [
  { label: 'Deep Repository Scanning', desc: 'Symbols, imports, call graphs, architecture patterns' },
  { label: 'Persistent Context Hub', desc: 'Every artifact, decision, and lesson stored and searchable' },
  { label: 'Architectural Intelligence', desc: 'Auto-detect patterns, dependencies, blast radius, technical debt' },
  { label: 'Evidence-Driven Workflows', desc: 'Every decision backed by test output, verification, human approval' },
]

export function ProblemSection() {
  return (
    <section className="py-20 px-6 relative">
      <div className="max-w-7xl mx-auto">
        {/* Problem Grid */}
        <div className="mb-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="mb-12"
          >
            <h2 className="text-4xl lg:text-5xl font-bold mb-6">The Problem with AI Coding Today</h2>
            <p className="text-xl text-text-secondary max-w-2xl">
              LLMs are powerful at generation, but they lack the engineering intelligence to generate correctly.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6 mb-12">
            {problems.map((problem, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: i * 0.1 }}
                viewport={{ once: true }}
                className="glass-effect p-6 rounded-lg hover:bg-white/10 transition-all"
              >
                <problem.icon className="w-6 h-6 mb-4 text-blue-500" />
                <h3 className="text-lg font-semibold mb-2">{problem.title}</h3>
                <p className="text-text-secondary">{problem.description}</p>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Solution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="glass-dark p-12 rounded-2xl border-t border-emerald-500/20"
        >
          <h3 className="text-3xl font-bold mb-8 flex items-center gap-3">
            <span className="text-emerald-500">✓</span> How Ortho Solves It
          </h3>

          <div className="grid md:grid-cols-2 gap-8">
            {solutions.map((solution, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: i * 0.1 }}
                viewport={{ once: true }}
              >
                <div className="flex items-start gap-4">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full mt-2 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">{solution.label}</h4>
                    <p className="text-text-secondary text-sm">{solution.desc}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
