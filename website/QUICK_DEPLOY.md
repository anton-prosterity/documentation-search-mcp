# Quick Deploy Guide - Cloudflare Pages

## Prerequisites
- A Cloudflare account (free): https://dash.cloudflare.com/sign-up
- Your GitHub repository must be accessible

## Step-by-Step Deployment (5 minutes)

### 1. Open Cloudflare Pages
Go to: **https://dash.cloudflare.com**
- Log in to your Cloudflare account
- Click **"Workers & Pages"** in the left sidebar
- Click **"Create application"**
- Click **"Pages"** tab
- Click **"Connect to Git"**

### 2. Connect GitHub
- Click **"Connect GitHub"**
- Authorize Cloudflare Pages to access your GitHub
- Select your repository: **anton-prosterity/documentation-search-mcp**
- Click **"Begin setup"**

### 3. Configure Build Settings

**CRITICAL: Copy these settings exactly:**

```
Project name: documentation-search-enhanced
Production branch: main
```

**Build settings:**
```
Framework preset: Astro
Root directory: website
Build command: npm run build
Build output directory: dist
```

**Environment variables:** (leave empty)

### 4. Deploy
- Click **"Save and Deploy"**
- Wait 2-3 minutes for build to complete
- Your site will be live at: `https://documentation-search-enhanced.pages.dev`

---

## Common Issues

### Issue: "Cannot find repository"
**Solution:** Make sure you've authorized Cloudflare to access your GitHub account

### Issue: Build fails with "Module not found"
**Solution:** Make sure **Root directory** is set to `website` (not `/` or empty)

### Issue: Build fails with Node version error
**Solution:** The `.node-version` file should handle this automatically. If it persists, add environment variable:
- Key: `NODE_VERSION`
- Value: `20`

### Issue: "Project name already taken"
**Solution:** Use a different name like `documentation-search-enhanced-2` or `docs-search-mcp`

---

## After Deployment

Once deployed, Cloudflare will automatically:
- ✅ Redeploy every time you push to `main` branch
- ✅ Provide a URL: `https://your-project.pages.dev`
- ✅ Provide free SSL certificate
- ✅ Serve from global CDN

---

## Need Help?

If you're still stuck:
1. Take a screenshot of where you're stuck
2. Copy any error messages
3. Share them so I can help troubleshoot

Or try alternative deployment:
- See `DEPLOYMENT.md` for Wrangler CLI method
