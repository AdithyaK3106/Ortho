'use client'

import { motion } from 'framer-motion'
import { Database, BookOpen, Layers, Cog, Zap } from 'lucide-react'

const pillars = [
  {
    title: 'Repository Intelligence',
    icon: Database,
    capabilities: ['Symbol extraction', 'Call graphs', 'Import analysis', 'Module detection', 'Incremental indexing'],
    description: 'Deep understanding of repository structure through AST analysis and graph construction.',
    color: 'blue',
  },
  {
    title: 'ContextHub',
    icon: BookOpen,
    capabilities: ['Artifact storage', 'BM25 search', 'Semantic search', 'Hybrid retrieval', 'Git metadata'],
    description: 'Persistent knowledge store with multi-modal search (full-text + semantic + hybrid RRF).',
    color: 'purple',
  },
  {
    title: 'Architectural Intelligence',
    icon: Layers,
    capabilities: ['Pattern detection', 'Layer extraction', 'Subsystem discovery', 'Impact analysis', 'Debt scoring'],
    description: 'Automatic detection of architecture styles, layers, subsystems, and dependency health.',
    color: 'blue',
  },
  {
    title: 'Engineering Orchestration',
    icon: Cog,
    capabilities: ['Workflow automation', 'Agent selection', 'Task planning', 'Approval gates', 'Evidence tracking'],
    description: 'Intelligent coordination of engineering workflows using ASES methodology.',
    color: 'purple',
  },
  {
    title: 'Token Optimization',
    icon: Zap,
    capabilities: ['Context ranking', 'Deduplication', 'Compression', 'Budget management', 'Quality logging'],
    description: 'Maximum engineering value per token through intelligent context assembly.',
    color: 'blue',
  },
]

const colorMap = {
  blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/20',
  purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/20',
}

export function Pillars() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6 },
    },
  }

  return (
    <section id="features" className="py-20 px-6 relative">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-6">Five Pillars of Intelligence</h2>
          <p className="text-xl text-text-secondary max-w-2xl">
            Each pillar is independently useful but more powerful together. Choose what you need.
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {pillars.map((pillar, i) => {
            const colorClass = colorMap[pillar.color as keyof typeof colorMap]
            return (
              <motion.div
                key={i}
                variants={itemVariants}
                whileHover={{ translateY: -4 }}
                className={`glass-effect p-6 rounded-lg border ${colorClass} group hover:bg-white/5 transition-all`}
              >
                {/* Icon */}
                <div className="mb-4 inline-block p-3 bg-white/5 rounded-lg group-hover:bg-white/10 transition-colors">
                  <pillar.icon className="w-6 h-6" />
                </div>

                {/* Title */}
                <h3 className="text-lg font-semibold mb-3">{pillar.title}</h3>

                {/* Description */}
                <p className="text-text-secondary text-sm mb-4">{pillar.description}</p>

                {/* Capabilities */}
                <div className="space-y-2">
                  {pillar.capabilities.map((cap, j) => (
                    <div key={j} className="flex items-center gap-2 text-sm text-text-secondary">
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                      {cap}
                    </div>
                  ))}
                </div>
              </motion.div>
            )
          })}
        </motion.div>
      </div>
    </section>
  )
}
