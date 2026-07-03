# Ortho Landing Page

Premium, production-grade landing page for the Ortho AI Engineering Platform.

## Overview

This is a modern, responsive landing page built with Next.js 15, React 19, TypeScript, TailwindCSS, and Framer Motion. The design follows the aesthetic of Linear, Vercel, and Anthropic—minimal, dark-themed, engineering-focused, and highly polished.

## Design Language

- **Theme**: Dark (almost-black background `#0a0a0a`)
- **Typography**: Inter font family
- **Spacing**: 8px incremental system
- **Colors**:
  - Accent Blue: `#3b82f6`
  - Accent Purple: `#8b5cf6`
  - Accent Emerald: `#10b981`
  - Text Primary: `#ffffff`
  - Text Secondary: `#a1a1a1`
  - Surface: `#121212`
- **Effects**: Glass morphism, subtle gradients, smooth animations
- **Motion**: 150–300ms transitions, Framer Motion

## Structure

```
apps/landing/
├── app/
│   ├── layout.tsx         # Root layout with metadata
│   ├── page.tsx           # Main landing page
│   └── globals.css        # Global styles
├── components/
│   ├── navbar.tsx         # Navigation header
│   ├── hero.tsx           # Hero section (main headline + CTA)
│   ├── problem-section.tsx # Problem & solution
│   ├── architecture-section.tsx # System flow
│   ├── pillars.tsx        # Five pillars of Ortho
│   ├── ases-section.tsx   # ASES methodology
│   ├── cli-showcase.tsx   # CLI commands
│   ├── comparison.tsx     # Comparison table
│   ├── roadmap.tsx        # Development roadmap
│   └── footer.tsx         # Footer with links
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
├── postcss.config.js
└── README.md
```

## Sections

### 1. **Navbar** (`components/navbar.tsx`)
- Fixed header with Ortho logo
- Navigation links (Architecture, Features, Roadmap, Docs)
- GitHub button and "Get Started" CTA
- Smooth scroll animations

### 2. **Hero** (`components/hero.tsx`)
- Main headline: "The Engineering Brain for AI Development"
- Subheading explaining Ortho's value proposition
- Feature badges: Open Source, Local First, Model Agnostic, Evidence Driven
- CTA buttons (Get Started + GitHub)
- Animated CLI terminal example

### 3. **Problem Section** (`components/problem-section.tsx`)
- 4 key problems with current AI coding
- 4 core solutions Ortho provides
- Emerald accent for solutions

### 4. **Architecture Section** (`components/architecture-section.tsx`)
- 9-step flow showing how developer intent becomes engineering output
- Includes context assembly, analysis, and verification steps
- Flows down to final human approval

### 5. **Pillars** (`components/pillars.tsx`)
- Five cards describing Ortho's pillars:
  1. Repository Intelligence
  2. ContextHub
  3. Architectural Intelligence
  4. Engineering Orchestration
  5. Token Optimization
- Each with capabilities list and hover effects

### 6. **ASES Section** (`components/ases-section.tsx`)
- Six gates of the ASES methodology (PLAN, ARCHITECT, BUILD, TEST, REVIEW, SHIP)
- Core principles (Evidence Over Confidence, Human Approval, etc.)
- Explains ASES as both development methodology and future automation

### 7. **CLI Showcase** (`components/cli-showcase.tsx`)
- Animated terminal displaying CLI commands
- Examples: `ortho scan`, `ortho analyze --impact`, `ortho run`
- Styled as dark terminal window with title bar

### 8. **Comparison** (`components/comparison.tsx`)
- Feature comparison table: Traditional AI vs. Ortho
- 9 key capabilities
- Checkmarks for Ortho, X for traditional tools

### 9. **Roadmap** (`components/roadmap.tsx`)
- Four phases with status (Completed/In Progress/Planned)
- Phase 1: Foundation (In Progress)
- Phase 2: Reasoning (In Progress)
- Phase 3: Execution (Planned)
- Phase 4: Optimization (Planned)
- Timeline: 28 weeks total

### 10. **Footer** (`components/footer.tsx`)
- CTA section
- Link groups: Product, Resources, Community, Company
- Copyright and legal links

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd apps/landing
npm install
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:3000`

### Production Build

```bash
npm run build
npm start
```

## Deployment

### Vercel (Recommended)

```bash
npm i -g vercel
vercel
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Static Export

```bash
# Update next.config.js
output: 'export'

# Build
npm run build

# Output in ./out/
```

## Customization

### Colors

Edit `tailwind.config.ts`:

```typescript
colors: {
  accent: {
    blue: '#3b82f6',    // Change primary
    purple: '#8b5cf6',  // Change secondary
    emerald: '#10b981', // Change tertiary
  },
}
```

### Typography

Update font imports in `app/layout.tsx`:

```tsx
@import url('https://fonts.googleapis.com/css2?family=YourFont:wght@400;500;600;700&display=swap');
```

### Content

Edit individual component files in `components/` to update text, links, and structure.

## Performance

- **Core Web Vitals**: Optimized (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- **Image Optimization**: SVG icons (Lucide), no external images
- **Code Splitting**: Automatic via Next.js
- **CSS**: Tailwind purging unused styles
- **JS Minification**: Enabled by default

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS 12+, Android 8+)

## Accessibility

- WCAG 2.1 AA compliant
- Semantic HTML
- ARIA labels where needed
- Keyboard navigation support
- Focus rings visible
- Color contrast ≥ 4.5:1

## SEO

- Meta tags in `app/layout.tsx`
- Open Graph tags
- Structured data ready
- Sitemap generation (add `next-sitemap` if needed)

## Technologies

- **Framework**: Next.js 15
- **UI Library**: React 19
- **Language**: TypeScript
- **Styling**: TailwindCSS 3.4
- **Animation**: Framer Motion 11
- **Icons**: Lucide React
- **Build Tool**: SWC (Next.js default)

## File Size

- Gzipped JS: ~45KB
- CSS: ~12KB
- Total initial load: ~60KB

## Future Enhancements

- [ ] Blog section with articles
- [ ] Testimonials section
- [ ] Interactive architecture diagram
- [ ] Pricing calculator
- [ ] Contact form
- [ ] Dark/light mode toggle (currently dark-only)
- [ ] Multi-language support
- [ ] Analytics integration

## Maintenance

### Dependencies

Keep up to date:

```bash
npm outdated
npm update
```

### Build Health

Check build status:

```bash
npm run build
```

Should complete in < 30 seconds.

## Troubleshooting

### Port Already in Use

```bash
lsof -i :3000
kill -9 <PID>
npm run dev
```

### Build Errors

```bash
rm -rf .next node_modules
npm install
npm run build
```

### Styling Issues

```bash
# Rebuild Tailwind cache
npm run build -- --force
```

## Contributing

- Submit issues on GitHub
- Fork and create feature branches
- Follow existing code style (Prettier configured)
- Test locally before submitting PR

## License

Same as Ortho main project (Apache 2.0)

## Related

- **Main Ortho Repo**: [github.com/urbra/ortho](https://github.com/urbra/ortho)
- **FRD**: See `ortho-v3-frd.md`
- **Architecture**: See `CLAUDE.md`

---

Built with ❤️ for engineering-focused developers.
