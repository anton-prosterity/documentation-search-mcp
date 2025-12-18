# Documentation Search Enhanced Website

This is the official website for the Documentation Search Enhanced MCP Server project, built with Astro and Tailwind CSS.

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Deployment to Cloudflare Pages

### Automatic Deployment (Recommended)

1. Push the code to GitHub
2. Go to [Cloudflare Pages](https://pages.cloudflare.com/)
3. Click "Create a project"
4. Connect your GitHub repository
5. Configure build settings:
   - **Framework preset**: Astro
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
   - **Root directory**: `website`

6. Click "Save and Deploy"

### Build Settings

Cloudflare Pages will automatically detect the Astro framework and use these settings:

- **Build command**: `npm run build`
- **Build output directory**: `dist`
- **Node version**: 18+ (auto-detected from package.json)

### Custom Domain

After deployment, you can configure a custom domain in the Cloudflare Pages dashboard.

The site is currently configured to be hosted at: `https://documentation-search-enhanced.pages.dev`

## Project Structure

```
website/
├── src/
│   ├── layouts/
│   │   └── Layout.astro      # Main layout with navigation and footer
│   └── pages/
│       ├── index.astro        # Homepage
│       ├── README.md          # Documentation page (auto-generated from root README)
│       └── TUTORIAL.md        # Tutorial page (auto-generated from root TUTORIAL)
├── public/                    # Static assets
├── astro.config.mjs          # Astro configuration
├── tailwind.config.mjs       # Tailwind CSS configuration
└── package.json              # Dependencies and scripts
```

## Features

- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Static Site Generation**: Fast loading with pre-rendered pages
- **Markdown Support**: Automatic rendering of README and TUTORIAL
- **SEO Optimized**: Meta tags and descriptions
- **Modern UI**: Clean, professional design with gradient accents

## Technologies

- [Astro](https://astro.build/) - Static site generator
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Cloudflare Pages](https://pages.cloudflare.com/) - Static site hosting

## License

MIT License - same as the main project
