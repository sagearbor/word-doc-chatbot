# SvelteKit Frontend for Word Document Chatbot

Modern, high-performance frontend for the Word Document Tracked Changes Chatbot application.

## Overview

This SvelteKit application provides a fast, responsive user interface for uploading Word documents and applying AI-suggested edits with tracked changes. Built with TypeScript, TailwindCSS, and Skeleton UI for excellent developer experience and user experience.

## Tech Stack

- **Framework:** SvelteKit 2.x with TypeScript
- **Styling:** TailwindCSS 4.x + Skeleton UI 4.x
- **Icons:** Lucide Icons
- **Build Tool:** Vite 7.x
- **Adapter:** adapter-static (for static site generation)
- **Package Manager:** npm

## Features

- Upload Word documents (.docx) with drag-and-drop support
- Process documents with AI-suggested tracked changes
- Analyze existing tracked changes in documents
- Support for fallback documents (tracked changes or requirements)
- LLM configuration (model selection, temperature, debug modes)
- Detailed processing logs with collapsible sections
- Dark mode with persistent preference
- Mobile-first responsive design
- Toast notifications for user feedback
- WCAG 2.1 AA accessibility

## Project Structure

```
frontend-new/
├── src/
│   ├── routes/
│   │   ├── +layout.svelte          # Root layout with dark mode
│   │   └── +page.svelte            # Main application page
│   ├── lib/
│   │   ├── components/             # Reusable Svelte components
│   │   │   ├── DocumentUpload.svelte
│   │   │   ├── ProcessingOptions.svelte
│   │   │   ├── ProcessingResults.svelte
│   │   │   ├── ProcessingLogs.svelte
│   │   │   ├── AnalysisResults.svelte
│   │   │   ├── Header.svelte
│   │   │   ├── Footer.svelte
│   │   │   └── Toast.svelte
│   │   ├── stores/                 # Svelte stores for state management
│   │   │   ├── documentStore.ts    # Document state (files)
│   │   │   ├── processingStore.ts  # Processing state and results
│   │   │   └── uiStore.ts          # UI state (dark mode, tabs, toasts)
│   │   ├── api/                    # Backend API client
│   │   │   ├── client.ts           # API functions
│   │   │   └── types.ts            # TypeScript interfaces
│   │   └── utils/                  # Utility functions
│   │       └── index.ts
│   ├── app.html                    # HTML template
│   └── app.css                     # Global styles
├── static/                         # Static assets (favicon, etc.)
├── build/                          # Build output (generated)
├── .svelte-kit/                    # SvelteKit internal files (generated)
├── svelte.config.js               # SvelteKit configuration
├── vite.config.ts                 # Vite configuration
├── tailwind.config.js             # TailwindCSS configuration
├── postcss.config.js              # PostCSS configuration
├── tsconfig.json                  # TypeScript configuration
├── package.json                   # Dependencies and scripts
├── .env.development               # Development environment variables
├── .env.production                # Production environment variables
└── .env.example                   # Environment variables template
```

## Prerequisites

- Node.js 18+ (LTS recommended)
- npm 9+

## Installation

```bash
# Install dependencies
npm install
```

## Environment Variables

Create `.env.development` for local development:

```bash
# Backend API URL
PUBLIC_BACKEND_URL=http://localhost:8000

# Base path for reverse proxy deployment (optional)
BASE_URL_PATH=
```

For production, create `.env.production`:

```bash
# Backend API URL (adjust for your deployment)
PUBLIC_BACKEND_URL=http://localhost:8000

# Base path if deployed behind reverse proxy
BASE_URL_PATH=/sageapp04
```

See `.env.example` for all available options.

## Development

### Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173` with hot module replacement (HMR) enabled.

### Development Features

- **Hot Module Replacement:** Changes appear instantly without page reload
- **TypeScript Checking:** Real-time type checking in the terminal
- **Source Maps:** Easy debugging with original source code
- **Fast Refresh:** Component state preserved during updates

### Type Checking

```bash
# Run type checking
npm run check

# Run type checking in watch mode
npm run check:watch
```

## Building for Production

### Build the Application

```bash
# Build for production
npm run build

# Output directory: build/
```

The build process:
1. Compiles TypeScript to JavaScript
2. Bundles and minifies code with Vite
3. Processes CSS with TailwindCSS and PostCSS
4. Generates static HTML files
5. Applies base path if `BASE_URL_PATH` is set

### Preview Production Build

```bash
# Preview the production build locally
npm run preview
```

Access at `http://localhost:4173`

## Docker Deployment

This frontend is typically deployed as part of the main application Docker container. See the main README.md for full deployment instructions.

### Build with Docker

The frontend is built automatically in the main Dockerfile:

```dockerfile
# From project root
docker build -f Dockerfile.sveltekit -t word-chatbot:sveltekit .
```

The Dockerfile:
1. Builds the SvelteKit frontend with correct base path
2. Copies build output to FastAPI backend
3. FastAPI serves the static files

## Architecture

### State Management

The application uses Svelte stores for reactive state management:

**documentStore.ts** - Document files
```typescript
interface DocumentState {
  mainFile: File | null;
  fallbackFile: File | null;
}
```

**processingStore.ts** - Processing state and results
```typescript
interface ProcessingState {
  isProcessing: boolean;
  result: ProcessingResult | null;
  logs: string;
  error: string | null;
}
```

**uiStore.ts** - UI state (dark mode, active tab, toasts)
```typescript
interface UIState {
  darkMode: boolean;
  activeTab: 'process' | 'analyze';
  toasts: Toast[];
}
```

### API Client

All backend communication goes through the centralized API client (`src/lib/api/client.ts`):

```typescript
import { processDocument, analyzeDocument } from '$lib/api/client';

// Process document
const result = await processDocument(formData);

// Analyze document
const analysis = await analyzeDocument(formData);
```

The client handles:
- Base URL configuration from environment
- Error handling and response parsing
- FormData construction for file uploads
- TypeScript type safety

### Component Architecture

Components follow a container/presentation pattern:

- **Presentation Components:** Pure UI, receive props
  - Example: `Toast.svelte`, `Footer.svelte`

- **Container Components:** Connect to stores, handle logic
  - Example: `DocumentUpload.svelte`, `ProcessingOptions.svelte`

- **Page Components:** Orchestrate containers and presentation
  - Example: `+page.svelte`

### Styling

The application uses TailwindCSS for utility-first styling:

```svelte
<button class="btn variant-filled-primary">
  Process Document
</button>
```

Skeleton UI provides:
- Pre-built component styles
- Dark mode theme system
- Consistent design tokens
- Accessibility features

### Routing

SvelteKit uses file-based routing:

- `/` → `src/routes/+page.svelte` (main application)
- Layout: `src/routes/+layout.svelte` (wraps all pages)

## Key Components

### DocumentUpload

Handles file uploads with drag-and-drop support:

```svelte
<DocumentUpload
  label="Main Document"
  accept=".docx"
  onFileSelect={handleFileSelect}
/>
```

### ProcessingOptions

LLM configuration and debug options:

```svelte
<ProcessingOptions
  showTemperature={true}
  showDebugModes={true}
/>
```

### ProcessingResults

Displays processing results with download button:

```svelte
<ProcessingResults
  result={$processingStore.result}
  onDownload={handleDownload}
/>
```

### ProcessingLogs

Collapsible log viewer:

```svelte
<ProcessingLogs
  logs={$processingStore.logs}
  expanded={false}
/>
```

### Toast

Notification system:

```svelte
<script>
import { uiStore } from '$lib/stores/uiStore';

uiStore.addToast({
  message: 'Document processed successfully!',
  type: 'success',
  duration: 3000
});
</script>
```

## Development Workflow

### Adding a New Component

1. Create component file in `src/lib/components/`
2. Define TypeScript interfaces for props
3. Implement component logic and UI
4. Add to parent component
5. Test in browser with HMR

Example:

```svelte
<!-- src/lib/components/NewComponent.svelte -->
<script lang="ts">
  interface Props {
    title: string;
    onClick?: () => void;
  }

  let { title, onClick }: Props = $props();
</script>

<button class="btn" onclick={onClick}>
  {title}
</button>
```

### Adding a New Store

1. Create store file in `src/lib/stores/`
2. Define TypeScript interface
3. Export writable store
4. Use in components

Example:

```typescript
// src/lib/stores/newStore.ts
import { writable } from 'svelte/store';

interface NewState {
  value: string;
}

export const newStore = writable<NewState>({
  value: ''
});
```

### Adding a New API Endpoint

1. Add function to `src/lib/api/client.ts`
2. Define TypeScript types in `src/lib/api/types.ts`
3. Use in components

Example:

```typescript
// src/lib/api/client.ts
export async function newEndpoint(data: FormData) {
  const response = await fetch(`${API_BASE_URL}/new-endpoint/`, {
    method: 'POST',
    body: data
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}
```

## Performance Optimization

The application is optimized for performance:

- **Code Splitting:** Vite automatically splits vendor chunks
- **Tree Shaking:** Unused code is removed during build
- **Minification:** JavaScript and CSS are minified
- **Compression:** Gzip/Brotli compression in production
- **Lazy Loading:** Components loaded on demand
- **Image Optimization:** SVG icons, no raster images

### Bundle Analysis

```bash
# Build and analyze bundle
npm run build

# Check build output
ls -lh build/_app/immutable/

# Typical sizes:
# - Entry chunks: ~15KB (gzipped)
# - Vendor chunks: ~30KB (gzipped)
# - CSS: ~5KB (gzipped)
```

## Accessibility

The application follows WCAG 2.1 AA guidelines:

- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Focus indicators
- Color contrast ratios
- Screen reader compatibility
- Skip links for navigation

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### Issue: HMR Not Working

**Solution:** Restart the dev server
```bash
npm run dev
```

### Issue: Type Errors

**Solution:** Run type checking
```bash
npm run check
```

### Issue: Build Fails

**Solution:** Check environment variables and dependencies
```bash
# Verify .env files exist
ls .env.*

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Issue: Styles Not Applying

**Solution:** Rebuild Tailwind
```bash
# Restart dev server
npm run dev
```

## Testing

_Testing infrastructure to be added in future enhancement_

Planned test frameworks:
- **Unit Tests:** Vitest
- **Component Tests:** Testing Library
- **E2E Tests:** Playwright

## Contributing

When contributing to the frontend:

1. Follow TypeScript best practices
2. Use existing component patterns
3. Add types for all props and stores
4. Test in both light and dark modes
5. Verify mobile responsiveness
6. Run type checking before committing

## Resources

- [SvelteKit Documentation](https://kit.svelte.dev/docs)
- [Svelte Tutorial](https://svelte.dev/tutorial)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [Skeleton UI Documentation](https://www.skeleton.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Documentation](https://vitejs.dev/guide/)

## License

See main project LICENSE file.

---

**For full project documentation, see the main README.md in the project root.**
