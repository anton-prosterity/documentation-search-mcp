# Cloudflare Pages Deployment Guide

This guide explains how to deploy the Documentation Search Enhanced website to Cloudflare Pages.

## Method 1: Automated GitHub Actions Deployment (Recommended)

This method automatically deploys your website whenever you push changes to the `website/` directory.

### Step 1: Get Cloudflare Credentials

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Get your **Account ID**:
   - Go to any page in the dashboard
   - Look in the URL: `https://dash.cloudflare.com/<ACCOUNT_ID>/`
   - Or go to "Workers & Pages" and find it in the right sidebar

3. Create an **API Token**:
   - Go to [API Tokens](https://dash.cloudflare.com/profile/api-tokens)
   - Click "Create Token"
   - Use the "Edit Cloudflare Workers" template
   - Permissions needed:
     - Account > Cloudflare Pages > Edit
   - Click "Continue to summary" → "Create Token"
   - **Copy the token immediately** (you won't see it again)

### Step 2: Add GitHub Secrets

1. Go to your GitHub repository settings
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add two secrets:
   - Name: `CLOUDFLARE_API_TOKEN`
     - Value: (paste your API token from Step 1)
   - Name: `CLOUDFLARE_ACCOUNT_ID`
     - Value: (paste your Account ID from Step 1)

### Step 3: Trigger Deployment

The GitHub Actions workflow is already set up and will automatically deploy when you:
- Push changes to the `website/` directory on the `main` branch
- Manually trigger it from the Actions tab

To manually trigger:
1. Go to your repository's **Actions** tab
2. Click "Deploy to Cloudflare Pages" workflow
3. Click "Run workflow"

### Step 4: Access Your Site

After deployment completes (1-2 minutes):
- Visit: `https://documentation-search-enhanced.pages.dev`
- Or check the deployment URL in the GitHub Actions log

---

## Method 2: Manual Cloudflare Dashboard Setup

If you prefer manual setup through the Cloudflare dashboard:

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

## Method 3: Wrangler CLI Deployment

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

The project requires Node.js 18+. The `.node-version` file should handle this automatically, but you can also set it in Cloudflare:

- Go to project **Settings** → **Environment variables**
- Add: `NODE_VERSION` = `18`

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
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Astro Deployment Guide](https://docs.astro.build/en/guides/deploy/cloudflare/)
