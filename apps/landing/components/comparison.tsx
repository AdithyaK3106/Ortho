'use client'

import { motion } from 'framer-motion'
import { CheckCircle, XCircle } from 'lucide-react'

const features = [
  'Repository Understanding',
  'Persistent Memory',
  'Architecture Awareness',
  'Impact Analysis',
  'Workflow Enforcement',
  'Evidence Collection',
  'Token Optimization',
  'Human Approval Gates',
  'ASES Compliance',
]

export function Comparison() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <h2 className="text-4xl font-bold mb-6">Why Ortho is Different</h2>
          <p className="text-xl text-text-secondary max-w-2xl">
            Traditional AI coding assistants vs. Ortho as your engineering brain.
          </p>
        </motion.div>

        {/* Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="glass-dark rounded-lg overflow-hidden border border-white/10"
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              {/* Header */}
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-6 py-4 text-left text-sm font-semibold text-text-secondary">Capability</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold">Traditional AI</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-blue-400">Ortho</th>
                </tr>
              </thead>

              {/* Body */}
              <tbody>
                {features.map((feature, i) => (
                  <motion.tr
                    key={i}
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    transition={{ duration: 0.5, delay: i * 0.05 }}
                    viewport={{ once: true }}
                    className={i % 2 === 0 ? 'bg-white/5' : 'bg-transparent'}
                  >
                    <td className="px-6 py-4 text-sm font-medium border-b border-white/5">{feature}</td>
                    <td className="px-6 py-4 text-center border-b border-white/5">
                      <XCircle className="w-5 h-5 mx-auto text-text-tertiary opacity-40" />
                    </td>
                    <td className="px-6 py-4 text-center border-b border-white/5">
                      <CheckCircle className="w-5 h-5 mx-auto text-emerald-500" />
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Bottom note */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          viewport={{ once: true }}
          className="mt-8 text-center"
        >
          <p className="text-text-secondary">
            Ortho isn't a replacement for Claude or any LLM. It's the intelligence layer that makes LLMs more effective.
          </p>
        </motion.div>
      </div>
    </section>
  )
}
