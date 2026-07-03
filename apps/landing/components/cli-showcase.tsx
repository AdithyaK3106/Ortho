'use client'

import { motion } from 'framer-motion'
import { Zap } from 'lucide-react'

const commands = [
  { cmd: '$ ortho init', desc: 'Initialize Ortho in your project' },
  { cmd: '$ ortho scan', desc: 'Scan and index repository' },
  { cmd: '$ ortho analyze --impact src/auth/service.py', desc: 'Blast radius analysis' },
  { cmd: '$ ortho context search "authentication flow"', desc: 'Semantic search' },
  { cmd: '$ ortho run "add rate limiting to API"', desc: 'Execute full workflow' },
]

export function CLIShowcase() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <h2 className="text-4xl font-bold mb-6 flex items-center gap-3">
            <Zap className="w-8 h-8 text-blue-500" />
            Command Line Interface
          </h2>
          <p className="text-xl text-text-secondary">
            Everything accessible from the terminal. Simple, powerful, scriptable.
          </p>
        </motion.div>

        {/* Terminal */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="glass-dark rounded-xl overflow-hidden border border-white/10"
        >
          {/* Header */}
          <div className="bg-surface-secondary px-6 py-4 border-b border-white/10 flex items-center gap-3">
            <div className="flex gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full" />
              <div className="w-3 h-3 bg-yellow-500 rounded-full" />
              <div className="w-3 h-3 bg-green-500 rounded-full" />
            </div>
            <span className="text-text-tertiary text-sm ml-auto">ortho</span>
          </div>

          {/* Content */}
          <div className="p-8 font-mono text-sm space-y-6">
            {commands.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                viewport={{ once: true }}
              >
                <div className="text-blue-400 mb-2 flex items-center gap-2">
                  <span className="text-text-tertiary">›</span>
                  {item.cmd}
                </div>
                <div className="text-text-tertiary text-xs ml-4"># {item.desc}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
