# SvelteKit Migration: Complete Development Task List

> **Purpose**: Migrate from Streamlit frontend to SvelteKit in a single Docker container
> **Target**: VM deployment (NGINX on port 3004) → Azure Web Apps (future)
> **Timeline**: 12-14 days full-time development

---

## 📋 Table of Contents
- [Phase 0: Pre-Migration Planning](#phase-0-pre-migration-planning)
- [Phase 1: SvelteKit Project Setup](#phase-1-sveltekit-project-setup)
- [Phase 2: Core UI Components](#phase-2-core-ui-components)
- [Phase 3: Feature Components](#phase-3-feature-components)
- [Phase 4: API Integration](#phase-4-api-integration)
- [Phase 5: State Management](#phase-5-state-management)
- [Phase 6: FastAPI Backend Updates](#phase-6-fastapi-backend-updates)
- [Phase 7: Docker Single Container](#phase-7-docker-single-container)
- [Phase 8: Testing & QA](#phase-8-testing--qa)
- [Phase 9: VM Deployment](#phase-9-vm-deployment)
- [Phase 10: Documentation](#phase-10-documentation)
- [Phase 11: Cleanup & Optimization](#phase-11-cleanup--optimization)
- [Phase 12: Azure Preparation](#phase-12-azure-preparation)

---

## Phase 0: Pre-Migration Planning

### 0.1 Environment Analysis
- [ ] Document current Streamlit features (create feature inventory)
- [ ] List all API endpoints used by frontend
- [ ] Map Streamlit session state to SvelteKit stores
- [ ] Identify all environment variables used
- [ ] Document current NGINX configuration
- [ ] Review current docker-compose setup
- [ ] Understand nginx-helper purpose and determine if still needed
- [ ] Document BASE_URL_PATH behavior (/sageapp04/)

### 0.2 Technology Decisions
- [ ] Confirm SvelteKit vs alternatives (Next.js, Nuxt, etc.)
- [ ] Choose UI library: Skeleton UI (decided ✓)
- [ ] Decide on TypeScript vs JavaScript (TypeScript recommended)
- [ ] Choose state management approach (Svelte stores vs context)
- [ ] Decide on form handling library (native vs Superforms)
- [ ] Choose icon library (Lucide, Heroicons, or Material Icons)
- [ ] Decide on date formatting library (if needed)
- [ ] Choose notification/toast library (or build custom)

### 0.3 Architecture Planning
- [ ] Design component hierarchy diagram
- [ ] Plan folder structure (`/routes`, `/lib/components`, `/lib/utils`)
- [ ] Design API client architecture
- [ ] Plan state management strategy
- [ ] Design error handling strategy
- [ ] Plan loading state patterns
- [ ] Design mobile-first responsive breakpoints
- [ ] Plan accessibility strategy (WCAG 2.1 AA compliance)

### 0.4 Risk Assessment
- [ ] Identify potential migration blockers
- [ ] Plan rollback strategy if migration fails
- [ ] Document backward compatibility requirements
- [ ] Plan for zero-downtime deployment
- [ ] Identify critical features that must work day-1
- [ ] Plan gradual rollout strategy (optional)
- [ ] Document testing requirements before go-live

---

## Phase 1: SvelteKit Project Setup

### 1.1 Project Initialization
- [ ] Create `frontend-new/` directory in project root
- [ ] Run `npx sv create frontend-new` (SvelteKit 2.0+ CLI)
  - [ ] Choose: Skeleton project template
  - [ ] Choose: Yes to TypeScript
  - [ ] Choose: Add Tailwind CSS
  - [ ] Choose: Add Prettier (code formatting)
  - [ ] Choose: Add Playwright (E2E testing - optional)
  - [ ] Choose: Add Vitest (unit testing - optional)
- [ ] Verify `frontend-new/` structure created correctly
- [ ] Navigate to `frontend-new/` and verify `package.json` exists

### 1.2 Core Dependencies Installation
- [ ] Install Skeleton UI: `npm install -D @skeletonlabs/skeleton @skeletonlabs/tw-plugin`
- [ ] Install Tailwind plugins: `npm install -D @tailwindcss/forms @tailwindcss/typography`
- [ ] Install icons: `npm install lucide-svelte` (or `@iconify/svelte`)
- [ ] Install utility libraries:
  - [ ] `npm install clsx` (class name utility)
  - [ ] `npm install date-fns` (date formatting, if needed)
- [ ] Install dev dependencies:
  - [ ] `npm install -D vite-plugin-tailwind-purgecss` (CSS optimization)
  - [ ] `npm install -D @sveltejs/adapter-static` (static build adapter)

### 1.3 SvelteKit Configuration
- [ ] Configure `svelte.config.js`:
  ```javascript
  import adapter from '@sveltejs/adapter-static';
  import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

  export default {
    preprocess: vitePreprocess(),
    kit: {
      adapter: adapter({
        pages: 'build',
        assets: 'build',
        fallback: 'index.html',
        precompress: false,
        strict: true
      }),
      paths: {
        base: process.env.BASE_URL_PATH || '', // Support /sageapp04 prefix
        relative: false
      }
    }
  };
  ```
- [ ] Verify adapter-static configuration for FastAPI serving
- [ ] Test base path configuration with `/sageapp04` prefix

### 1.4 Tailwind CSS Configuration
- [ ] Configure `tailwind.config.js`:
  ```javascript
  import { skeleton } from '@skeletonlabs/tw-plugin';
  import forms from '@tailwindcss/forms';
  import typography from '@tailwindcss/typography';

  export default {
    darkMode: 'class',
    content: [
      './src/**/*.{html,js,svelte,ts}',
      './node_modules/@skeletonlabs/skeleton/**/*.{html,js,svelte,ts}'
    ],
    theme: {
      extend: {
        // Custom breakpoints for mobile-first design
        screens: {
          'xs': '475px',
        }
      }
    },
    plugins: [
      forms,
      typography,
      skeleton({
        themes: { preset: ['skeleton', 'modern'] }
      })
    ]
  };
  ```
- [ ] Create `postcss.config.js`:
  ```javascript
  export default {
    plugins: {
      tailwindcss: {},
      autoprefixer: {}
    }
  };
  ```
- [ ] Create `src/app.pcss` (global styles):
  ```css
  @tailwind base;
  @tailwind components;
  @tailwind utilities;

  @layer base {
    body {
      @apply bg-surface-50 dark:bg-surface-900;
    }
  }
  ```

### 1.5 TypeScript Configuration
- [ ] Review `tsconfig.json` (should be auto-generated)
- [ ] Add path aliases if needed:
  ```json
  {
    "compilerOptions": {
      "paths": {
        "$lib": ["./src/lib"],
        "$lib/*": ["./src/lib/*"]
      }
    }
  }
  ```
- [ ] Create `src/app.d.ts` for type definitions
- [ ] Define API response types in `src/lib/types/api.ts`

### 1.6 Environment Variables Setup
- [ ] Create `.env.development`:
  ```bash
  PUBLIC_BACKEND_URL=http://localhost:8000
  PUBLIC_BASE_URL_PATH=
  ```
- [ ] Create `.env.production`:
  ```bash
  PUBLIC_BACKEND_URL=http://localhost:8000
  PUBLIC_BASE_URL_PATH=/sageapp04
  ```
- [ ] Document environment variable naming (PUBLIC_ prefix for client-side)
- [ ] Add `.env*` to `.gitignore`
- [ ] Create `.env.example` with all variables documented

### 1.7 Vite Configuration
- [ ] Configure `vite.config.ts`:
  ```typescript
  import { sveltekit } from '@sveltejs/kit/vite';
  import { defineConfig } from 'vite';

  export default defineConfig({
    plugins: [sveltekit()],
    server: {
      port: 5173,
      proxy: {
        '/process-document': 'http://localhost:8000',
        '/analyze-document': 'http://localhost:8000',
        '/download': 'http://localhost:8000',
      }
    }
  });
  ```
- [ ] Test dev server proxy for API calls during development

### 1.8 Project Structure Setup
- [ ] Create folder structure:
  ```
  frontend-new/
  ├── src/
  │   ├── lib/
  │   │   ├── components/        # UI components
  │   │   │   ├── core/          # Layout components
  │   │   │   ├── features/      # Feature-specific components
  │   │   │   └── shared/        # Reusable components
  │   │   ├── stores/            # Svelte stores (state)
  │   │   ├── utils/             # Utility functions
  │   │   ├── api/               # API client
  │   │   └── types/             # TypeScript types
  │   ├── routes/                # SvelteKit routes
  │   │   ├── +layout.svelte     # Root layout
  │   │   └── +page.svelte       # Home page
  │   ├── app.html               # HTML template
  │   └── app.pcss               # Global CSS
  ├── static/                    # Static assets
  │   └── favicon.png
  └── package.json
  ```
- [ ] Verify folder structure created

### 1.9 Initial Build Test
- [ ] Run `npm install` to install all dependencies
- [ ] Run `npm run dev` and verify dev server starts on port 5173
- [ ] Open `http://localhost:5173` and verify default page loads
- [ ] Run `npm run build` and verify static build succeeds
- [ ] Check `build/` directory contains static files
- [ ] Test built files: `npm run preview`
- [ ] Verify base path works: `http://localhost:4173/sageapp04/` (if configured)

### 1.10 Version Control Setup
- [ ] Create `.gitignore` entries for `frontend-new/`:
  ```
  node_modules/
  build/
  .svelte-kit/
  .env
  .env.*
  !.env.example
  ```
- [ ] Commit initial SvelteKit setup:
  ```bash
  git add frontend-new/
  git commit -m "feat: Initialize SvelteKit project structure"
  ```

---

## Phase 2: Core UI Components

### 2.1 Root Layout Component
- [ ] Create `src/routes/+layout.svelte`:
  - [ ] Import global CSS (`import '../app.pcss';`)
  - [ ] Set up Skeleton UI AppShell structure
  - [ ] Define main container with responsive grid
  - [ ] Add `<slot />` for page content
  - [ ] Include modal/drawer providers (if using Skeleton modals)
  - [ ] Add theme toggle button (dark/light mode)
  - [ ] Test responsive layout on mobile/tablet/desktop

### 2.2 Main Page Layout
- [ ] Create `src/routes/+page.svelte`:
  - [ ] Import necessary components
  - [ ] Set up two-column layout (options sidebar + main content)
  - [ ] Add responsive breakpoint (stack vertically on mobile)
  - [ ] Include page title and description
  - [ ] Add meta tags for SEO (optional)

### 2.3 Header Component
- [ ] Create `src/lib/components/core/Header.svelte`:
  - [ ] App title: "📄 Word Document Tracked Changes Assistant"
  - [ ] Optional: Add navigation menu
  - [ ] Include theme toggle button
  - [ ] Add responsive hamburger menu for mobile
  - [ ] Props: `title: string`
  - [ ] Emit events: `on:themeToggle`

### 2.4 Sidebar Component
- [ ] Create `src/lib/components/core/Sidebar.svelte`:
  - [ ] Container for all options and controls
  - [ ] Collapsible on mobile (drawer/modal)
  - [ ] Sticky positioning on desktop
  - [ ] Scrollable content if overflows
  - [ ] Section dividers with headers
  - [ ] Props: `isMobile: boolean`

### 2.5 Loading Spinner Component
- [ ] Create `src/lib/components/shared/LoadingSpinner.svelte`:
  - [ ] SVG spinner animation
  - [ ] Props: `size: 'sm' | 'md' | 'lg'`, `message?: string`
  - [ ] Accessible ARIA attributes
  - [ ] Skeleton UI spinner variant support

### 2.6 Toast/Notification Component
- [ ] Create `src/lib/components/shared/Toast.svelte`:
  - [ ] Support types: `success`, `error`, `warning`, `info`
  - [ ] Auto-dismiss after timeout (configurable)
  - [ ] Close button
  - [ ] Stack multiple toasts
  - [ ] Accessible ARIA live region
  - [ ] Slide-in animation
  - [ ] Props: `type`, `message`, `duration`, `dismissible`

### 2.7 Toast Store
- [ ] Create `src/lib/stores/toast.ts`:
  - [ ] Svelte writable store for toast queue
  - [ ] Functions: `showToast()`, `dismissToast()`, `clearAll()`
  - [ ] Auto-increment toast IDs
  - [ ] Example usage:
    ```typescript
    export const toastStore = writable<Toast[]>([]);
    export function showToast(message: string, type: ToastType, duration = 5000) {
      const id = Date.now();
      toastStore.update(toasts => [...toasts, { id, message, type, duration }]);
      setTimeout(() => dismissToast(id), duration);
    }
    ```

### 2.8 Modal Component (Optional)
- [ ] Create `src/lib/components/shared/Modal.svelte`:
  - [ ] Overlay backdrop
  - [ ] Centered modal container
  - [ ] Close on outside click
  - [ ] Close on ESC key
  - [ ] Trap focus inside modal
  - [ ] Props: `isOpen: boolean`, `title: string`, `onClose: () => void`
  - [ ] Slot for modal content

### 2.9 Button Component
- [ ] Create `src/lib/components/shared/Button.svelte`:
  - [ ] Variants: `primary`, `secondary`, `danger`, `ghost`
  - [ ] Sizes: `sm`, `md`, `lg`
  - [ ] Loading state (shows spinner)
  - [ ] Disabled state
  - [ ] Icon support (prefix/suffix)
  - [ ] Props: `variant`, `size`, `loading`, `disabled`, `onClick`
  - [ ] Accessible ARIA attributes

### 2.10 Card Component
- [ ] Create `src/lib/components/shared/Card.svelte`:
  - [ ] Container with padding and border
  - [ ] Optional header and footer slots
  - [ ] Responsive padding
  - [ ] Shadow/elevation variants
  - [ ] Props: `elevated: boolean`, `padding: 'sm' | 'md' | 'lg'`

### 2.11 Divider Component
- [ ] Create `src/lib/components/shared/Divider.svelte`:
  - [ ] Horizontal rule with proper spacing
  - [ ] Optional text in center
  - [ ] Props: `text?: string`, `spacing: 'sm' | 'md' | 'lg'`

### 2.12 Accessibility Utilities
- [ ] Create `src/lib/utils/a11y.ts`:
  - [ ] `trapFocus()` function for modals
  - [ ] `announceToScreenReader()` for live regions
  - [ ] `getAriaLabel()` helper

---

## Phase 3: Feature Components

### 3.1 File Upload Component
- [ ] Create `src/lib/components/features/FileUpload.svelte`:
  - [ ] Drag and drop zone
  - [ ] Click to browse files
  - [ ] File type validation (.docx only)
  - [ ] File size validation (warn if >10MB)
  - [ ] Display selected file name and size
  - [ ] Remove/clear file button
  - [ ] Visual feedback on drag over
  - [ ] Props: `label: string`, `accept: string`, `onFileSelect: (file: File) => void`
  - [ ] Emit: `file:selected`, `file:removed`, `file:error`
  - [ ] Accessible keyboard interaction
  - [ ] Mobile-friendly file picker

### 3.2 Instructions Input Component
- [ ] Create `src/lib/components/features/InstructionsInput.svelte`:
  - [ ] Textarea with label
  - [ ] Character count indicator
  - [ ] Auto-resize based on content
  - [ ] Placeholder text
  - [ ] Optional: Syntax highlighting for common patterns
  - [ ] Props: `value: string`, `placeholder: string`, `rows: number`
  - [ ] Emit: `input`, `change`

### 3.3 Process Button Component
- [ ] Create `src/lib/components/features/ProcessButton.svelte`:
  - [ ] Large primary button
  - [ ] Loading state with spinner
  - [ ] Disabled when no file or no instructions
  - [ ] Keyboard shortcut hint (Ctrl+Enter)
  - [ ] Props: `loading: boolean`, `disabled: boolean`, `onClick: () => void`

### 3.4 Results Display Component
- [ ] Create `src/lib/components/features/ResultsDisplay.svelte`:
  - [ ] Status message with icon (success/error/info)
  - [ ] Metrics display (edits suggested/applied)
  - [ ] Download button for processed file
  - [ ] Processing duration indicator
  - [ ] Expandable details section
  - [ ] Props: `result: ProcessingResult`
  - [ ] Conditional rendering based on result type

### 3.5 Processing Log Component
- [ ] Create `src/lib/components/features/ProcessingLog.svelte`:
  - [ ] Expandable/collapsible section
  - [ ] Syntax-highlighted log text
  - [ ] Search/filter functionality
  - [ ] Copy to clipboard button
  - [ ] Color-coded log levels (error=red, warning=yellow)
  - [ ] Props: `logContent: string`, `expanded: boolean`
  - [ ] Max height with scrolling

### 3.6 Analysis Mode Selector
- [ ] Create `src/lib/components/features/AnalysisMode.svelte`:
  - [ ] Radio button group or dropdown
  - [ ] Options: "Summarize Extracted Changes", "Summarize from Raw XML"
  - [ ] Helper text explaining each option
  - [ ] Props: `value: 'summary' | 'raw_xml'`, `onChange: (value) => void`

### 3.7 Analyze Button Component
- [ ] Create `src/lib/components/features/AnalyzeButton.svelte`:
  - [ ] Secondary button style
  - [ ] Loading state
  - [ ] Disabled when no file uploaded
  - [ ] Props: `loading: boolean`, `disabled: boolean`, `onClick: () => void`

### 3.8 Analysis Results Component
- [ ] Create `src/lib/components/features/AnalysisResults.svelte`:
  - [ ] Display AI-generated analysis text
  - [ ] Formatted markdown rendering (if AI returns markdown)
  - [ ] Copy analysis button
  - [ ] Expandable sections for long analysis
  - [ ] Props: `analysisContent: string`

### 3.9 Fallback Upload Component
- [ ] Create `src/lib/components/features/FallbackUpload.svelte`:
  - [ ] Similar to FileUpload but labeled "Fallback Document"
  - [ ] Conditional rendering (only show if checkbox enabled)
  - [ ] Visual distinction from main upload
  - [ ] Info tooltip explaining fallback purpose
  - [ ] Props: `enabled: boolean`, `onFileSelect: (file: File) => void`

### 3.10 Merge Strategy Selector
- [ ] Create `src/lib/components/features/MergeStrategy.svelte`:
  - [ ] Dropdown or radio group
  - [ ] Options: "Append", "Prepend", "Priority (Fallback takes precedence)"
  - [ ] Helper text for each option
  - [ ] Props: `value: string`, `onChange: (value) => void`

### 3.11 Fallback Analysis Preview
- [ ] Create `src/lib/components/features/FallbackAnalysis.svelte`:
  - [ ] Show requirements count
  - [ ] Display categories found
  - [ ] Preview first few requirements
  - [ ] Expandable details
  - [ ] Tracked changes detection indicator
  - [ ] Props: `analysisData: FallbackAnalysisResult`

### 3.12 LLM Config Component
- [ ] Create `src/lib/components/features/LLMConfig.svelte`:
  - [ ] Extraction method selector (LLM vs Regex)
  - [ ] Instruction method selector (LLM vs Hardcoded)
  - [ ] Current mode indicator
  - [ ] "Update AI Mode" button
  - [ ] Loading state during config update
  - [ ] Props: `currentConfig: LLMConfig`, `onUpdate: (config) => void`

### 3.13 Debug Options Component
- [ ] Create `src/lib/components/features/DebugOptions.svelte`:
  - [ ] Debug level dropdown (Off, Standard, Extended)
  - [ ] Helper text explaining each level
  - [ ] Props: `value: 'off' | 'standard' | 'extended'`, `onChange: (value) => void`

### 3.14 Debug Info Display Component
- [ ] Create `src/lib/components/features/DebugInfo.svelte`:
  - [ ] Expandable sections for debug data
  - [ ] User-friendly summary section
  - [ ] Extended details section (JSON viewer)
  - [ ] Edit details list with status icons
  - [ ] Fallback document analysis preview
  - [ ] Copy debug data button
  - [ ] Props: `debugInfo: DebugInfo`

### 3.15 Options Panel Component
- [ ] Create `src/lib/components/features/OptionsPanel.svelte`:
  - [ ] Author name input
  - [ ] Case-sensitive search checkbox
  - [ ] Add comments checkbox
  - [ ] Grouped related options
  - [ ] Props: `options: ProcessingOptions`, `onChange: (options) => void`

### 3.16 Download Button Component
- [ ] Create `src/lib/components/features/DownloadButton.svelte`:
  - [ ] Large success-colored button
  - [ ] File icon
  - [ ] File name and size display
  - [ ] Download progress indicator (if large file)
  - [ ] Props: `filename: string`, `url: string`, `onClick: () => void`

---

## Phase 4: API Integration

### 4.1 API Client Setup
- [ ] Create `src/lib/api/client.ts`:
  - [ ] Base API URL from environment variable
  - [ ] Helper function: `getBackendUrl()`
  - [ ] Helper function: `buildFormData()`
  - [ ] Helper function: `handleResponse()`
  - [ ] Error handling utility
  - [ ] Timeout configuration

### 4.2 Type Definitions
- [ ] Create `src/lib/types/api.ts`:
  - [ ] `ProcessDocumentRequest` interface
  - [ ] `ProcessDocumentResponse` interface
  - [ ] `AnalyzeDocumentRequest` interface
  - [ ] `AnalyzeDocumentResponse` interface
  - [ ] `ProcessWithFallbackRequest` interface
  - [ ] `ProcessWithFallbackResponse` interface
  - [ ] `LLMConfigResponse` interface
  - [ ] `ErrorResponse` interface
  - [ ] `TrackedChange` interface
  - [ ] `DebugInfo` interface

### 4.3 Process Document Endpoint
- [ ] Create `src/lib/api/processDocument.ts`:
  ```typescript
  export async function processDocument(
    file: File,
    instructions: string,
    options: ProcessingOptions
  ): Promise<ProcessDocumentResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('instructions', instructions);
    formData.append('author_name', options.authorName);
    formData.append('case_sensitive', options.caseSensitive.toString());
    formData.append('add_comments', options.addComments.toString());
    formData.append('debug_mode', options.debugMode.toString());
    formData.append('extended_debug_mode', options.extendedDebugMode.toString());

    const response = await fetch(`${getBackendUrl()}/process-document/`, {
      method: 'POST',
      body: formData,
      signal: AbortSignal.timeout(300000) // 5 min timeout
    });

    return handleResponse(response);
  }
  ```
- [ ] Add error handling for network errors
- [ ] Add error handling for timeout
- [ ] Add error handling for HTTP errors
- [ ] Add retry logic (optional)

### 4.4 Analyze Document Endpoint
- [ ] Create `src/lib/api/analyzeDocument.ts`:
  - [ ] Function: `analyzeDocument(file: File, mode: 'summary' | 'raw_xml')`
  - [ ] Build FormData with file and analysis_mode
  - [ ] POST to `/analyze-document/`
  - [ ] Timeout: 120 seconds
  - [ ] Return analysis text

### 4.5 Process With Fallback Endpoint
- [ ] Create `src/lib/api/processWithFallback.ts`:
  - [ ] Function: `processWithFallback(inputFile, fallbackFile, userInstructions, options)`
  - [ ] Build FormData with both files
  - [ ] Include merge_strategy parameter
  - [ ] POST to `/process-document-with-fallback/`
  - [ ] Timeout: 300 seconds
  - [ ] Return processing result with debug info

### 4.6 Analyze Fallback Requirements Endpoint
- [ ] Create `src/lib/api/analyzeFallback.ts`:
  - [ ] Function: `analyzeFallbackRequirements(file: File, context: string)`
  - [ ] Build FormData with file and context
  - [ ] POST to `/analyze-fallback-requirements/`
  - [ ] Timeout: 120 seconds
  - [ ] Return requirements analysis

### 4.7 LLM Config Endpoints
- [ ] Create `src/lib/api/llmConfig.ts`:
  - [ ] Function: `getLLMConfig()` - GET `/llm-config/`
  - [ ] Function: `setLLMConfig(extractionMethod, instructionMethod)` - POST `/llm-config/`
  - [ ] Return current configuration

### 4.8 Download File Handler
- [ ] Create `src/lib/api/downloadFile.ts`:
  ```typescript
  export async function downloadFile(filename: string): Promise<Blob> {
    const response = await fetch(`${getBackendUrl()}/download/${filename}`);
    if (!response.ok) throw new Error('Download failed');
    return response.blob();
  }

  export function triggerDownload(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }
  ```

### 4.9 API Error Handling
- [ ] Create `src/lib/api/errors.ts`:
  - [ ] Custom error classes: `NetworkError`, `TimeoutError`, `APIError`
  - [ ] Error parsing from response JSON
  - [ ] User-friendly error messages
  - [ ] Error logging utility

### 4.10 API Testing
- [ ] Test each endpoint individually with mock server
- [ ] Test error scenarios (network failure, timeout, 500 error)
- [ ] Test file upload with large files (>10MB)
- [ ] Test concurrent requests
- [ ] Test request cancellation (AbortController)

---

## Phase 5: State Management

### 5.1 Application State Store
- [ ] Create `src/lib/stores/app.ts`:
  - [ ] `isProcessing` (boolean) - loading state
  - [ ] `uploadedFile` (File | null) - main document
  - [ ] `fallbackFile` (File | null) - fallback document
  - [ ] `instructions` (string) - user instructions
  - [ ] `processingOptions` (object) - author name, case-sensitive, etc.
  - [ ] Derived stores where appropriate

### 5.2 Results State Store
- [ ] Create `src/lib/stores/results.ts`:
  - [ ] `processedResult` - processing response
  - [ ] `analysisResult` - analysis response
  - [ ] `fallbackAnalysis` - fallback analysis response
  - [ ] `llmConfig` - current LLM configuration
  - [ ] Functions: `setProcessedResult()`, `clearResults()`

### 5.3 UI State Store
- [ ] Create `src/lib/stores/ui.ts`:
  - [ ] `useFallbackMode` (boolean) - fallback checkbox state
  - [ ] `analysisMode` ('summary' | 'raw_xml')
  - [ ] `mergeStrategy` (string)
  - [ ] `debugLevel` ('off' | 'standard' | 'extended')
  - [ ] `sidebarOpen` (boolean) - mobile sidebar state

### 5.4 Form Validation Store
- [ ] Create `src/lib/stores/validation.ts`:
  - [ ] Validation rules for file upload
  - [ ] Validation rules for instructions
  - [ ] Error messages store
  - [ ] Functions: `validateFile()`, `validateInstructions()`

### 5.5 Store Actions
- [ ] Create `src/lib/stores/actions.ts`:
  - [ ] `resetAllState()` - clear all stores
  - [ ] `loadFromLocalStorage()` - restore state (optional)
  - [ ] `saveToLocalStorage()` - persist state (optional)

---

## Phase 6: FastAPI Backend Updates

### 6.1 Add StaticFiles Support
- [ ] Update `backend/main.py`:
  ```python
  from fastapi.staticfiles import StaticFiles
  from fastapi.responses import FileResponse

  # ... existing routes ...

  # Mount static files AFTER all API routes
  app.mount("/", StaticFiles(directory="static", html=True), name="static")
  ```
- [ ] Ensure API routes are defined BEFORE static mount
- [ ] Test that API endpoints still work

### 6.2 Add SPA Fallback Route
- [ ] Add fallback route for SvelteKit client-side routing:
  ```python
  @app.get("/{full_path:path}")
  async def serve_spa(full_path: str):
      # Serve index.html for all non-API routes
      if not full_path.startswith(("process-", "analyze-", "download", "llm-config")):
          return FileResponse("static/index.html")
      raise HTTPException(status_code=404)
  ```
- [ ] Test that `/sageapp04/` route serves index.html

### 6.3 Update CORS Settings (Development Only)
- [ ] Add CORS middleware for local development:
  ```python
  from fastapi.middleware.cors import CORSMiddleware

  if os.getenv("ENVIRONMENT") == "development":
      app.add_middleware(
          CORSMiddleware,
          allow_origins=["http://localhost:5173"],
          allow_methods=["*"],
          allow_headers=["*"],
      )
  ```
- [ ] Remove CORS in production (single-origin deployment)

### 6.4 Health Check for Frontend
- [ ] Add frontend-specific health check:
  ```python
  @app.get("/health")
  async def health_check():
      return {"status": "healthy", "version": "4.1.0"}
  ```

### 6.5 Test Backend Changes
- [ ] Run FastAPI: `uvicorn backend.main:app --reload`
- [ ] Test API endpoints at `http://localhost:8000/process-document/`
- [ ] Test static file serving (create dummy `static/index.html` for testing)
- [ ] Verify CORS allows requests from SvelteKit dev server

---

## Phase 7: Docker Single Container

### 7.1 Multi-Stage Dockerfile Creation
- [ ] Create `Dockerfile.sveltekit` in project root:
  ```dockerfile
  # ============================================================================
  # Stage 1: Build SvelteKit Frontend
  # ============================================================================
  FROM node:18-alpine AS frontend-builder

  WORKDIR /frontend

  # Copy package files
  COPY frontend-new/package*.json ./

  # Install dependencies
  RUN npm ci --only=production

  # Copy source code
  COPY frontend-new/ ./

  # Set build-time environment variables
  ARG BASE_URL_PATH=/sageapp04
  ENV PUBLIC_BASE_URL_PATH=${BASE_URL_PATH}
  ENV PUBLIC_BACKEND_URL=

  # Build static site
  RUN npm run build

  # Verify build output
  RUN ls -la /frontend/build

  # ============================================================================
  # Stage 2: Python Backend + Static Frontend
  # ============================================================================
  FROM python:3.11-slim

  WORKDIR /app

  # Install system dependencies
  RUN apt-get update && \
      apt-get install -y --no-install-recommends \
        curl \
        && rm -rf /var/lib/apt/lists/*

  # Copy backend requirements and install
  COPY requirements.txt ./
  RUN pip install --no-cache-dir -r requirements.txt

  # Copy backend code
  COPY backend/ ./backend/

  # Copy built SvelteKit static files from Stage 1
  COPY --from=frontend-builder /frontend/build ./static

  # Verify static files copied
  RUN ls -la /app/static

  # Create non-root user for security
  RUN useradd -m -u 1000 appuser && \
      chown -R appuser:appuser /app
  USER appuser

  # Expose port 8000
  EXPOSE 8000

  # Health check
  HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

  # Run FastAPI
  CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- [ ] Document build arguments in comments

### 7.2 Docker Build Configuration
- [ ] Create `.dockerignore`:
  ```
  # Python
  __pycache__/
  *.py[cod]
  *$py.class
  .Python
  env/
  venv/

  # Node
  node_modules/
  .svelte-kit/
  build/

  # Git
  .git/
  .gitignore

  # Docs
  *.md
  docs/

  # Tests
  tests/
  *.test.js

  # IDE
  .vscode/
  .idea/

  # Misc
  .env
  .env.*
  !.env.example
  ```
- [ ] Test `.dockerignore` effectiveness

### 7.3 Environment Variables for Docker
- [ ] Create `.env.docker`:
  ```bash
  # AI Provider Configuration
  CURRENT_AI_PROVIDER=azure_openai
  AZURE_OPENAI_API_KEY=your-key-here
  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
  AZURE_OPENAI_DEFAULT_DEPLOYMENT_NAME=gpt-4

  # Application Settings
  ENVIRONMENT=production
  DEBUG_MODE=false
  LOG_LEVEL=INFO

  # Path Configuration (for NGINX reverse proxy)
  BASE_URL_PATH=/sageapp04
  ```
- [ ] Add `.env.docker` to `.gitignore`
- [ ] Create `.env.docker.example` with placeholder values

### 7.4 Build Scripts
- [ ] Create `scripts/build-docker.sh`:
  ```bash
  #!/bin/bash
  set -e

  echo "Building SvelteKit Docker image..."
  docker build \
    --file Dockerfile.sveltekit \
    --build-arg BASE_URL_PATH=/sageapp04 \
    --tag word-chatbot:sveltekit \
    --tag word-chatbot:latest \
    .

  echo "Build complete!"
  docker images | grep word-chatbot
  ```
- [ ] Make script executable: `chmod +x scripts/build-docker.sh`

### 7.5 Run Scripts
- [ ] Create `scripts/run-docker.sh`:
  ```bash
  #!/bin/bash
  set -e

  echo "Running SvelteKit container..."
  docker run -d \
    --name word-chatbot \
    -p 127.0.0.1:3004:8000 \
    --env-file .env.docker \
    --restart unless-stopped \
    word-chatbot:sveltekit

  echo "Container started!"
  docker ps | grep word-chatbot

  echo "Logs:"
  docker logs -f word-chatbot
  ```
- [ ] Make script executable

### 7.6 Docker Compose Alternative (Optional)
- [ ] Create `docker-compose.sveltekit.yml`:
  ```yaml
  version: '3.8'

  services:
    app:
      build:
        context: .
        dockerfile: Dockerfile.sveltekit
        args:
          BASE_URL_PATH: /sageapp04
      container_name: word-chatbot
      restart: unless-stopped
      ports:
        - "127.0.0.1:3004:8000"
      env_file:
        - .env.docker
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:8000/"]
        interval: 30s
        timeout: 10s
        retries: 3
  ```
- [ ] Test: `docker compose -f docker-compose.sveltekit.yml up`

### 7.7 Build Optimization
- [ ] Reduce image size:
  - [ ] Use multi-stage build ✓
  - [ ] Use alpine base images where possible
  - [ ] Remove unnecessary dependencies
  - [ ] Minimize layers
  - [ ] Use `.dockerignore` ✓
- [ ] Target image size: <500MB (measure with `docker images`)

### 7.8 Security Hardening
- [ ] Run as non-root user ✓
- [ ] Scan image for vulnerabilities: `docker scan word-chatbot:sveltekit`
- [ ] Use specific base image versions (not `latest`)
- [ ] Minimize exposed ports
- [ ] Review environment variable exposure

---

## Phase 8: Testing & QA

### 8.1 Development Environment Testing
- [ ] Start FastAPI backend: `uvicorn backend.main:app --reload --port 8000`
- [ ] Start SvelteKit dev server: `cd frontend-new && npm run dev`
- [ ] Test basic page load at `http://localhost:5173`
- [ ] Test API proxy to backend
- [ ] Test hot module replacement (HMR)

### 8.2 Feature Testing (Development)
- [ ] **Document Upload**:
  - [ ] Upload valid .docx file
  - [ ] Upload invalid file type (should reject)
  - [ ] Upload large file (>10MB, should warn)
  - [ ] Drag and drop file
  - [ ] Remove selected file
- [ ] **Document Processing**:
  - [ ] Process document with simple instructions
  - [ ] Verify loading state appears
  - [ ] Verify success toast appears
  - [ ] Download processed file
  - [ ] Verify file opens correctly in Word
- [ ] **Document Analysis**:
  - [ ] Analyze document with "Summary" mode
  - [ ] Analyze document with "Raw XML" mode
  - [ ] Verify analysis results display
  - [ ] Copy analysis text
- [ ] **Fallback Document**:
  - [ ] Enable fallback mode
  - [ ] Upload fallback document
  - [ ] Analyze fallback requirements
  - [ ] Process with fallback (append strategy)
  - [ ] Process with fallback (prepend strategy)
  - [ ] Process with fallback (priority strategy)
  - [ ] Verify tracked changes extraction works
- [ ] **LLM Configuration**:
  - [ ] Get current LLM config
  - [ ] Change extraction method to LLM
  - [ ] Change instruction method to LLM
  - [ ] Update configuration
  - [ ] Verify config persists
- [ ] **Debug Modes**:
  - [ ] Enable standard debug mode
  - [ ] Enable extended debug mode
  - [ ] Verify debug info displays
  - [ ] Verify debug expandable sections work

### 8.3 Static Build Testing
- [ ] Run `npm run build` in `frontend-new/`
- [ ] Verify `build/` directory created
- [ ] Check bundle sizes: `ls -lh frontend-new/build/_app/immutable/chunks/`
- [ ] Target: Total JS < 100KB gzipped
- [ ] Run `npm run preview` and test at `http://localhost:4173`
- [ ] Test with base path: `http://localhost:4173/sageapp04/`

### 8.4 Docker Build Testing
- [ ] Build Docker image: `./scripts/build-docker.sh`
- [ ] Verify build succeeds without errors
- [ ] Check image size: `docker images word-chatbot:sveltekit`
- [ ] Run container: `./scripts/run-docker.sh`
- [ ] Check container is running: `docker ps`
- [ ] View logs: `docker logs -f word-chatbot`
- [ ] Test health check: `curl http://localhost:3004/health`

### 8.5 Docker Feature Testing
- [ ] Access UI at `http://localhost:3004/`
- [ ] Test all features listed in 8.2 through Docker container
- [ ] Verify static files load correctly (check browser Network tab)
- [ ] Verify API calls succeed
- [ ] Verify file downloads work
- [ ] Test error scenarios (backend down, network timeout)

### 8.6 Responsive Design Testing
- [ ] Test on desktop (1920x1080, 1366x768)
- [ ] Test on tablet (iPad 768x1024, portrait and landscape)
- [ ] Test on mobile (iPhone 375x667, Android 360x640)
- [ ] Verify sidebar collapses on mobile
- [ ] Verify buttons are touch-friendly (44x44px minimum)
- [ ] Test drag-and-drop on touch devices
- [ ] Verify file upload works on mobile

### 8.7 Browser Compatibility Testing
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest, desktop and iOS)
- [ ] Test file upload in each browser
- [ ] Test file download in each browser

### 8.8 Accessibility Testing
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Screen reader testing (NVDA or JAWS)
- [ ] Color contrast (WCAG AA minimum)
- [ ] Focus indicators visible
- [ ] ARIA labels present
- [ ] Form labels associated correctly
- [ ] Run automated tools (Lighthouse, axe DevTools)

### 8.9 Performance Testing
- [ ] Lighthouse audit (target: >90 performance score)
- [ ] Bundle size analysis (target: <100KB gzipped)
- [ ] Time to Interactive (target: <2 seconds)
- [ ] First Contentful Paint (target: <1 second)
- [ ] Test with slow 3G network
- [ ] Test file upload with 100MB file (should handle gracefully)

### 8.10 Error Handling Testing
- [ ] Network offline (disconnect network)
- [ ] Backend down (stop FastAPI)
- [ ] Invalid API response
- [ ] File upload timeout
- [ ] Invalid file type
- [ ] Corrupted .docx file
- [ ] Verify error toasts appear
- [ ] Verify error messages are user-friendly

---

## Phase 9: VM Deployment

### 9.1 Pre-Deployment Preparation
- [ ] Document current VM configuration
- [ ] Backup current production data
- [ ] Plan deployment window (low-traffic time)
- [ ] Prepare rollback plan
- [ ] Notify users of potential downtime (if any)

### 9.2 NGINX Configuration Review
- [ ] SSH into VM
- [ ] Review current NGINX config: `sudo cat /etc/nginx/sites-available/default`
- [ ] Document current configuration:
  ```nginx
  location = /sageapp04  { return 301 /sageapp04/; }
  location /sageapp04/  { proxy_pass http://127.0.0.1:3004/; }
  ```
- [ ] Determine if nginx-helper is still needed:
  - Current setup: Main NGINX strips prefix (`/sageapp04/` → `/`)
  - nginx-helper adds it back (`/` → `/sageapp04/`)
  - **With SvelteKit**: nginx-helper NOT needed! (SvelteKit handles base path)
- [ ] Plan to remove nginx-helper service

### 9.3 Update NGINX Configuration
- [ ] No changes needed to main NGINX config (IT-managed)
- [ ] Main NGINX will proxy to port 3004
- [ ] Our Docker container will listen on port 3004 (mapped from 8000)
- [ ] SvelteKit will handle `/sageapp04/` prefix via `base` path config
- [ ] Test NGINX config syntax: `sudo nginx -t`

### 9.4 Build Image on VM
- [ ] Option 1: Build directly on VM
  ```bash
  cd /path/to/word-doc-chatbot
  ./scripts/build-docker.sh
  ```
- [ ] Option 2: Build locally and push to registry
  ```bash
  # Local machine
  docker tag word-chatbot:sveltekit myregistry.azurecr.io/word-chatbot:sveltekit
  docker push myregistry.azurecr.io/word-chatbot:sveltekit

  # VM
  docker pull myregistry.azurecr.io/word-chatbot:sveltekit
  docker tag myregistry.azurecr.io/word-chatbot:sveltekit word-chatbot:sveltekit
  ```
- [ ] Choose build approach based on VM resources

### 9.5 Create Production Environment File
- [ ] Create `.env.production` on VM:
  ```bash
  # AI Provider Configuration
  CURRENT_AI_PROVIDER=azure_openai
  AZURE_OPENAI_API_KEY=<actual-key-from-vault>
  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
  AZURE_OPENAI_DEFAULT_DEPLOYMENT_NAME=gpt-4
  AZURE_OPENAI_API_VERSION=2024-02-15-preview

  # Application Settings
  ENVIRONMENT=production
  DEBUG_MODE=false
  LOG_LEVEL=INFO

  # Path Configuration
  BASE_URL_PATH=/sageapp04
  ```
- [ ] Set secure file permissions: `chmod 600 .env.production`
- [ ] Verify API keys are correct and active

### 9.6 Stop Old Services
- [ ] Stop old docker-compose services:
  ```bash
  docker compose down
  ```
- [ ] Verify all old containers stopped: `docker ps`
- [ ] Remove old containers (optional): `docker compose rm`

### 9.7 Deploy New Container
- [ ] Run new SvelteKit container:
  ```bash
  docker run -d \
    --name word-chatbot-sveltekit \
    -p 127.0.0.1:3004:8000 \
    --env-file .env.production \
    --restart unless-stopped \
    word-chatbot:sveltekit
  ```
- [ ] Verify container started: `docker ps | grep word-chatbot`
- [ ] Check logs: `docker logs -f word-chatbot-sveltekit`
- [ ] Verify no startup errors

### 9.8 Verify Internal Access
- [ ] Test health check from VM:
  ```bash
  curl http://localhost:3004/health
  # Expected: {"status":"healthy","version":"4.1.0"}
  ```
- [ ] Test API endpoint:
  ```bash
  curl http://localhost:3004/
  # Expected: HTML content (SvelteKit index.html)
  ```

### 9.9 Verify External Access
- [ ] Open browser to `https://aidemo.dcri.duke.edu/sageapp04/`
- [ ] Verify page loads without errors
- [ ] Open browser DevTools Network tab
- [ ] Verify static files load (JS, CSS)
- [ ] Verify no CORS errors
- [ ] Verify no 404 errors

### 9.10 Smoke Testing in Production
- [ ] Upload a test document
- [ ] Process document with simple instruction
- [ ] Verify processing completes
- [ ] Download processed file
- [ ] Open file in Microsoft Word
- [ ] Verify tracked changes appear correctly
- [ ] Test analysis feature
- [ ] Test fallback document feature (if time permits)

### 9.11 Monitor Logs
- [ ] Watch container logs for 10 minutes:
  ```bash
  docker logs -f word-chatbot-sveltekit
  ```
- [ ] Look for errors or warnings
- [ ] Monitor NGINX access logs:
  ```bash
  sudo tail -f /var/log/nginx/access.log | grep sageapp04
  ```
- [ ] Monitor NGINX error logs:
  ```bash
  sudo tail -f /var/log/nginx/error.log
  ```

### 9.12 Performance Verification
- [ ] Run Lighthouse audit on production URL
- [ ] Verify performance score >90
- [ ] Verify page load time <2 seconds
- [ ] Test from mobile device
- [ ] Verify mobile load time acceptable

### 9.13 Cleanup Old Infrastructure
- [ ] Stop nginx-helper container (if running):
  ```bash
  docker stop nginx-helper
  docker rm nginx-helper
  ```
- [ ] Remove old frontend container
- [ ] Archive old Streamlit code:
  ```bash
  mv frontend frontend-old
  ```
- [ ] Archive old docker-compose.yml:
  ```bash
  mv docker-compose.yml docker-compose.yml.old
  ```
- [ ] Clean up unused Docker images:
  ```bash
  docker image prune -a
  ```

### 9.14 Post-Deployment Verification
- [ ] Test all critical features in production
- [ ] Verify with 2-3 real users
- [ ] Collect initial feedback
- [ ] Monitor for 24 hours
- [ ] Check error logs daily for first week

### 9.15 Rollback Plan (If Needed)
- [ ] Stop new container: `docker stop word-chatbot-sveltekit`
- [ ] Start old services: `docker compose up -d`
- [ ] Verify old version working
- [ ] Investigate issues
- [ ] Plan fix and retry deployment

---

## Phase 10: Documentation

### 10.1 Update README.md
- [ ] Update "Architecture Overview" section:
  - Remove Streamlit references
  - Add SvelteKit + FastAPI architecture
  - Update tech stack list
- [ ] Update "Getting Started" section:
  - Remove Streamlit setup instructions
  - Add SvelteKit development instructions
  - Update Docker build commands
- [ ] Add "Frontend Development" section:
  ```markdown
  ## Frontend Development (SvelteKit)

  ### Prerequisites
  - Node.js 18+ and npm
  - Python 3.11+ (for backend)

  ### Setup
  1. Install dependencies:
     ```bash
     cd frontend-new
     npm install
     ```

  2. Start backend:
     ```bash
     uvicorn backend.main:app --reload --port 8000
     ```

  3. Start frontend dev server:
     ```bash
     npm run dev
     ```

  4. Open http://localhost:5173

  ### Build for Production
  ```bash
  npm run build
  npm run preview  # Test production build locally
  ```
  ```
- [ ] Update deployment section
- [ ] Add migration notes

### 10.2 Update NGINX_DEPLOYMENT_GUIDE.md
- [ ] Remove all nginx-helper references
- [ ] Simplify deployment architecture diagram
- [ ] Update to reflect single Docker container
- [ ] Add SvelteKit-specific notes:
  ```markdown
  ## SvelteKit Deployment (Simplified)

  With SvelteKit, nginx-helper is no longer needed because SvelteKit's
  `base` path configuration handles the `/sageapp04/` prefix natively.

  ### Architecture
  ```
  Browser → Main NGINX → Docker Container (port 3004)
                           ├── FastAPI (port 8000)
                           └── SvelteKit static files
  ```

  The main NGINX configuration remains unchanged:
  ```nginx
  location = /sageapp04  { return 301 /sageapp04/; }
  location /sageapp04/  { proxy_pass http://127.0.0.1:3004/; }
  ```
  ```
- [ ] Remove troubleshooting for nginx-helper

### 10.3 Create SVELTEKIT_MIGRATION.md
- [ ] Document migration rationale
- [ ] Before/after comparison table:
  | Aspect | Streamlit (Before) | SvelteKit (After) |
  |--------|-------------------|-------------------|
  | Framework | Streamlit | SvelteKit |
  | Bundle Size | ~2MB | ~50KB |
  | Load Time | 3-5s | <1s |
  | Concurrent Users | 10-20 | 1000+ |
  | Deployment | 3 containers | 1 container |
  | Mobile Support | Poor | Excellent |
- [ ] Architecture changes
- [ ] Feature parity checklist
- [ ] Performance improvements
- [ ] Developer experience improvements
- [ ] Breaking changes (if any)
- [ ] Migration timeline
- [ ] Lessons learned

### 10.4 Update DOCKER_DEPLOYMENT.md
- [ ] Remove docker-compose multi-container setup
- [ ] Document single-container approach
- [ ] Update deployment instructions:
  ```markdown
  ## Single Container Deployment

  ### Build
  ```bash
  docker build -f Dockerfile.sveltekit -t word-chatbot:sveltekit .
  ```

  ### Run
  ```bash
  docker run -d \
    --name word-chatbot \
    -p 127.0.0.1:3004:8000 \
    --env-file .env.production \
    --restart unless-stopped \
    word-chatbot:sveltekit
  ```

  ### Verify
  ```bash
  docker logs -f word-chatbot
  curl http://localhost:3004/health
  ```
  ```
- [ ] Add multi-stage build explanation
- [ ] Document environment variables
- [ ] Add troubleshooting section

### 10.5 Update CLAUDE.md
- [ ] Update "Project Overview" section
- [ ] Replace Streamlit references with SvelteKit
- [ ] Update "Key Commands" section:
  ```markdown
  ### Frontend Development
  ```bash
  # Navigate to frontend
  cd frontend-new

  # Install dependencies
  npm install

  # Start dev server
  npm run dev  # Opens on http://localhost:5173

  # Build for production
  npm run build

  # Preview production build
  npm run preview
  ```

  ### Docker (Single Container)
  ```bash
  # Build
  docker build -f Dockerfile.sveltekit -t word-chatbot:sveltekit .

  # Run
  docker run -d -p 3004:8000 --env-file .env word-chatbot:sveltekit

  # Logs
  docker logs -f word-chatbot
  ```
  ```
- [ ] Update "Architecture Overview" section
- [ ] Update frontend structure documentation
- [ ] Add SvelteKit component structure
- [ ] Update development workflow

### 10.6 Create AZURE_DEPLOYMENT.md
- [ ] Document Azure Web App deployment steps:
  ```markdown
  # Azure Web App Deployment Guide

  ## Prerequisites
  - Azure subscription
  - Azure Container Registry (ACR)
  - Azure Web App (Linux, Docker container)

  ## Step 1: Create Azure Container Registry
  ```bash
  az acr create \
    --resource-group myResourceGroup \
    --name myregistry \
    --sku Basic
  ```

  ## Step 2: Build and Push Image
  ```bash
  # Login to ACR
  az acr login --name myregistry

  # Build and push
  docker build -f Dockerfile.sveltekit -t myregistry.azurecr.io/word-chatbot:latest .
  docker push myregistry.azurecr.io/word-chatbot:latest
  ```

  ## Step 3: Create Web App
  ```bash
  az webapp create \
    --resource-group myResourceGroup \
    --plan myAppServicePlan \
    --name word-chatbot \
    --deployment-container-image-name myregistry.azurecr.io/word-chatbot:latest
  ```

  ## Step 4: Configure Environment Variables
  Navigate to Azure Portal → Web App → Configuration → Application Settings
  Add:
  - `CURRENT_AI_PROVIDER`: azure_openai
  - `AZURE_OPENAI_API_KEY`: (from Key Vault)
  - `AZURE_OPENAI_ENDPOINT`: https://...
  - `BASE_URL_PATH`: / (Azure handles routing at root)
  - `WEBSITES_PORT`: 8000 (Azure expects this)

  ## Step 5: Enable Continuous Deployment (Optional)
  Configure webhook from ACR to Web App for auto-deploy on push.
  ```
- [ ] Add troubleshooting section
- [ ] Document scaling settings
- [ ] Add monitoring recommendations

### 10.7 Update API Documentation
- [ ] Update `backend/main.py` docstrings
- [ ] Ensure all endpoints have clear descriptions
- [ ] Add response examples
- [ ] Update OpenAPI schema if customized
- [ ] Generate API docs: Access `/docs` endpoint

### 10.8 Create Frontend Documentation
- [ ] Create `frontend-new/README.md`:
  ```markdown
  # Word Document Chatbot - Frontend

  SvelteKit-based frontend for document processing application.

  ## Tech Stack
  - SvelteKit 2.0
  - TypeScript
  - Tailwind CSS
  - Skeleton UI

  ## Development
  See [main README](../README.md) for setup instructions.

  ## Project Structure
  ```
  src/
  ├── lib/
  │   ├── components/       # UI components
  │   ├── stores/          # State management
  │   ├── api/             # API client
  │   └── utils/           # Utilities
  └── routes/              # Pages
  ```

  ## Component Library
  See [COMPONENTS.md](./COMPONENTS.md) for component documentation.
  ```
- [ ] Create component catalog (optional but helpful)

### 10.9 Create Troubleshooting Guide
- [ ] Create `TROUBLESHOOTING.md`:
  - Common issues and solutions
  - Docker build failures
  - NGINX configuration issues
  - File upload problems
  - API timeout issues
  - Mobile-specific issues
- [ ] Add FAQ section

### 10.10 Update IMPLEMENTATION_SUMMARY.md
- [ ] Add SvelteKit migration section
- [ ] Document new architecture
- [ ] Update technology stack
- [ ] Add performance metrics
- [ ] Document lessons learned

---

## Phase 11: Cleanup & Optimization

### 11.1 Code Cleanup
- [ ] Remove unused imports in all files
- [ ] Remove console.log statements
- [ ] Remove commented-out code
- [ ] Fix linting errors: `npm run lint` (if configured)
- [ ] Format code: `npm run format` (Prettier)
- [ ] Remove TODO comments (or create issues for them)

### 11.2 Performance Optimization
- [ ] Analyze bundle size: `npm run build` and check output
- [ ] Identify large dependencies
- [ ] Consider code splitting for large routes (if any)
- [ ] Optimize images in `static/` folder
- [ ] Enable compression in NGINX (gzip)
- [ ] Add caching headers for static assets
- [ ] Lazy load heavy components

### 11.3 Accessibility Audit
- [ ] Run Lighthouse accessibility audit
- [ ] Fix any violations
- [ ] Test with keyboard navigation
- [ ] Test with screen reader
- [ ] Verify all images have alt text
- [ ] Verify all forms have labels
- [ ] Check color contrast ratios

### 11.4 Security Review
- [ ] Review environment variables (no secrets in code)
- [ ] Check for XSS vulnerabilities
- [ ] Validate all user inputs
- [ ] Review API authentication (if applicable)
- [ ] Check CORS configuration
- [ ] Review Docker image security
- [ ] Run security scan: `npm audit`
- [ ] Update dependencies: `npm update`

### 11.5 Dependency Updates
- [ ] Update outdated npm packages:
  ```bash
  npm outdated
  npm update
  ```
- [ ] Update Python dependencies:
  ```bash
  pip list --outdated
  # Update requirements.txt
  ```
- [ ] Test after updates

### 11.6 Archive Old Code
- [ ] Move `frontend/` to `frontend-streamlit-old/`
- [ ] Move `docker-compose.yml` to `archive/docker-compose.yml.old`
- [ ] Move `nginx-helper-docker.conf` to `archive/`
- [ ] Update `.gitignore` to ignore `*-old/` directories
- [ ] Commit archive changes:
  ```bash
  git add .
  git commit -m "chore: Archive old Streamlit frontend"
  ```

### 11.7 Git Cleanup
- [ ] Create `.gitattributes` for LFS (if large files)
- [ ] Review `.gitignore` completeness
- [ ] Remove committed `.env` files (if any - CRITICAL!)
- [ ] Create proper Git tags for release:
  ```bash
  git tag -a v2.0.0 -m "SvelteKit migration complete"
  git push origin v2.0.0
  ```

### 11.8 Documentation Review
- [ ] Proofread all updated documentation
- [ ] Verify all code examples work
- [ ] Check for broken links
- [ ] Ensure consistent formatting
- [ ] Add table of contents where needed
- [ ] Review for clarity and completeness

### 11.9 Testing Review
- [ ] Verify all tests pass (if unit tests exist)
- [ ] Review test coverage
- [ ] Add missing critical tests
- [ ] Document manual testing checklist

### 11.10 Final Checks
- [ ] All TODO items in task list completed
- [ ] All success criteria met
- [ ] Deployment verified on VM
- [ ] Documentation complete
- [ ] Stakeholders informed
- [ ] Rollback plan documented

---

## Phase 12: Azure Preparation

### 12.1 Azure Container Registry Setup
- [ ] Create ACR instance in Azure Portal
- [ ] Document ACR login credentials
- [ ] Configure ACR access from local machine
- [ ] Test push/pull from ACR
- [ ] Create service principal for CI/CD (optional)

### 12.2 Azure Web App Configuration Planning
- [ ] Choose App Service Plan (tier and size)
- [ ] Plan resource group structure
- [ ] Document environment variables needed
- [ ] Plan scaling rules (if needed)
- [ ] Plan backup strategy
- [ ] Plan monitoring/logging strategy

### 12.3 Build Image for Azure
- [ ] Modify Dockerfile if needed for Azure specifics
- [ ] Build image with Azure-specific settings:
  ```bash
  docker build \
    -f Dockerfile.sveltekit \
    --build-arg BASE_URL_PATH=/ \
    -t myregistry.azurecr.io/word-chatbot:latest \
    .
  ```
- [ ] Tag for versioning:
  ```bash
  docker tag myregistry.azurecr.io/word-chatbot:latest \
             myregistry.azurecr.io/word-chatbot:v2.0.0
  ```

### 12.4 Push to Azure Container Registry
- [ ] Login to ACR:
  ```bash
  az acr login --name myregistry
  ```
- [ ] Push image:
  ```bash
  docker push myregistry.azurecr.io/word-chatbot:latest
  docker push myregistry.azurecr.io/word-chatbot:v2.0.0
  ```
- [ ] Verify image in ACR:
  ```bash
  az acr repository list --name myregistry
  az acr repository show-tags --name myregistry --repository word-chatbot
  ```

### 12.5 Create Azure Web App
- [ ] Create via Azure Portal or CLI:
  ```bash
  az webapp create \
    --resource-group word-chatbot-rg \
    --plan word-chatbot-plan \
    --name word-chatbot-app \
    --deployment-container-image-name myregistry.azurecr.io/word-chatbot:latest
  ```
- [ ] Configure container settings
- [ ] Set `WEBSITES_PORT=8000`
- [ ] Enable container logging

### 12.6 Configure Environment Variables
- [ ] Add via Azure Portal → Configuration → Application Settings:
  - `CURRENT_AI_PROVIDER`
  - `AZURE_OPENAI_API_KEY` (link to Key Vault recommended)
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_DEFAULT_DEPLOYMENT_NAME`
  - `BASE_URL_PATH=/` (Azure handles routing)
  - `ENVIRONMENT=production`
  - `LOG_LEVEL=INFO`
- [ ] Save and restart Web App

### 12.7 Configure Continuous Deployment (Optional)
- [ ] Enable webhook from ACR to Web App
- [ ] Configure GitHub Actions for CI/CD:
  ```yaml
  name: Deploy to Azure
  on:
    push:
      branches: [main]

  jobs:
    build-and-deploy:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v2
        - name: Build and push to ACR
          # ... build steps ...
        - name: Deploy to Azure Web App
          # ... deployment steps ...
  ```
- [ ] Test CI/CD pipeline

### 12.8 Configure Custom Domain (Optional)
- [ ] Add custom domain in Azure Portal
- [ ] Configure DNS records
- [ ] Enable HTTPS with managed certificate
- [ ] Test access via custom domain

### 12.9 Configure Monitoring
- [ ] Enable Application Insights
- [ ] Configure log streaming
- [ ] Set up alerts for errors
- [ ] Create dashboard for metrics
- [ ] Test monitoring setup

### 12.10 Performance Testing in Azure
- [ ] Run load testing
- [ ] Verify auto-scaling works (if configured)
- [ ] Check response times
- [ ] Monitor resource usage
- [ ] Optimize based on findings

### 12.11 Security Configuration
- [ ] Enable managed identity
- [ ] Configure Key Vault for secrets
- [ ] Set up network restrictions (if needed)
- [ ] Enable diagnostic logging
- [ ] Review security recommendations

### 12.12 Documentation
- [ ] Complete AZURE_DEPLOYMENT.md
- [ ] Document deployment process
- [ ] Document rollback procedure
- [ ] Create runbook for common tasks
- [ ] Share with team

---

## 🎯 Success Criteria Verification

### Final Checklist
- [ ] ✅ Single Docker container (no docker-compose required)
- [ ] ✅ Works on VM with NGINX reverse proxy on port 3004
- [ ] ✅ Path prefix `/sageapp04/` handled correctly
- [ ] ✅ All Streamlit features replicated:
  - [ ] Document upload and processing
  - [ ] Document analysis (summary and raw XML)
  - [ ] Fallback document support
  - [ ] Tracked changes extraction
  - [ ] LLM configuration
  - [ ] Debug modes
  - [ ] File download
- [ ] ✅ Mobile-friendly UI (responsive, touch-optimized)
- [ ] ✅ Fast page load (<1 second)
- [ ] ✅ Small bundle size (<100KB gzipped)
- [ ] ✅ Ready for Azure Web Apps
- [ ] ✅ Improved UX over Streamlit
- [ ] ✅ Clean, maintainable code
- [ ] ✅ Complete documentation
- [ ] ✅ Passing accessibility audit
- [ ] ✅ Passing performance audit
- [ ] ✅ Production-stable (no critical bugs)

---

## 📊 Timeline & Effort Estimates

| Phase | Duration | Complexity | Priority |
|-------|----------|------------|----------|
| 0. Pre-Migration Planning | 0.5 day | Low | High |
| 1. SvelteKit Setup | 1 day | Low | High |
| 2. Core UI Components | 1.5 days | Medium | High |
| 3. Feature Components | 2 days | Medium | High |
| 4. API Integration | 1 day | Medium | High |
| 5. State Management | 0.5 day | Low | High |
| 6. FastAPI Updates | 0.5 day | Low | High |
| 7. Docker Single Container | 1 day | Medium | High |
| 8. Testing & QA | 1.5 days | Medium | High |
| 9. VM Deployment | 1 day | Medium | High |
| 10. Documentation | 1 day | Low | High |
| 11. Cleanup & Optimization | 1 day | Low | Medium |
| 12. Azure Preparation | 1 day | Medium | Low |
| **Total** | **13-14 days** | | |

**Notes:**
- Assumes full-time dedicated work
- Estimates may vary based on experience with SvelteKit
- Buffer included for unexpected issues
- Azure preparation (Phase 12) can be done later if needed

---

## 🚀 Quick Start (Day 1)

To get started immediately:

1. **Initialize SvelteKit** (Phase 1.1-1.2):
   ```bash
   npx sv create frontend-new
   cd frontend-new
   npm install
   npm install -D @skeletonlabs/skeleton @skeletonlabs/tw-plugin
   ```

2. **Configure basics** (Phase 1.3-1.7):
   - Update `svelte.config.js`
   - Create `tailwind.config.js`
   - Set up environment variables

3. **Test dev server**:
   ```bash
   npm run dev
   ```

4. **Start building components** (Phase 2):
   - Begin with layout and header
   - Add file upload component
   - Build incrementally

Good luck! 🎉
