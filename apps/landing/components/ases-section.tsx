'use client'

import { motion } from 'framer-motion'
import { CheckCircle } from 'lucide-react'

const gates = [
  { gate: 'PLAN', label: 'Planning', desc: 'Specifications and acceptance criteria' },
  { gate: 'ARCHITECT', label: 'Architecture', desc: 'Design review and decisions' },
  { gate: 'BUILD', label: 'Implementation', desc: 'Code and atomic tasks' },
  { gate: 'TEST', label: 'Testing', desc: 'Coverage and verification' },
  { gate: 'REVIEW', label: 'Review', desc: 'Code quality and standards' },
  { gate: 'SHIP', label: 'Approval', desc: 'Final authorization and merge' },
]

const principles = [
  'Evidence Over Confidence',
  'Human Approval Always Required',
  'Deterministic Workflows',
  'Traceable Decisions',
  'Artifact-Driven Process',
  'No Automation Without Understanding',
]

export function ASESSection() {
  return (
    <section className="py-20 px-6 relative">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-6">
            ASES: AI-Assisted <span className="gradient-text">Software Engineering</span>
          </h2>
          <p className="text-xl text-text-secondary max-w-2xl">
            A methodology for building software with AI that prioritizes engineering rigor, verification, and human judgment.
          </p>
        </motion.div>

        {/* Six gates */}
        <div className="mb-16">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="grid md:grid-cols-3 lg:grid-cols-6 gap-4"
          >
            {gates.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.05 }}
                viewport={{ once: true }}
                className="glass-effect p-4 rounded-lg text-center hover:bg-white/10 transition-all"
              >
                <div className="text-sm font-mono font-semibold text-blue-400 mb-2">{item.gate}</div>
                <h3 className="font-semibold text-sm mb-1">{item.label}</h3>
                <p className="text-xs text-text-tertiary">{item.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* Principles */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="glass-dark p-12 rounded-2xl"
        >
          <h3 className="text-2xl font-bold mb-8">Core Principles</h3>
          <div className="grid md:grid-cols-2 gap-6">
            {principles.map((principle, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: i * 0.05 }}
                viewport={{ once: true }}
                className="flex items-center gap-3"
              >
                <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                <span className="font-medium">{principle}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Bottom message */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          viewport={{ once: true }}
          className="mt-12 text-center"
        >
          <p className="text-lg text-text-secondary">
            ASES is both how we build Ortho and the methodology Ortho will eventually orchestrate.
          </p>
          <p className="text-sm text-text-tertiary mt-4">
            The product eats its own process.
          </p>
        </motion.div>
      </div>
    </section>
  )
}
