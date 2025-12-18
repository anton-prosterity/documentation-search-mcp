# Cloudflare Pages Deployment Guide

This guide explains how to deploy the Documentation Search Enhanced website to Cloudflare Pages.

## Cloudflare Dashboard Setup (Recommended)

This method uses Cloudflare's native GitHub integration - no API tokens needed!

### Step 1: Create Pages Project

1. Go to [Cloudflare Pages](https://dash.cloudflare.com/?to=/:account/pages)
2. Click "Create a project"
3. Click "Connect to Git"
4. Select your GitHub repository: `anton-prosterity/documentation-search-mcp`
5. Authorize Cloudflare Pages to access your repository

### Step 2: Configure Build Settings

Enter these settings:

- **Project name**: `documentation-search-enhanced`
- **Production branch**: `main`
- **Framework preset**: `Astro`
- **Root directory**: `website` (important!)
- **Build command**: `npm run build`
- **Build output directory**: `dist`

### Step 3: Environment Variables (Optional)

Leave environment variables empty unless you need custom configuration.

### Step 4: Deploy

1. Click "Save and Deploy"
2. Wait 1-2 minutes for the build to complete
3. Your site will be live at `https://documentation-search-enhanced.pages.dev`

---

## Alternative: Wrangler CLI Deployment

Deploy directly from your local machine using Wrangler:

### Prerequisites

```bash
npm install -g wrangler
wrangler login
```

### Deploy

```bash
cd website
npm run build
wrangler pages deploy dist --project-name=documentation-search-enhanced
```

---

## Troubleshooting

### Build Fails with Node Version Error

The project requires Node.js 20+. The `.node-version` file (set to 20.11.0) should handle this automatically, but you can also set it in Cloudflare:

- Go to project **Settings** → **Environment variables**
- Add: `NODE_VERSION` = `20`

### Build Fails with "Module not found"

Make sure the **Root directory** is set to `website` (not `/` or empty).

### Site Shows 404

Check that:
1. Build output directory is `dist`
2. Build completed successfully
3. The `dist` folder contains `index.html`

### Custom Domain

To use a custom domain:
1. Go to your Pages project
2. Click **Custom domains**
3. Click **Set up a custom domain**
4. Follow the DNS configuration instructions

---

## Monitoring

- View deployments: [Cloudflare Dashboard](https://dash.cloudflare.com/?to=/:account/pages)
- View build logs: Click on any deployment
- Analytics: Available in the Pages project dashboard

---

## Support

- [Cloudflare Pages Docs](https://developers.cloudflare.com/pages/)
- [Astro Deployment Guide](https://docs.astro.build/en/guides/deploy/cloudflare/)
- [Cloudflare Community](https://community.cloudflare.com/)
