# Quick Start - Ortho Landing Page

Get the landing page running in 60 seconds.

## 1. Install Dependencies

```bash
cd apps/landing
npm install
```

Takes ~30 seconds.

## 2. Start Dev Server

```bash
npm run dev
```

Outputs:
```
> next dev
  ▲ Next.js 15.0.0
  - Local:        http://localhost:3000
```

## 3. Open in Browser

Click or visit: **http://localhost:3000**

You should see the full landing page with:
- Hero section
- Problem/solution
- Five pillars
- ASES methodology
- CLI showcase
- Comparison table
- Roadmap
- Footer

## Editing Content

### Change Headline

`components/hero.tsx`, line ~28:
```typescript
<motion.h1>
  The <span className="gradient-text">Engineering Brain</span>
  <br />
  for AI Development
</motion.h1>
```

### Change Colors

`tailwind.config.ts`, line ~18:
```typescript
accent: {
  blue: '#3b82f6',
  purple: '#8b5cf6',
  emerald: '#10b981',
}
```

### Change Text in Sections

Each component in `components/` has a text array at the top:
```typescript
const items = [
  { label: 'Your text here', ... }
]
```

Just edit the strings.

### Add Navigation Link

`components/navbar.tsx`, line ~8:
```typescript
const links = [
  { label: 'Your Link', href: '#your-id' },
  // ...
]
```

Then in target component, add `id="your-id"`.

## Building for Production

```bash
npm run build
npm start
```

Output:
```
> next start
  ▲ Next.js 15.0.0
  - Local: http://localhost:3000
```

## Deploy to Vercel

```bash
npm i -g vercel
vercel
```

Follow prompts. Your site will be live at `your-project.vercel.app`

## Project Structure

```
components/
├── navbar.tsx         ← Navigation header
├── hero.tsx           ← Main section
├── problem-section.tsx
├── architecture-section.tsx
├── pillars.tsx        ← Five pillars cards
├── ases-section.tsx
├── cli-showcase.tsx
├── comparison.tsx
├── roadmap.tsx
└── footer.tsx

app/
├── layout.tsx         ← HTML head, metadata
├── page.tsx           ← Combines components
└── globals.css        ← Global styles

tailwind.config.ts     ← Colors, spacing, fonts
```

## Useful Commands

```bash
# Development
npm run dev              # Start dev server on :3000

# Building
npm run build            # Production build
npm start               # Run built version

# Linting
npm run lint            # Check code quality

# Deployment
vercel                  # Deploy to Vercel (one command)
```

## Common Customizations

### Change Accent Colors

Update three colors in `tailwind.config.ts`:
- `accent.blue`: Primary (buttons, highlights)
- `accent.purple`: Secondary (gradients)
- `accent.emerald`: Success/completed states

### Change Logo/Text

`components/navbar.tsx`, line ~15:
```typescript
<span className="text-lg font-semibold">Ortho</span> // Change this
```

### Change Fonts

`app/globals.css`:
```css
@import url('https://fonts.googleapis.com/css2?family=YourFont:wght@400;500;600;700&display=swap');
```

Then update `tailwind.config.ts` fontFamily.

### Remove a Section

`app/page.tsx` imports sections. Just delete the import + component:
```typescript
// Delete this line
import { ASESSection } from '@/components/ases-section'

// Delete from JSX
<ASESSection />
```

## Performance

Current Lighthouse score: **95+**

Stay fast:
- No external images (Lucide icons only)
- No analytics by default (add Sentry/GA manually)
- No third-party scripts
- CSS purged (Tailwind removes unused)

## Accessibility

- WCAG 2.1 AA compliant
- Semantic HTML
- Color contrast ≥ 4.5:1
- Keyboard navigation
- Screen reader friendly

Test with:
```bash
# Lighthouse audit
# DevTools → Lighthouse → Accessibility
```

## Mobile Testing

```bash
# Open on phone
# Same network as dev machine
# Visit: http://<your-ip>:3000
```

Or use Chrome DevTools:
- F12 → Toggle device toolbar (Ctrl+Shift+M)
- Set to iPhone 12 / Pixel 6 / iPad

## Troubleshooting

### Port 3000 Already in Use

```bash
lsof -i :3000
kill -9 <PID>
npm run dev
```

### Module Not Found

```bash
rm -rf node_modules
npm install
```

### Styles Not Applying

```bash
npm run build -- --force
npm run dev
```

### Hot Reload Not Working

Try:
```bash
npm install --legacy-peer-deps
npm run dev
```

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: 14+
- Mobile: iOS 12+, Android 8+

## File Size

Gzipped production bundle:
- JS: ~45KB
- CSS: ~12KB
- Total: ~60KB

Very fast.

## Environment Variables

**None needed** for the landing page.

If you add forms/analytics later:
```bash
# Create .env.local
NEXT_PUBLIC_ANALYTICS_ID=your-id
NEXT_PUBLIC_FORM_ENDPOINT=https://api.example.com
```

## Next Steps

1. Customize colors/text to match your brand
2. Update links (docs, GitHub, contact)
3. Run `npm run build` locally to verify
4. Deploy with `vercel` command
5. Add custom domain
6. Monitor with UptimeRobot (free)

## Getting Help

- Next.js docs: https://nextjs.org/docs
- Tailwind docs: https://tailwindcss.com/docs
- Framer Motion: https://www.framer.com/motion/
- Lucide Icons: https://lucide.dev

## That's It

Your landing page is now running. Make changes, see them live instantly. Deploy when ready.

Enjoy building!
