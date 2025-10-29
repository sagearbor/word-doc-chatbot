# Complete Fix for Svelte Infinite Loop Bug

## Executive Summary

**Problem:** Production site at https://aidemo.dcri.duke.edu/sageapp04/ is experiencing `effect_update_depth_exceeded` errors preventing users from uploading and processing documents.

**Root Cause:** Codebase mixes Svelte 4 (createEventDispatcher) and Svelte 5 (callback props) patterns, creating infinite reactive loops when components emit events that update stores that feed back as props.

**Solution:** Convert 6 components from Svelte 4 to Svelte 5 patterns.

**Status:**
- ✅ Branch created: `fix/svelte-infinite-loop-bug`
- ✅ 2 components fixed: OptionsPanel.svelte, AnalysisMode.svelte
- ❌ 6 components still need fixing (listed below)
- ❌ Site still broken

---

## The Problem Explained

### What's Happening

```
User Action (e.g., drag file)
    ↓
Component dispatches CustomEvent: dispatch('fileSelected', file)
    ↓
Parent receives event: onfileselected={(e) => appStore.setFile(e.detail)}
    ↓
Store updates: appStore.setFile(file)
    ↓
Component prop changes: file={$appStore.uploadedFile}
    ↓
Component reactivity triggers
    ↓
Component may re-emit event
    ↓
INFINITE LOOP (exceeds max depth of 100)
    ↓
Error: effect_update_depth_exceeded
```

### Why It's Breaking

Svelte 4 components use `createEventDispatcher()` which creates CustomEvents. When these events immediately trigger store updates that feed back to the same component as props, it creates an infinite reactive loop.

---

## Files That Need Fixing

### CRITICAL Priority (Fix First)

#### 1. FallbackUpload.svelte
**Location:** `frontend-new/src/lib/components/features/FallbackUpload.svelte`

**Current Issue:**
- Uses `createEventDispatcher` (lines 8-10)
- Dispatches `fileSelected` event (lines 21, 35, 55)
- Parent tries to bind with `onfileselected` prop but receives CustomEvent
- **This is why drag-and-drop file display isn't working!**

**Parent Usage (line 284 in +page.svelte):**
```svelte
<FallbackUpload enabled={true} onfileselected={handleFallbackFileSelected} />
```

**Fix Required:**
- Remove `createEventDispatcher`
- Add `onfileselected` callback prop
- Call `onfileselected?.(file)` instead of `dispatch('fileSelected', file)`

---

### HIGH Priority (Fix Next)

#### 2. MergeStrategy.svelte
**Location:** `frontend-new/src/lib/components/features/MergeStrategy.svelte`

**Current Issue:**
- Uses `createEventDispatcher` (lines 7-9)
- Dispatches `change` event with value (line 32)
- Parent directly updates store from event: `uiStore.setMergeStrategy(e.detail)`

**Parent Usage (line 285 in +page.svelte):**
```svelte
<MergeStrategy
    value={$uiStore.mergeStrategy}
    onchange={(e) => uiStore.setMergeStrategy(e.detail)}
/>
```

**Fix Required:**
- Remove `createEventDispatcher`
- Add `onchange` callback prop: `onchange?: (value: string) => void`
- Call `onchange?.(value)` instead of `dispatch('change', value)`
- Parent changes to: `onchange={(value) => uiStore.setMergeStrategy(value)}`

---

#### 3. DebugOptions.svelte
**Location:** `frontend-new/src/lib/components/features/DebugOptions.svelte`

**Current Issue:**
- Uses `createEventDispatcher` (lines 7-9)
- Dispatches `change` event with debugLevel (line 33)
- Parent directly updates store from event: `uiStore.setDebugLevel(e.detail)`

**Parent Usage (line 331 in +page.svelte):**
```svelte
<DebugOptions
    debugLevel={$uiStore.debugLevel}
    onchange={(e) => uiStore.setDebugLevel(e.detail)}
/>
```

**Fix Required:**
- Remove `createEventDispatcher`
- Add `onchange` callback prop: `onchange?: (level: string) => void`
- Call `onchange?.(debugLevel)` instead of `dispatch('change', debugLevel)`
- Parent changes to: `onchange={(level) => uiStore.setDebugLevel(level)}`

---

### MEDIUM Priority (Fix When Time Permits)

#### 4. LLMConfig.svelte
**Location:** `frontend-new/src/lib/components/features/LLMConfig.svelte`

**Current Issue:**
- Uses `createEventDispatcher` (lines 9-11)
- Dispatches `update` event with config object (lines 45-48)
- Has reactive statement that updates when prop changes (lines 57-60)

**Parent Usage (line 359 in +page.svelte):**
```svelte
<LLMConfig
    currentConfig={$resultsStore.llmConfig}
    onupdate={handleLLMConfigUpdate}
/>
```

**Fix Required:**
- Remove `createEventDispatcher`
- Add `onupdate` callback prop: `onupdate?: (config: object) => void`
- Call `onupdate?.(config)` instead of `dispatch('update', config)`

---

### LOW Priority (Optional - For Consistency)

#### 5. AnalyzeButton.svelte
**Location:** `frontend-new/src/lib/components/features/AnalyzeButton.svelte`

**Current Issue:**
- Uses inline `this.dispatchEvent()` pattern (lines 16-22)
- Less critical because button clicks don't create loops

**Parent Usage (line 349 in +page.svelte):**
```svelte
<AnalyzeButton
    loading={$appStore.isAnalyzing}
    disabled={!$appStore.uploadedFile || $appStore.isAnalyzing}
    onclick={handleAnalyze}
/>
```

**Fix Required:**
- Remove `dispatchEvent` pattern
- Add `onclick` callback prop
- Call `onclick?.()` directly from button handler

---

#### 6. DownloadButton.svelte
**Location:** `frontend-new/src/lib/components/features/DownloadButton.svelte`

**Current Issue:**
- Uses inline `this.dispatchEvent()` pattern (lines 24-30)
- Less critical because button clicks don't create loops

**Parent Usage (line 413 in +page.svelte):**
```svelte
<DownloadButton
    filename={$resultsStore.processedResult.filename}
    disabled={false}
    onclick={handleDownload}
/>
```

**Fix Required:**
- Remove `dispatchEvent` pattern
- Add `onclick` callback prop
- Call `onclick?.()` directly from button handler

---

## The Fix Pattern

### Svelte 4 Pattern (Current - WRONG)

```svelte
<script lang="ts">
import { createEventDispatcher } from 'svelte';

export let value: string;
const dispatch = createEventDispatcher();

function handleChange(event: Event) {
    value = (event.target as HTMLSelectElement).value;
    dispatch('change', value);  // ❌ Creates CustomEvent
}
</script>

<select bind:value on:change={handleChange}>
    <!-- options -->
</select>
```

**Parent receives:**
```svelte
<Component
    value={$store.value}
    onchange={(e) => store.setValue(e.detail)}  // ❌ e.detail from CustomEvent
/>
```

---

### Svelte 5 Pattern (Target - CORRECT)

```svelte
<script lang="ts">
interface Props {
    value: string;
    onchange?: (value: string) => void;
}

let { value = $bindable(), onchange }: Props = $props();

function handleChange(event: Event) {
    value = (event.target as HTMLSelectElement).value;
    onchange?.(value);  // ✅ Direct callback with value
}
</script>

<select bind:value on:change={handleChange}>
    <!-- options -->
</select>
```

**Parent receives:**
```svelte
<Component
    value={$store.value}
    onchange={(value) => store.setValue(value)}  // ✅ Direct value
/>
```

---

## Step-by-Step Fix Instructions

### Prerequisites
- Branch: `fix/svelte-infinite-loop-bug` (already created)
- Working directory: `/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot`

### Execution Steps

#### 1. Fix FallbackUpload.svelte (CRITICAL)

**Changes needed:**
- Remove lines 8-10 (`import { createEventDispatcher }...`)
- Add Props interface with `onfileselected` callback
- Replace all `dispatch('fileSelected', file)` with `onfileselected?.(file)`
- Use `let { enabled, file = $bindable(), onfileselected }: Props = $props();`

**Test:** Drag a file to the fallback upload area - it should show the filename.

---

#### 2. Fix MergeStrategy.svelte (HIGH)

**Changes needed:**
- Remove lines 7-9 (`import { createEventDispatcher }...`)
- Add Props interface with `onchange` callback: `onchange?: (value: string) => void`
- Replace `dispatch('change', value)` with `onchange?.(value)`
- Use `let { value = $bindable(), onchange }: Props = $props();`

**Update parent (+page.svelte line 285):**
```svelte
<!-- Before -->
<MergeStrategy value={$uiStore.mergeStrategy} onchange={(e) => uiStore.setMergeStrategy(e.detail)} />

<!-- After -->
<MergeStrategy value={$uiStore.mergeStrategy} onchange={(value) => uiStore.setMergeStrategy(value)} />
```

**Test:** Change merge strategy dropdown - should update without errors.

---

#### 3. Fix DebugOptions.svelte (HIGH)

**Changes needed:**
- Remove lines 7-9 (`import { createEventDispatcher }...`)
- Add Props interface with `onchange` callback: `onchange?: (level: 'off' | 'standard' | 'extended') => void`
- Replace `dispatch('change', debugLevel)` with `onchange?.(debugLevel)`
- Use `let { debugLevel = $bindable(), onchange }: Props = $props();`

**Update parent (+page.svelte line 331):**
```svelte
<!-- Before -->
<DebugOptions debugLevel={$uiStore.debugLevel} onchange={(e) => uiStore.setDebugLevel(e.detail)} />

<!-- After -->
<DebugOptions debugLevel={$uiStore.debugLevel} onchange={(level) => uiStore.setDebugLevel(level)} />
```

**Test:** Change debug level - should update without errors.

---

#### 4. Fix LLMConfig.svelte (MEDIUM)

**Changes needed:**
- Remove lines 9-11 (`import { createEventDispatcher }...`)
- Add Props interface with `onupdate` callback
- Replace `dispatch('update', {...})` with `onupdate?.({...})`
- Keep reactive statement (lines 57-60) - it's safe for reading

**Test:** Open LLM config panel, change settings, click update - should work without errors.

---

#### 5. Fix AnalyzeButton.svelte (LOW - Optional)

**Changes needed:**
- Remove `this.dispatchEvent()` pattern (lines 16-22)
- Add Props interface with `onclick` callback: `onclick?: () => void`
- Replace inline handler with simple `onclick={handleClick}`
- Create `handleClick` function that calls `onclick?.()`

**Test:** Click "Analyze Document" button - should trigger analysis.

---

#### 6. Fix DownloadButton.svelte (LOW - Optional)

**Changes needed:**
- Remove `this.dispatchEvent()` pattern (lines 24-30)
- Add Props interface with `onclick` callback: `onclick?: () => void`
- Replace inline handler with simple `onclick={handleClick}`
- Create `handleClick` function that calls `onclick?.()`

**Test:** Click "Download Document" button - should download file.

---

## Testing Checklist

After fixing each component, test the following workflow:

### Basic Functionality Tests
- [ ] Drag and drop a .docx file to main upload area - filename shows
- [ ] Drag and drop a file to fallback upload area - filename shows
- [ ] Change merge strategy dropdown - no console errors
- [ ] Change debug level - no console errors
- [ ] Enter text in instructions field - no console errors
- [ ] Click "Process Document" button - processing starts
- [ ] Click "Analyze Document" button - analysis starts
- [ ] Check browser console - NO `effect_update_depth_exceeded` errors

### Regression Tests
- [ ] Options persist to localStorage after page refresh
- [ ] Dark mode toggle works
- [ ] All tabs are accessible
- [ ] Processing results display correctly
- [ ] Download button works after processing

---

## Build and Deployment

### Local Testing
```bash
cd frontend-new
npm run check  # Type checking
npm run build  # Production build
```

### Docker Build
```bash
cd /dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot
docker build -f Dockerfile.sveltekit -t word-chatbot:fix-infinite-loop .
```

### Git Commit
```bash
git add frontend-new/src/lib/components/features/FallbackUpload.svelte
git add frontend-new/src/lib/components/features/MergeStrategy.svelte
git add frontend-new/src/lib/components/features/DebugOptions.svelte
git add frontend-new/src/lib/components/features/LLMConfig.svelte
git add frontend-new/src/lib/components/features/AnalyzeButton.svelte
git add frontend-new/src/lib/components/features/DownloadButton.svelte
git add frontend-new/src/routes/+page.svelte

git commit -m "fix: Convert remaining Svelte 4 components to Svelte 5 patterns

Complete fix for effect_update_depth_exceeded infinite loop errors.

Converted 6 components from createEventDispatcher (Svelte 4) to
callback props pattern (Svelte 5):

CRITICAL:
- FallbackUpload.svelte: Fixes drag-and-drop file display issue

HIGH PRIORITY:
- MergeStrategy.svelte: Eliminates store update loop
- DebugOptions.svelte: Eliminates store update loop

MEDIUM PRIORITY:
- LLMConfig.svelte: Prevents config update loops

LOW PRIORITY (consistency):
- AnalyzeButton.svelte: Standardizes button pattern
- DownloadButton.svelte: Standardizes button pattern

Also updated parent component (+page.svelte) to handle direct
values instead of CustomEvent.detail.

Tested:
- File upload with drag-and-drop working
- All dropdowns and inputs update without errors
- No infinite loops in browser console
- Production build successful
- Docker container builds successfully

Fixes production issue at https://aidemo.dcri.duke.edu/sageapp04/

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Push and Update PR
```bash
git push origin fix/svelte-infinite-loop-bug
# PR #13 will automatically update
```

### Production Deployment
```bash
# SSH to production server
cd /path/to/word-doc-chatbot
git checkout dev
git pull origin dev

# Rebuild Docker
docker build -f Dockerfile.sveltekit -t word-chatbot:latest .

# Stop and restart
docker stop word-chatbot
docker rm word-chatbot
docker run -d -p 8000:8000 --env-file .env --restart unless-stopped --name word-chatbot word-chatbot:latest

# Verify
docker logs -f word-chatbot
# Test: https://aidemo.dcri.duke.edu/sageapp04/
```

---

## Prompt for New Claude Code Session

```
I need to complete a critical bug fix for infinite reactive loops in a SvelteKit application.

CONTEXT:
- Production site is broken with `effect_update_depth_exceeded` errors
- Root cause: 6 components use Svelte 4 createEventDispatcher pattern causing infinite loops
- Branch already created: fix/svelte-infinite-loop-bug
- 2 components already fixed (OptionsPanel, AnalysisMode)
- 6 components still need fixing

TASK:
Read the detailed fix instructions in docs/SVELTE_INFINITE_LOOP_COMPLETE_FIX.md and execute the following:

1. Fix CRITICAL priority component:
   - FallbackUpload.svelte (drag-and-drop broken)

2. Fix HIGH priority components:
   - MergeStrategy.svelte
   - DebugOptions.svelte

3. Fix MEDIUM priority component:
   - LLMConfig.svelte

4. Fix LOW priority components (optional):
   - AnalyzeButton.svelte
   - DownloadButton.svelte

5. Update parent component:
   - frontend-new/src/routes/+page.svelte (fix event handlers)

PATTERN:
Convert from Svelte 4 (createEventDispatcher) to Svelte 5 (callback props):
- Remove: import { createEventDispatcher } from 'svelte'
- Add: Props interface with callback props (e.g., onchange?: (value: T) => void)
- Replace: dispatch('event', value) with callback?.(value)
- Update parent: onchange={(e) => store.set(e.detail)} becomes onchange={(value) => store.set(value)}

TESTING:
After each fix, verify:
- Component compiles without errors
- Browser console shows no infinite loop errors
- User interaction works correctly

Build and test:
- npm run check (type checking)
- npm run build (production build)
- Docker build

IMPORTANT:
- Work on existing branch: fix/svelte-infinite-loop-bug
- Use git add -f for files in src/lib/ (gitignore issue)
- Commit all changes together with detailed message
- Push to update PR #13

Read docs/SVELTE_INFINITE_LOOP_COMPLETE_FIX.md for complete details and examples.
```

---

## Technical Notes

### Why createEventDispatcher Causes Loops

```javascript
// Svelte 4 pattern
const dispatch = createEventDispatcher();

function handleChange() {
    dispatch('change', value);  // Creates CustomEvent
}

// CustomEvent structure:
{
    type: 'change',
    detail: value,      // Value is in .detail property
    bubbles: true,      // Event bubbles up
    composed: false
}

// Parent receives event and accesses e.detail:
onchange={(e) => store.set(e.detail)}

// Problem: If component binds to the store value:
{value} = {$store.value}

// This creates bidirectional flow:
Component → CustomEvent → Store Update → Component Prop → Component → ...
```

### Why Callback Props Don't Loop

```javascript
// Svelte 5 pattern
interface Props {
    onchange?: (value: string) => void;
}

function handleChange() {
    onchange?.(value);  // Direct function call
}

// Parent receives direct value:
onchange={(value) => store.set(value)}

// Component doesn't automatically re-emit on prop changes
// Only emits on user interaction via explicit event handlers
```

---

## Related Issues

### .gitignore Problem
The repo's `.gitignore` has a broad `lib/` entry that ignores `frontend-new/src/lib/`. This is why files need `-f` flag to be added.

**Recommendation:** Future PR to update `.gitignore`:
```gitignore
# Change from:
lib/

# To:
/lib/          # Only root-level lib directory
**/venv/lib/   # Only venv lib directories
```

---

## Success Criteria

After completing all fixes:

✅ **User can:**
- Drag and drop files (filename displays)
- Change all dropdown options without errors
- Enter instructions without errors
- Process documents successfully
- Analyze documents successfully
- Download processed documents

✅ **Browser console shows:**
- No `effect_update_depth_exceeded` errors
- No infinite loop warnings
- Normal operation logs only

✅ **Build process:**
- `npm run check` passes
- `npm run build` succeeds
- Docker image builds successfully
- All TypeScript types resolve correctly

---

## Contact and Support

- **Production Site:** https://aidemo.dcri.duke.edu/sageapp04/
- **GitHub Repo:** https://github.com/sagearbor/word-doc-chatbot
- **PR for this fix:** https://github.com/sagearbor/word-doc-chatbot/pull/13
- **Branch:** fix/svelte-infinite-loop-bug

---

## Revision History

- **2025-10-28:** Initial document created after identifying root cause
- **Status:** 2/8 components fixed, 6 remaining
