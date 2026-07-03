import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Ortho - AI Engineering Platform',
  description: 'Repository intelligence, context assembly, and engineering orchestration. The engineering brain for AI-assisted development.',
  keywords: ['AI', 'Engineering', 'Repository Intelligence', 'Code Analysis', 'LLM'],
  viewport: 'width=device-width, initial-scale=1',
  openGraph: {
    title: 'Ortho - AI Engineering Platform',
    description: 'Repository intelligence, context assembly, and engineering orchestration.',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <style>{`
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
          html {
            scroll-behavior: smooth;
          }
        `}</style>
      </head>
      <body className="bg-background text-text-primary font-sans antialiased">
        <NoHydrationWarning>
          {children}
        </NoHydrationWarning>
      </body>
    </html>
  )
}

function NoHydrationWarning({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
