# Ortho Landing Page — File Index

Quick navigation guide to all landing page files.

## 📂 Directory Structure

```
apps/landing/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # Root HTML template, metadata, fonts
│   ├── page.tsx                 # Main landing page component
│   └── globals.css              # Global styles, utilities, animations
│
├── components/                   # Reusable UI components
│   ├── navbar.tsx               # Header + navigation (fixed)
│   ├── hero.tsx                 # Hero section (headline + CTA)
│   ├── problem-section.tsx      # Problems + solutions section
│   ├── architecture-section.tsx # 9-step architecture flow
│   ├── pillars.tsx              # Five pillars cards
│   ├── ases-section.tsx         # ASES methodology section
│   ├── cli-showcase.tsx         # Terminal showcase section
│   ├── comparison.tsx           # Feature comparison table
│   ├── roadmap.tsx              # Development roadmap section
│   └── footer.tsx               # Footer with links
│
├── public/                       # Static assets (empty, using SVG icons)
│
├── Configuration Files
│   ├── package.json             # Dependencies, scripts, metadata
│   ├── tsconfig.json            # TypeScript configuration
│   ├── next.config.js           # Next.js build configuration
│   ├── tailwind.config.ts       # Tailwind CSS theme (colors, fonts)
│   ├── postcss.config.js        # PostCSS + Tailwind setup
│   └── .eslintrc.json           # ESLint rules for code quality
│
├── Documentation
│   ├── README.md                # Project overview, setup, deployment
│   ├── QUICKSTART.md            # 60-second setup + common edits
│   ├── DEPLOYMENT.md            # Deploy to Vercel, Docker, etc.
│   ├── INDEX.md                 # This file
│   └── .gitignore               # Git exclusions
```

---

## 📄 File Descriptions

### Core App Files

#### `app/layout.tsx`
- Root HTML wrapper for entire app
- Sets up metadata (title, description, OG tags)
- Imports Google Fonts (Inter)
- Configures HTML language and body styling
- No need to edit unless changing global metadata

#### `app/page.tsx`
- Main landing page component
- Imports all sections from `components/`
- Stitches them together in order
- This is what renders at `/`
- Edit to add/remove sections or change order

#### `app/globals.css`
- Global CSS across entire site
- Tailwind directives (@tailwind base/components/utilities)
- Utility classes (.gradient-text, .glass-effect, etc.)
- Animations (@keyframes for fade-in, slide-up, glow-pulse)
- Scrollbar styling
- Typography base styles

### Components (10 sections)

Each component is self-contained and independent. All use:
- Framer Motion for animations
- React hooks for interactivity
- Tailwind utility classes for styling
- Lucide icons for icons

#### `components/navbar.tsx`
- Fixed header that stays at top
- Logo on left, nav links center, CTA on right
- Responsive (links hidden on mobile)
- Smooth slide-down animation on load
- All internal links use `href="#section-id"` for smooth scroll

**Edit**: Update links array at top, change logo text

#### `components/hero.tsx`
- Main headline section
- Feature badges (open source, local first, etc.)
- Large heading with gradient text
- Subheading explaining value proposition
- Two CTA buttons
- Animated terminal example showing `ortho scan`
- Background grid pattern + animated gradient orb

**Edit**: Change headline, subheading, CTA text, badges

#### `components/problem-section.tsx`
- 4 problems with current AI coding
- 4 solutions Ortho provides
- Grid layout with icons
- Glass effect cards with hover animations

**Edit**: Update `problems` and `solutions` arrays

#### `components/architecture-section.tsx`
- 9-step flow from developer intent to result
- Shows: intent → scanning → context → analysis → selection → assembly → LLM → evidence → approval
- Vertical timeline with animated arrows

**Edit**: Update `steps` array to change flow

#### `components/pillars.tsx`
- 5 cards (one per pillar)
- Each has icon, title, description, capabilities list
- Hover scale effect
- Color-coded (blue/purple alternating)

**Edit**: Update `pillars` array with new pillar info

#### `components/ases-section.tsx`
- 6 gates grid (PLAN, ARCHITECT, BUILD, TEST, REVIEW, SHIP)
- Core principles listed (6 items)
- Explains ASES philosophy

**Edit**: Update `gates` and `principles` arrays

#### `components/cli-showcase.tsx`
- Terminal window styling
- MacOS-like title bar with stop/minimize/maximize buttons
- Example commands listed
- Monospace font (Fira Code)

**Edit**: Update `commands` array with new CLI examples

#### `components/comparison.tsx`
- Feature comparison table
- Traditional AI vs. Ortho
- Checkmarks/X marks for each capability
- 9 rows of features

**Edit**: Update `features` array, change column 1/2 text

#### `components/roadmap.tsx`
- 4 phase cards (Phase 1–4)
- Color-coded by status (emerald/blue/purple)
- Phase 1: Completed items (strikethrough)
- Phase 2–4: Planned items (arrows)
- Timeline at bottom

**Edit**: Update `phases` array to reflect current status

#### `components/footer.tsx`
- CTA section at top
- 4 link groups (Product, Resources, Community, Company)
- Copyright and legal links
- Responsive layout

**Edit**: Update link groups, change CTA text

### Configuration Files

#### `package.json`
- Project metadata (name, version, description)
- Scripts: `dev`, `build`, `start`, `lint`
- Dependencies: next, react, react-dom, framer-motion, lucide-react
- DevDependencies: typescript, tailwindcss, eslint

**Edit**: Add new dependencies with `npm install package-name`

#### `tsconfig.json`
- TypeScript compiler options
- Strict mode enabled (recommended)
- Path aliases: `@/*` maps to root

**Edit**: Rarely needed. Only if changing TS behavior.

#### `next.config.js`
- Next.js build configuration
- `reactStrictMode: true` (good for catching bugs)
- `swcMinify: true` (fast builds with SWC)
- `images.unoptimized: true` (since we use SVG only)

**Edit**: Rarely needed. Only if changing Next.js behavior.

#### `tailwind.config.ts`
- **Most important for theming**
- Color palette (background, text, accent colors)
- Font families (Inter, Fira Code)
- Custom animations (gradient-shift, fade-in, etc.)
- Grid background pattern

**Edit**: Change colors here, all components update automatically

#### `postcss.config.js`
- PostCSS plugins configuration
- Includes Tailwind + Autoprefixer
- Necessary for Tailwind to work

**Edit**: Rarely needed.

#### `.eslintrc.json`
- ESLint rules for code quality
- Extends Next.js recommended config
- Custom rules for React hooks, console logs

**Edit**: Add/remove rules if you want stricter/looser linting

### Documentation Files

#### `README.md`
- **START HERE** for project overview
- Tech stack explanation
- Sections guide (what each section does)
- Getting started (npm install, npm run dev)
- Customization tips
- Deployment options
- Browser support
- Accessibility info

#### `QUICKSTART.md`
- **60-second setup guide**
- Install, start dev server, edit content
- Common customizations (colors, fonts, links)
- Troubleshooting

**Best for**: First-time setup, quick edits

#### `DEPLOYMENT.md`
- **Detailed deployment guide**
- Vercel (recommended): 1 command
- Docker: Build + deploy to AWS/GCP/DigitalOcean
- Static export: S3, GitHub Pages, Netlify
- Custom domain setup
- SSL/TLS
- Performance tuning
- CI/CD pipeline (GitHub Actions)
- Cost estimates

**Best for**: Going to production

#### `LANDING_PAGE_SUMMARY.md`
- **Complete project summary**
- Everything about the landing page
- Architecture, features, customization
- Quality assurance checklist
- Performance metrics

**Best for**: Understanding the full project

#### `INDEX.md` (this file)
- **Navigation guide**
- Directory structure
- File descriptions
- Quick lookup

---

## 🚀 Quick Lookup Table

| Need | File | Line |
|------|------|------|
| Change headline | `components/hero.tsx` | ~28 |
| Change colors | `tailwind.config.ts` | ~18 |
| Change navigation links | `components/navbar.tsx` | ~8 |
| Change footer links | `components/footer.tsx` | ~20 |
| Add new badge | `components/hero.tsx` | ~6 |
| Change pillar info | `components/pillars.tsx` | ~6 |
| Change phase status | `components/roadmap.tsx` | ~10 |
| Update CLI commands | `components/cli-showcase.tsx` | ~8 |
| Change fonts | `tailwind.config.ts` | ~25 |
| Update metadata | `app/layout.tsx` | ~3 |

---

## 📋 Component Import Order

The main page (`app/page.tsx`) imports in this order:

```typescript
import { Navbar } from '@/components/navbar'
import { Hero } from '@/components/hero'
import { ProblemSection } from '@/components/problem-section'
import { ArchitectureSection } from '@/components/architecture-section'
import { Pillars } from '@/components/pillars'
import { ASESSection } from '@/components/ases-section'
import { CLIShowcase } from '@/components/cli-showcase'
import { Comparison } from '@/components/comparison'
import { Roadmap } from '@/components/roadmap'
import { Footer } from '@/components/footer'
```

Reorder imports to change section order on page.

---

## 🎨 Design System Quick Reference

### Colors (from `tailwind.config.ts`)

```typescript
colors: {
  background: '#0a0a0a',          // Page background
  surface: '#121212',              // Cards, surfaces
  surface-secondary: '#1a1a1a',   // Slightly lighter
  border: '#252525',               // Border color
  text-primary: '#ffffff',         // Main text
  text-secondary: '#a1a1a1',      // Secondary text
  text-tertiary: '#696969',       // Tertiary text
  accent: {
    blue: '#3b82f6',               // Primary accent
    purple: '#8b5cf6',             // Secondary accent
    emerald: '#10b981',            // Success accent
  }
}
```

### Utility Classes (from `app/globals.css`)

- `.gradient-text` → Gradient heading text
- `.glass-effect` → Frosted glass card
- `.glass-dark` → Dark glass card
- `.glow-blue` → Blue shadow glow
- `.glow-purple` → Purple shadow glow
- `.smooth-transition` → Fade animation

### Tailwind Spacing

Uses 4px incremental system:
- `p-2` = 8px padding
- `p-4` = 16px padding
- `p-6` = 24px padding
- `p-8` = 32px padding
- `gap-4` = 16px gap

---

## 🔗 Navigation IDs

All sections have scroll targets. Use in navbar:

- `#architecture` → Architecture section
- `#features` → Pillars section
- `#roadmap` → Roadmap section
- `#docs` → (custom link)

To add: Add `id="your-id"` to section div, then add to navbar.

---

## ✅ Checklist: Making Changes

1. **Identify the component** (use table above)
2. **Open the file** in editor
3. **Find the data array** (usually at top of component)
4. **Edit the strings/objects**
5. **Save file**
6. **Dev server hot-reloads** (browser auto-updates)
7. **Test on mobile** (DevTools or real device)

No rebuilding needed for local changes.

---

## 📚 Key Files for Different Tasks

| Task | Edit | Backup |
|------|------|--------|
| Change colors | `tailwind.config.ts` | `tailwind.config.ts.bak` |
| Update all content | `components/*.tsx` | Individual files |
| Change fonts | `tailwind.config.ts` + `app/layout.tsx` | Both |
| Customize layout | `app/page.tsx` | `app/page.tsx.bak` |
| Add new dependencies | `package.json` | `package-lock.json` |
| Deploy settings | `next.config.js` | Keep default |

---

## 🎯 Development Workflow

1. **Make changes** in any `components/` file
2. **Save** (Ctrl+S)
3. **Browser updates automatically** (hot reload)
4. **Test locally** at `http://localhost:3000`
5. **Run `npm run build`** to check for errors
6. **Deploy** with `vercel` command

No manual refresh needed. Hot reload is automatic.

---

## 🚨 Do Not Edit

These files are rarely needed:
- `app/layout.tsx` (unless changing metadata)
- `tsconfig.json` (unless changing TS config)
- `next.config.js` (unless changing Next.js behavior)
- `postcss.config.js` (never)

Edit these instead:
- `tailwind.config.ts` → Colors, fonts, animations
- `app/globals.css` → Global styles
- `components/*.tsx` → Content and styling
- `package.json` → Only to add dependencies

---

## 📞 Quick Help

| Problem | Solution |
|---------|----------|
| Styling not updating | Hard refresh (Ctrl+Shift+R) or restart dev server |
| Type errors | Run `npm run build` to see full list |
| Module not found | Make sure import path matches filename |
| Hot reload not working | Restart dev server with `npm run dev` |
| Components not rendering | Check `app/page.tsx` imports all components |

---

## 🎓 Learning Resources

- **Next.js**: https://nextjs.org/docs
- **React**: https://react.dev
- **Tailwind CSS**: https://tailwindcss.com/docs
- **TypeScript**: https://www.typescriptlang.org/docs
- **Framer Motion**: https://www.framer.com/motion

---

This index should help you navigate all files quickly. Start with `README.md` for overview, then use this file to find specific components to edit.

Happy building! 🚀
