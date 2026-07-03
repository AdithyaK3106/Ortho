'use client'

import { motion } from 'framer-motion'
import { CheckCircle, Clock, Zap } from 'lucide-react'

const phases = [
  {
    phase: 'Phase 1',
    title: 'Foundation',
    status: 'In Progress',
    icon: CheckCircle,
    color: 'emerald',
    items: [
      '✓ Monorepo & Poetry setup',
      '✓ Shared types (TS + Python)',
      '✓ SQLite storage layer',
      '✓ Python AST adapter',
      '✓ Symbol & import extraction',
      '✓ Call graph builder',
      '✓ Incremental indexing',
      '✓ ContextHub storage',
      '✓ BM25 & semantic search',
    ],
  },
  {
    phase: 'Phase 2',
    title: 'Reasoning',
    status: 'In Progress',
    icon: Clock,
    color: 'blue',
    items: [
      '✓ Architecture detection',
      '✓ Layer extraction',
      '✓ Subsystem discovery',
      '✓ Impact analysis',
      '✓ Debt scoring',
      '✓ ADR cross-reference',
      '→ TypeScript adapter',
      '→ Circular dependency detection',
    ],
  },
  {
    phase: 'Phase 3',
    title: 'Execution',
    status: 'Planned',
    icon: Zap,
    color: 'purple',
    items: [
      '→ Intent routing (semantic-router)',
      '→ Workflow orchestration',
      '→ Agent registry & skills',
      '→ Selector engine',
      '→ Human approval gates',
      '→ Evidence collection',
      '→ ortho run command',
      '→ Workflow state persistence',
    ],
  },
  {
    phase: 'Phase 4',
    title: 'Optimization',
    status: 'Planned',
    icon: Zap,
    color: 'purple',
    items: [
      '→ Token budget management',
      '→ Context ranking & reranking',
      '→ Semantic deduplication',
      '→ Graph expansion',
      '→ Compression strategies',
      '→ Model routing',
      '→ Quality logging',
    ],
  },
]

export function Roadmap() {
  return (
    <section id="roadmap" className="py-20 px-6">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <h2 className="text-4xl font-bold mb-6">Development Roadmap</h2>
          <p className="text-xl text-text-secondary max-w-2xl">
            Building Ortho phase by phase, with rigorous ASES discipline.
          </p>
        </motion.div>

        {/* Timeline */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {phases.map((phase, i) => {
            const Icon = phase.icon
            const isCompleted = phase.color === 'emerald'

            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: i * 0.1 }}
                viewport={{ once: true }}
                className={`glass-effect p-6 rounded-lg border-l-4 ${
                  phase.color === 'emerald'
                    ? 'border-emerald-500'
                    : phase.color === 'blue'
                      ? 'border-blue-500'
                      : 'border-purple-500'
                }`}
              >
                {/* Header */}
                <div className="flex items-center gap-3 mb-4">
                  <Icon className={`w-5 h-5 ${
                    phase.color === 'emerald' ? 'text-emerald-500' : 'text-text-tertiary'
                  }`} />
                  <div>
                    <div className="text-xs font-mono font-semibold text-text-tertiary uppercase">
                      {phase.phase}
                    </div>
                    <h3 className="text-lg font-semibold">{phase.title}</h3>
                  </div>
                </div>

                {/* Status badge */}
                <div className="inline-block px-3 py-1 bg-white/5 rounded-full text-xs font-medium mb-4 text-text-tertiary">
                  {phase.status}
                </div>

                {/* Items */}
                <div className="space-y-2">
                  {phase.items.map((item, j) => (
                    <motion.div
                      key={j}
                      initial={{ opacity: 0, x: -10 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.4, delay: j * 0.05 }}
                      viewport={{ once: true }}
                      className="text-sm text-text-secondary flex items-start gap-2"
                    >
                      <span className="text-xs mt-0.5">{item.startsWith('✓') ? '✓' : '→'}</span>
                      <span className={item.startsWith('✓') ? 'line-through opacity-50' : ''}>
                        {item.replace(/^[✓→]\s*/, '')}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Timeline legend */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          viewport={{ once: true }}
          className="mt-12 flex flex-wrap justify-center gap-6 text-sm text-text-secondary"
        >
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
            Completed
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-500" />
            In Progress
          </div>
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-purple-500" />
            Planned
          </div>
        </motion.div>

        {/* Estimated timeline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          viewport={{ once: true }}
          className="mt-12 text-center text-text-secondary"
        >
          <p>Phase 1 (Weeks 1–8) | Phase 2 (Weeks 9–14) | Phase 3 (Weeks 15–22) | Phase 4 (Weeks 23–28)</p>
        </motion.div>
      </div>
    </section>
  )
}
