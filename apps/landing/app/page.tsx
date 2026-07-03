/**
 * REDESIGNED LANDING PAGE
 *
 * Philosophy:
 * - Premium, cinematic, minimal
 * - 60% less text (one idea per section)
 * - Massive typography + whitespace
 * - Asymmetrical layouts
 * - GPU-accelerated animations (transform + opacity only)
 * - Framer Motion best practices
 * - 120 FPS target
 */

import dynamic from 'next/dynamic'

// Lazy load redesigned page with dynamic import for performance
const HomeRedesignedDynamic = dynamic(() => import('./page-redesigned'), {
  loading: () => <div className="h-screen bg-background" />,
})

export default function Home() {
  return <HomeRedesignedDynamic />
}
