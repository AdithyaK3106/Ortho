# Deployment Guide - Ortho Landing Page

Complete guide to deploying the Ortho landing page to production.

## Quick Start (Vercel - Recommended)

Vercel is the easiest path. It's built for Next.js.

```bash
cd apps/landing

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

Follow prompts. Your site will be live in ~2 minutes.

**Environment**: Zero env vars needed. Everything is static.

## Option 1: Vercel (Production)

### Setup

1. Push code to GitHub (public or private)
2. Go to [vercel.com](https://vercel.com)
3. Click "New Project"
4. Select your GitHub repo
5. Configure:
   - Framework: Next.js (auto-detected)
   - Root: `./apps/landing`
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Environment: Leave blank

6. Click "Deploy"

### Custom Domain

1. In Vercel dashboard, go to Project → Settings → Domains
2. Add custom domain (e.g., `ortho.dev`)
3. Add DNS records:
   ```
   A record: 76.76.19.165
   AAAA record: 2606:4700:4700::1111
   ```

### Auto-Deploy on Git Push

Enabled by default. Push to main → auto-deploys.

### Performance

Vercel automatically:
- CDN caching worldwide
- Edge function optimization
- Image optimization
- Zero-downtime deployments

**Estimated Cost**: Free tier covers landing page. Scales to $20–100/mo under high load.

---

## Option 2: Self-Hosted (Docker)

### Build Image

```bash
cd apps/landing

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine

WORKDIR /app
RUN npm install -g next
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY package*.json ./

EXPOSE 3000
CMD ["npm", "start"]
EOF

# Build
docker build -t ortho-landing:latest .

# Test locally
docker run -p 3000:3000 ortho-landing:latest
```

Visit `http://localhost:3000`

### Deploy to Container Platform

**AWS ECS:**
```bash
# Tag
docker tag ortho-landing:latest <your-aws-account>.dkr.ecr.us-east-1.amazonaws.com/ortho-landing:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-aws-account>.dkr.ecr.us-east-1.amazonaws.com
docker push <your-aws-account>.dkr.ecr.us-east-1.amazonaws.com/ortho-landing:latest

# Deploy task definition + service
# (Use AWS Console or CloudFormation)
```

**Google Cloud Run:**
```bash
# Push to Artifact Registry
docker tag ortho-landing:latest us-central1-docker.pkg.dev/<project>/repo/ortho-landing:latest
docker push us-central1-docker.pkg.dev/<project>/repo/ortho-landing:latest

# Deploy
gcloud run deploy ortho-landing --image us-central1-docker.pkg.dev/<project>/repo/ortho-landing:latest
```

**DigitalOcean App Platform:**
1. Push to GitHub
2. Go to App Platform
3. Connect GitHub repo
4. Select `apps/landing` as source
5. Set `npm run build` as build command
6. Deploy

---

## Option 3: Static Export (No Server)

If you don't need dynamic features (this landing page doesn't).

### Export as Static

```bash
# Edit next.config.js
output: 'export'

# Build
npm run build

# Output in ./out/
```

### Deploy to S3 + CloudFront

```bash
# Install AWS CLI
aws configure

# Sync output to S3
aws s3 sync out/ s3://ortho-landing/ --delete --cache-control "public, max-age=31536000"

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"
```

### Deploy to GitHub Pages

```bash
# In package.json
"deploy": "npm run build && touch out/.nojekyll && git add . && git commit -m 'deploy' && git push"

npm run deploy
```

Then enable GitHub Pages in repo settings.

### Deploy to Netlify

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
netlify deploy --prod --dir=out
```

---

## Option 4: Railway / Fly.io (Simple VPS)

### Railway

```bash
# Install CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Fly.io

```bash
# Install
curl https://fly.io/install.sh | sh

# Initialize
fly launch

# Deploy
fly deploy
```

---

## SSL/TLS Certificate

All platforms above provide free SSL by default.

Custom domain? Use Let's Encrypt (free, auto-renewal):

```bash
# Certbot (Linux)
sudo certbot certonly --standalone -d ortho.dev -d www.ortho.dev
```

---

## Performance Tuning

### Caching Strategy

The landing page is static. Cache aggressively:

```
HTML: no-cache (revalidate on each request)
JS/CSS: public, max-age=31536000 (1 year)
Images: public, max-age=86400 (1 day)
```

Most platforms handle this automatically.

### CDN

Use Cloudflare for extra performance:

1. Update nameservers at registrar
2. Cloudflare dashboard → DNS
3. Add your site
4. Cache static assets
5. Enable minification

**Cost**: Free tier covers landing page.

---

## Monitoring

### Uptime Monitoring

Use UptimeRobot (free):

1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Add monitor: `https://ortho.dev`
3. Check every 5 minutes
4. Get alerts if down

### Analytics

Add to `app/layout.tsx`:

```typescript
// Google Analytics
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_ID" />
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'GA_ID');
</script>

// Or Fathom (privacy-first)
<script src="https://cdn.usefathom.com/script.js" data-site="YOUR_SITE_ID" defer></script>
```

### Error Tracking

Add Sentry:

```bash
npm install @sentry/nextjs
```

```typescript
// app/layout.tsx
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
});
```

---

## CI/CD Pipeline

### GitHub Actions

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: npm
      
      - name: Install
        run: npm ci
        working-directory: apps/landing
      
      - name: Build
        run: npm run build
        working-directory: apps/landing
      
      - name: Deploy to Vercel
        run: npm i -g vercel && vercel --prod
        working-directory: apps/landing
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
```

---

## Rollback Strategy

### Vercel

1. Dashboard → Deployments
2. Click a previous deployment
3. Click "Promote to Production"

Instant rollback in seconds.

### Docker

```bash
# Keep previous images
docker tag ortho-landing:old <registry>/ortho-landing:stable

# Deploy stable
docker pull <registry>/ortho-landing:stable
docker run -p 3000:3000 <registry>/ortho-landing:stable
```

---

## Domain Registration

Use any registrar:

- Namecheap: $8.88/yr
- Google Domains: $12/yr
- Vercel Domains: $10/yr
- GoDaddy: varies

Then:
1. Update nameservers to your platform's
2. Add SSL cert
3. Redirect www to non-www (or vice versa)

---

## Pre-Launch Checklist

- [ ] All links work (internal + external)
- [ ] Mobile responsive tested (375px, 768px, 1024px)
- [ ] Performance: Lighthouse score ≥ 90
- [ ] SEO: Meta tags, OG tags filled
- [ ] Forms: Newsletter signup (if added) tested
- [ ] Analytics: Tracking code added
- [ ] Error tracking: Sentry configured
- [ ] SSL: HTTPS working
- [ ] www redirect: www.ortho.dev → ortho.dev
- [ ] robots.txt: Allow search engines
- [ ] sitemap.xml: Generated
- [ ] 404 page: Custom 404 created
- [ ] Favicon: Set
- [ ] Canonical tags: Present on all pages

---

## Post-Launch

### Week 1

- Monitor uptime (UptimeRobot)
- Check error logs (Sentry)
- Verify analytics tracking

### Month 1

- Gather feedback from users
- Monitor Core Web Vitals (Lighthouse CI)
- Check SEO indexing (Google Search Console)
- Review analytics for traffic patterns

### Ongoing

- Security: Keep dependencies updated (`npm audit`)
- Performance: Monitor Lighthouse scores
- Content: Update testimonials, roadmap, features
- Backups: Automated backups for DNS/SSL certs

---

## Troubleshooting

### Deploy Fails

```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run build
```

### Slow Build

```bash
# Check build time
npm run build 2>&1 | tee build.log
grep -i "duration" build.log
```

Usually < 30 seconds. If longer, check for:
- Heavy imports
- Large images
- Slow network

### 404 Errors

Check `app/layout.tsx` and links are correct.

### Styling Issues

```bash
# Rebuild Tailwind cache
npm run build -- --force
```

---

## Cost Estimate (Annual)

| Service | Cost | Notes |
|---------|------|-------|
| Vercel | Free | Includes free tier |
| Domain | $10 | Namecheap |
| SSL | Free | Vercel included |
| Analytics | Free | Google Analytics |
| Monitoring | Free | UptimeRobot free tier |
| **Total** | **~$10** | Per year |

---

## Next Steps

1. Choose deployment platform (Vercel recommended)
2. Set up domain
3. Run deployment command
4. Verify live
5. Monitor uptime + analytics

**Done!** Your landing page is live.

