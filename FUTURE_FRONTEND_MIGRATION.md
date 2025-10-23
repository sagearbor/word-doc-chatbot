# Future Frontend Migration Guide

## Overview

This guide provides a roadmap for migrating from Streamlit to a more scalable frontend framework when you're ready to support 1000+ concurrent users.

## Why Migrate from Streamlit?

### Current Limitations
- **Performance**: Streamlit reruns entire script on every interaction
- **Concurrency**: Session state issues with multiple concurrent users
- **Bundle Size**: Heavy framework (large initial load)
- **WebSocket overhead**: Maintains persistent connection for each user
- **Limited control**: Difficult to customize UI/UX beyond Streamlit components

### When to Migrate
- When you need to support 100+ concurrent users
- When performance becomes noticeably slow
- When you need more UI customization
- When API access becomes primary use case
- When Streamlit's footprint is too large for your deployment

## Good News: Backend is Ready!

Your FastAPI backend already has all the endpoints needed:

```python
# backend/main.py
@app.post("/process-document/")                  # Basic processing
@app.post("/process-document-with-fallback/")   # With fallback doc
@app.post("/analyze-document/")                  # Analyze existing changes
@app.get("/")                                    # Health check
```

**No backend changes needed!** Just build a new frontend that calls these endpoints.

---

## Recommended Tech Stack

### Option 1: SvelteKit (⭐ Recommended for Readability)

**Why SvelteKit:**
- ✅ Extremely readable code (looks like enhanced HTML)
- ✅ Less boilerplate than React
- ✅ Built-in form handling and file uploads
- ✅ Server-side rendering (SSR) for better performance
- ✅ Smaller bundle size
- ✅ Easy to learn if you know HTML/CSS/JS

**Best for:** Teams that value code readability and fast development

**Example Component:**
```svelte
<!-- routes/+page.svelte -->
<script>
  let file;
  let instructions = '';
  let processing = false;
  let result = null;

  async function processDocument() {
    processing = true;
    const formData = new FormData();
    formData.append('input_file', file[0]);
    formData.append('user_instructions', instructions);

    const response = await fetch('http://localhost:8004/process-document/', {
      method: 'POST',
      body: formData
    });

    result = await response.json();
    processing = false;
  }
</script>

<h1>Word Document Processor</h1>

<form on:submit|preventDefault={processDocument}>
  <label>
    Upload Document:
    <input type="file" bind:files={file} accept=".docx" required />
  </label>

  <label>
    Instructions:
    <textarea bind:value={instructions} placeholder="Enter editing instructions..."></textarea>
  </label>

  <button type="submit" disabled={processing}>
    {processing ? 'Processing...' : 'Process Document'}
  </button>
</form>

{#if result}
  <div class="results">
    <h2>Results</h2>
    <p>Status: {result.status_message}</p>
    <p>Edits Applied: {result.edits_applied_count}</p>
    <a href={result.download_url} download>Download Processed Document</a>
  </div>
{/if}

<style>
  /* Simple, scoped styles */
  form {
    max-width: 600px;
    margin: 2rem auto;
  }
  label {
    display: block;
    margin: 1rem 0;
  }
  button {
    padding: 0.5rem 1rem;
    background: #007bff;
    color: white;
    border: none;
    cursor: pointer;
  }
</style>
```

**UI Component Library:**
- **Skeleton UI** - Beautiful, professional Duke-appropriate design
- **daisyUI** - Simple, Tailwind-based components

---

### Option 2: Next.js (Industry Standard)

**Why Next.js:**
- ✅ Large community and ecosystem
- ✅ Excellent documentation
- ✅ Built-in API routes (could eventually replace FastAPI if needed)
- ✅ Many pre-built UI component libraries
- ✅ Server-side rendering and static generation

**Best for:** Teams that prioritize ecosystem size and long-term support

**Example Component:**
```typescript
// app/page.tsx
'use client';

import { useState } from 'react';

export default function DocumentProcessor() {
  const [file, setFile] = useState<File | null>(null);
  const [instructions, setInstructions] = useState('');
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);

  const processDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    setProcessing(true);

    const formData = new FormData();
    if (file) formData.append('input_file', file);
    formData.append('user_instructions', instructions);

    const response = await fetch('http://localhost:8004/process-document/', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    setResult(data);
    setProcessing(false);
  };

  return (
    <div className="container">
      <h1>Word Document Processor</h1>

      <form onSubmit={processDocument}>
        <label>
          Upload Document:
          <input
            type="file"
            accept=".docx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            required
          />
        </label>

        <label>
          Instructions:
          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Enter editing instructions..."
          />
        </label>

        <button type="submit" disabled={processing}>
          {processing ? 'Processing...' : 'Process Document'}
        </button>
      </form>

      {result && (
        <div className="results">
          <h2>Results</h2>
          <p>Status: {result.status_message}</p>
          <p>Edits Applied: {result.edits_applied_count}</p>
          <a href={result.download_url} download>
            Download Processed Document
          </a>
        </div>
      )}
    </div>
  );
}
```

**UI Component Library:**
- **shadcn/ui** - Modern, customizable (⭐ trending)
- **Material-UI** - Google's design system, very polished
- **Chakra UI** - Simple, accessible

---

## Migration Roadmap

### Phase 1: Setup (Week 1, Days 1-2)

**SvelteKit:**
```bash
# Create new SvelteKit project
npm create svelte@latest frontend-new
cd frontend-new
npm install

# Add UI library
npm install -D @skeletonlabs/skeleton
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Next.js:**
```bash
# Create new Next.js project
npx create-next-app@latest frontend-new
cd frontend-new

# Add UI library (shadcn/ui)
npx shadcn-ui@latest init
```

### Phase 2: Core Features (Week 1, Days 3-7)

Build the main features in order of priority:

1. **Document Upload & Processing** (Day 3)
   - File upload component
   - Form handling
   - API call to `/process-document/`
   - Download processed document

2. **Fallback Document Support** (Day 4)
   - Second file upload for fallback
   - Checkbox to enable fallback mode
   - API call to `/process-document-with-fallback/`

3. **Document Analysis** (Day 5)
   - Upload for analysis
   - Display tracked changes
   - API call to `/analyze-document/`

4. **UI Polish** (Days 6-7)
   - Loading states
   - Error handling
   - Success/failure messages
   - Responsive design

### Phase 3: Testing & Deployment (Week 2)

1. **Testing** (Days 1-2)
   - Unit tests for components
   - Integration tests with backend
   - Load testing with 100+ concurrent users

2. **Docker Configuration** (Day 3)
   - Create Dockerfile for frontend
   - Update docker-compose.yml
   - Test full stack deployment

3. **Deployment** (Days 4-5)
   - Deploy to VM
   - Configure NGINX
   - Monitor performance
   - Gather user feedback

---

## Code Comparison: Streamlit vs SvelteKit vs Next.js

### Current Streamlit Code (frontend/streamlit_app.py)
```python
import streamlit as st
import requests

st.title("Word Document Processor")

uploaded_file = st.file_uploader("Upload .docx file", type="docx")
instructions = st.text_area("Instructions")

if st.button("Process"):
    if uploaded_file:
        files = {"input_file": uploaded_file}
        data = {"user_instructions": instructions}
        response = requests.post(f"{BACKEND_URL}/process-document/", files=files, data=data)
        result = response.json()
        st.success(f"Processed! {result['status_message']}")
```

**Lines of code:** ~150 for full app

### SvelteKit Version
**Lines of code:** ~120 for full app (20% less)
**Bundle size:** ~50KB (vs Streamlit's ~2MB)
**Load time:** <1s (vs Streamlit's 3-5s)

### Next.js Version
**Lines of code:** ~180 for full app (similar to Streamlit)
**Bundle size:** ~200KB
**Load time:** 1-2s

---

## Architecture After Migration

### Current Architecture (Streamlit)
```
┌─────────────────┐      ┌─────────────────┐
│  Frontend       │      │  Backend        │
│  (Streamlit)    │─────▶│  (FastAPI)      │
│  Port 8501      │ WSS  │  Port 8004      │
│  Heavy          │      │  API            │
└─────────────────┘      └─────────────────┘
```

### Future Architecture (SvelteKit/Next.js)
```
┌─────────────────┐      ┌─────────────────┐
│  Frontend       │      │  Backend        │
│  (SvelteKit)    │─────▶│  (FastAPI)      │
│  Port 3000      │ HTTP │  Port 8004      │
│  Lightweight    │      │  API            │
└─────────────────┘      └─────────────────┘
```

### Docker Compose After Migration
```yaml
services:
  backend:
    build:
      context: .
      target: backend
    ports:
      - "8004:8004"
    environment:
      - CURRENT_AI_PROVIDER=${CURRENT_AI_PROVIDER}
      # ... other vars

  frontend:
    build:
      context: ./frontend-new
    ports:
      - "3004:3000"  # SvelteKit/Next.js default port
    environment:
      - BACKEND_URL=http://backend:8004
    depends_on:
      - backend

  # nginx-helper still needed if behind reverse proxy
  nginx-helper:
    image: nginx:alpine
    ports:
      - "127.0.0.1:3004:80"
    # ...
```

---

## Performance Comparison

| Metric | Streamlit | SvelteKit | Next.js |
|--------|-----------|-----------|---------|
| Initial Load | 3-5s | <1s | 1-2s |
| Bundle Size | ~2MB | ~50KB | ~200KB |
| Concurrent Users | 10-20 | 1000+ | 1000+ |
| Memory per User | ~50MB | ~5MB | ~10MB |
| Server Resources | High | Low | Medium |

---

## API Compatibility

Your FastAPI backend is already 100% compatible. No changes needed!

All endpoints work with standard HTTP multipart/form-data:

```javascript
// Works with any frontend framework
const formData = new FormData();
formData.append('input_file', fileInput.files[0]);
formData.append('user_instructions', instructionsText);
formData.append('author_name', 'AI Reviewer');
formData.append('case_sensitive', true);
formData.append('add_comments', true);

const response = await fetch('http://localhost:8004/process-document/', {
  method: 'POST',
  body: formData
});

const result = await response.json();
```

---

## Migration Checklist

### Before Migration
- [ ] Backend is stable and well-documented
- [ ] All Streamlit features are documented
- [ ] User feedback collected on current UI
- [ ] Performance requirements defined (concurrent users, load time)

### During Migration
- [ ] Choose framework (SvelteKit or Next.js)
- [ ] Set up new frontend project
- [ ] Install UI component library
- [ ] Implement core features (upload, process, download)
- [ ] Implement fallback document support
- [ ] Implement document analysis
- [ ] Add loading states and error handling
- [ ] Write tests
- [ ] Create Dockerfile for new frontend
- [ ] Update docker-compose.yml

### After Migration
- [ ] Load testing with 100+ concurrent users
- [ ] Deploy to staging environment
- [ ] User acceptance testing
- [ ] Update documentation
- [ ] Deploy to production
- [ ] Monitor performance
- [ ] Remove Streamlit code (archive in git)

---

## Keeping Streamlit (Alternative)

If you decide to keep Streamlit for now:

### Improvements to Make
1. **Session state management**: Use `st.session_state` properly
2. **Caching**: Add `@st.cache_data` and `@st.cache_resource`
3. **Async processing**: Use `st.spinner()` and background tasks
4. **Resource limits**: Set container memory/CPU limits

### When Streamlit is Good Enough
- Fewer than 50 concurrent users
- Internal tool for researchers only
- Budget/time constraints prevent migration
- UI customization not critical

---

## Recommendation

**Start with:** SvelteKit + Skeleton UI

**Why:**
1. **Most readable code** - easy to maintain
2. **Fastest to develop** - less boilerplate
3. **Best performance** - smallest bundle
4. **Perfect for your use case** - form-heavy application

**Timeline:** 1-2 weeks for full migration

**Effort:** Low-Medium (backend is already ready!)

---

## Resources

### SvelteKit
- **Official Tutorial:** https://learn.svelte.dev/
- **Skeleton UI Docs:** https://www.skeleton.dev/
- **File Upload Example:** https://kit.svelte.dev/docs/form-actions

### Next.js
- **Official Tutorial:** https://nextjs.org/learn
- **shadcn/ui Docs:** https://ui.shadcn.com/
- **File Upload Example:** https://github.com/vercel/next.js/tree/canary/examples/upload

### Testing
- **Playwright:** https://playwright.dev/ (E2E testing)
- **Vitest:** https://vitest.dev/ (Unit testing)

---

## Questions?

When you're ready to start the migration, consider:

1. **Timeline:** When do you need to scale to 100+ users?
2. **Resources:** How many developers available for migration?
3. **Priorities:** Is readability or ecosystem size more important?
4. **Risk tolerance:** Can you run Streamlit and new frontend in parallel?

The migration is straightforward because:
- ✅ Backend has all the APIs needed
- ✅ UI is simple (file upload, text input, display results)
- ✅ No complex state management needed
- ✅ Well-defined requirements from existing Streamlit app

Good luck! 🚀
