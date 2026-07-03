'use client'

import { motion } from 'framer-motion'
import { ArrowRight, Github, Zap } from 'lucide-react'

const badges = [
  { label: 'Open Source', icon: Github },
  { label: 'Local First', icon: Zap },
  { label: 'Model Agnostic', icon: '🤖' },
  { label: 'Evidence Driven', icon: '✓' },
]

export function Hero() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.8, ease: 'easeOut' },
    },
  }

  return (
    <section className="relative min-h-screen pt-32 pb-20 flex items-center justify-center overflow-hidden">
      {/* Background grid */}
      <div className="absolute inset-0 bg-grid-pattern bg-grid-size opacity-5" />

      {/* Gradient orb */}
      <div className="absolute top-20 left-1/2 -translate-x-1/2 w-96 h-96 bg-gradient-to-r from-blue-500/30 to-purple-500/30 rounded-full blur-3xl animate-pulse" />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 max-w-5xl mx-auto px-6 text-center"
      >
        {/* Badges */}
        <motion.div
          variants={itemVariants}
          className="flex flex-wrap justify-center gap-3 mb-8"
        >
          {badges.map((badge, i) => (
            <motion.div
              key={i}
              whileHover={{ scale: 1.05 }}
              className="glass-effect px-4 py-2 rounded-full text-sm font-medium text-text-secondary flex items-center gap-2"
            >
              {typeof badge.icon === 'string' ? (
                <span>{badge.icon}</span>
              ) : (
                <badge.icon className="w-4 h-4" />
              )}
              {badge.label}
            </motion.div>
          ))}
        </motion.div>

        {/* Main headline */}
        <motion.h1 variants={itemVariants} className="text-6xl lg:text-7xl font-bold mb-6 leading-tight">
          The <span className="gradient-text">Engineering Brain</span>
          <br />
          for AI Development
        </motion.h1>

        {/* Subheading */}
        <motion.p
          variants={itemVariants}
          className="text-xl text-text-secondary mb-12 max-w-2xl mx-auto leading-relaxed"
        >
          Ortho provides deep repository understanding, persistent engineering memory, and intelligent workflow orchestration. The LLM becomes a more powerful tool with Ortho as its context engine.
        </motion.p>

        {/* CTAs */}
        <motion.div
          variants={itemVariants}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16"
        >
          <button className="px-8 py-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-semibold flex items-center gap-2 transition-all hover:shadow-lg hover:shadow-blue-500/50 group">
            Get Started
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
          <a
            href="https://github.com/urbra/ortho"
            className="px-8 py-4 glass-effect rounded-lg font-semibold flex items-center gap-2 hover:bg-white/10 transition-all"
          >
            <Github className="w-5 h-5" />
            View on GitHub
          </a>
        </motion.div>

        {/* Hero visualization (placeholder for animated diagram) */}
        <motion.div
          variants={itemVariants}
          className="relative mt-20 pt-20 border-t border-border"
        >
          <div className="glass-dark p-8 rounded-2xl">
            <div className="space-y-4 text-left">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                <code className="text-sm text-text-secondary">$ ortho scan</code>
              </div>
              <div className="flex items-center gap-3 ml-4">
                <span className="text-text-tertiary">→</span>
                <span className="text-text-secondary text-sm">Analyzing 2,847 symbols in 156 files...</span>
              </div>
              <div className="flex items-center gap-3 ml-4">
                <span className="text-text-tertiary">→</span>
                <span className="text-text-secondary text-sm">Building call graph and import edges...</span>
              </div>
              <div className="flex items-center gap-3 ml-4">
                <span className="text-text-tertiary">→</span>
                <span className="text-emerald-500 text-sm">✓ Repository indexed in 2.3s</span>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </section>
  )
}
