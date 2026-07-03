'use client'

import { motion } from 'framer-motion'
import { ArrowDown } from 'lucide-react'

const steps = [
  { label: 'Developer Intent', desc: 'User request or command' },
  { label: 'Repository Intelligence', desc: 'Scan & analyze codebase' },
  { label: 'Context Assembly', desc: 'Retrieve relevant knowledge' },
  { label: 'Architectural Analysis', desc: 'Understand system patterns' },
  { label: 'Workflow Selection', desc: 'Choose engineering process' },
  { label: 'Context Delivery', desc: 'Assemble optimized prompt' },
  { label: 'LLM Generation', desc: 'AI executes with context' },
  { label: 'Evidence Collection', desc: 'Gather verification proof' },
  { label: 'Human Approval', desc: 'Final authorization gate' },
]

export function ArchitectureSection() {
  return (
    <section id="architecture" className="py-20 px-6">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-6">System Architecture</h2>
          <p className="text-xl text-text-secondary max-w-2xl">
            Every developer request flows through intelligent layers of analysis and context assembly.
          </p>
        </motion.div>

        {/* Flow diagram */}
        <div className="space-y-4">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              viewport={{ once: true }}
              className="flex items-center gap-6 group"
            >
              {/* Card */}
              <div className="flex-1 glass-effect p-6 rounded-lg hover:bg-white/10 transition-all">
                <h3 className="font-semibold mb-1 text-lg">{step.label}</h3>
                <p className="text-text-secondary text-sm">{step.desc}</p>
              </div>

              {/* Arrow */}
              {i < steps.length - 1 && (
                <div className="hidden md:flex flex-col items-center">
                  <ArrowDown className="w-5 h-5 text-text-tertiary animate-pulse" />
                </div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Result */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          viewport={{ once: true }}
          className="mt-12 glass-dark p-8 rounded-2xl text-center border-t-2 border-emerald-500/30"
        >
          <p className="text-2xl font-bold text-emerald-400">
            → High-Quality Engineering Result with Evidence and Confidence
          </p>
        </motion.div>
      </div>
    </section>
  )
}
