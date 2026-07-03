'use client'

import { motion } from 'framer-motion'
import { Github, ArrowRight } from 'lucide-react'
import Link from 'next/link'

export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t border-border py-16 px-6">
      <div className="max-w-7xl mx-auto">
        {/* CTA Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mb-16 text-center"
        >
          <h2 className="text-3xl font-bold mb-6">Ready to build better with AI?</h2>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="px-8 py-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-semibold flex items-center gap-2 transition-all hover:shadow-lg hover:shadow-blue-500/50 group">
              Get Started
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <a
              href="https://github.com/urbra/ortho"
              className="px-8 py-4 glass-effect rounded-lg font-semibold flex items-center gap-2 hover:bg-white/10 transition-all"
            >
              <Github className="w-5 h-5" />
              Star on GitHub
            </a>
          </div>
        </motion.div>

        {/* Links */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="grid md:grid-cols-4 gap-12 mb-12 py-12 border-y border-border"
        >
          {/* Product */}
          <div>
            <h4 className="font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li><a href="#features" className="hover:text-text-primary transition">Features</a></li>
              <li><a href="#architecture" className="hover:text-text-primary transition">Architecture</a></li>
              <li><a href="#roadmap" className="hover:text-text-primary transition">Roadmap</a></li>
              <li><a href="#" className="hover:text-text-primary transition">Pricing</a></li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li><a href="#" className="hover:text-text-primary transition">Documentation</a></li>
              <li><a href="#" className="hover:text-text-primary transition">API Reference</a></li>
              <li><a href="#" className="hover:text-text-primary transition">Examples</a></li>
              <li><a href="#" className="hover:text-text-primary transition">FAQ</a></li>
            </ul>
          </div>

          {/* Community */}
          <div>
            <h4 className="font-semibold mb-4">Community</h4>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li><a href="https://github.com/urbra/ortho" className="hover:text-text-primary transition">GitHub</a></li>
              <li><a href="#" className="hover:text-text-primary transition">Discussions</a></li>
              <li><a href="#" className="hover:text-text-primary transition">Issues</a></li>
              <li><a href="#" className="hover:text-text-primary transition">Contributing</a></li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-semibold mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li><a href="#" className="hover:text-text-primary transition">About</a></li>
              <li><a href="#" className="hover:text-text-primary transition">Blog</a></li>
              <li><a href="#" className="hover:text-text-primary transition">Status</a></li>
              <li><a href="#" className="hover:text-text-primary transition">Contact</a></li>
            </ul>
          </div>
        </motion.div>

        {/* Bottom */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-text-tertiary"
        >
          <div>© {currentYear} Ortho. Open source under Apache 2.0 license.</div>
          <div className="flex items-center gap-6">
            <a href="#" className="hover:text-text-primary transition">Privacy</a>
            <a href="#" className="hover:text-text-primary transition">Terms</a>
            <a href="#" className="hover:text-text-primary transition">Security</a>
          </div>
        </motion.div>
      </div>
    </footer>
  )
}
