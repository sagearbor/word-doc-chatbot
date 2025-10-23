# Component Usage Guide

This guide shows how to use the newly created feature components for the Word Document Chatbot.

## Components Created

### 1. FileUpload.svelte
File upload component with drag-and-drop support and validation.

### 2. InstructionsInput.svelte
Textarea component for entering processing instructions with auto-resize.

### 3. ProcessButton.svelte
Primary action button with loading state and keyboard shortcut support.

### 4. OptionsPanel.svelte
Form panel for configuring processing options.

### 5. fileValidation.ts
Utility functions for validating DOCX files.

## Usage Example

```svelte
<script lang="ts">
	import { FileUpload, InstructionsInput, ProcessButton, OptionsPanel } from '$lib/components/features';
	import type { ProcessingOptions } from '$lib/types/api';

	let mainFile: File | null = null;
	let instructions: string = '';
	let processing: boolean = false;
	let options: ProcessingOptions = {
		authorName: 'Claude',
		caseSensitive: false,
		addComments: true,
		debugMode: false,
		extendedDebugMode: false
	};

	function handleFileSelected(event: CustomEvent<File>) {
		mainFile = event.detail;
		console.log('File selected:', mainFile.name);
	}

	function handleFileRemoved() {
		mainFile = null;
		console.log('File removed');
	}

	function handleFileError(event: CustomEvent<string>) {
		console.error('File error:', event.detail);
		alert(event.detail);
	}

	function handleInstructionsInput(event: CustomEvent<string>) {
		instructions = event.detail;
	}

	function handleOptionsChange(event: CustomEvent<ProcessingOptions>) {
		options = event.detail;
	}

	async function handleProcess() {
		if (!mainFile) {
			alert('Please select a file first');
			return;
		}

		if (!instructions.trim()) {
			alert('Please provide instructions');
			return;
		}

		processing = true;

		try {
			// Create FormData
			const formData = new FormData();
			formData.append('file', mainFile);
			formData.append('instructions', instructions);
			formData.append('author_name', options.authorName);
			formData.append('case_sensitive', String(options.caseSensitive));
			formData.append('add_comments', String(options.addComments));
			formData.append('debug_mode', String(options.debugMode));
			formData.append('extended_debug_mode', String(options.extendedDebugMode));

			// Send request to backend
			const response = await fetch('/api/process-document', {
				method: 'POST',
				body: formData
			});

			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			// Handle response
			const blob = await response.blob();
			const downloadUrl = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = downloadUrl;
			a.download = `processed_${mainFile.name}`;
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(downloadUrl);
			document.body.removeChild(a);

			console.log('Processing complete!');
		} catch (error) {
			console.error('Processing failed:', error);
			alert(`Processing failed: ${error}`);
		} finally {
			processing = false;
		}
	}
</script>

<div class="container max-w-4xl mx-auto p-6">
	<h1 class="text-3xl font-bold mb-6">Word Document Chatbot</h1>

	<div class="space-y-6">
		<!-- File Upload -->
		<FileUpload
			label="Upload Word Document"
			accept=".docx"
			required={true}
			on:file:selected={handleFileSelected}
			on:file:removed={handleFileRemoved}
			on:file:error={handleFileError}
		/>

		<!-- Instructions -->
		<InstructionsInput
			bind:value={instructions}
			placeholder="Enter instructions for how to modify the document..."
			rows={6}
			on:input={handleInstructionsInput}
		/>

		<!-- Options -->
		<OptionsPanel
			bind:options
			on:change={handleOptionsChange}
		/>

		<!-- Process Button -->
		<ProcessButton
			loading={processing}
			disabled={!mainFile || !instructions.trim()}
			on:click={handleProcess}
		/>
	</div>
</div>
```

## Component Props and Events

### FileUpload

**Props:**
- `label: string` - Label text for the file input
- `accept: string = '.docx'` - Accepted file types
- `required: boolean = false` - Whether the field is required

**Events:**
- `file:selected` - Emitted when a valid file is selected (payload: File)
- `file:removed` - Emitted when file is removed (no payload)
- `file:error` - Emitted when validation fails (payload: string error message)

### InstructionsInput

**Props:**
- `value: string` - Current textarea value (bindable)
- `placeholder: string` - Placeholder text
- `rows: number = 4` - Initial number of rows

**Events:**
- `input` - Emitted on text input (payload: string current value)

### ProcessButton

**Props:**
- `loading: boolean = false` - Whether the button is in loading state
- `disabled: boolean = false` - Whether the button is disabled

**Events:**
- `click` - Emitted when button is clicked (no payload)

**Keyboard Shortcut:**
- `Ctrl+Enter` (or `Cmd+Enter` on Mac) - Triggers click event

### OptionsPanel

**Props:**
- `options: ProcessingOptions` - Current options object (bindable)

**Events:**
- `change` - Emitted when any option changes (payload: ProcessingOptions object)

## File Validation Utilities

### validateDocxFile(file: File)

Validates a DOCX file for type and size constraints.

```typescript
import { validateDocxFile } from '$lib/utils/fileValidation';

const file = event.target.files[0];
const result = validateDocxFile(file);

if (!result.valid) {
	console.error(result.error);
} else if (result.warning) {
	console.warn(result.warning);
}
```

**Returns:**
```typescript
interface ValidationResult {
	valid: boolean;
	error?: string;    // Set when validation fails (> 100MB or wrong type)
	warning?: string;  // Set when file is large but valid (> 10MB)
}
```

### formatFileSize(bytes: number)

Formats file size in human-readable format.

```typescript
import { formatFileSize } from '$lib/utils/fileValidation';

console.log(formatFileSize(1536)); // "1.5 KB"
console.log(formatFileSize(1048576)); // "1 MB"
```

## Accessibility Features

All components include:
- Proper ARIA labels and roles
- Keyboard navigation support
- Focus management
- Screen reader compatibility
- Color contrast compliance

## Mobile-Friendly Design

- Touch-friendly targets (minimum 44x44px)
- Responsive layouts
- Drag-and-drop works on mobile with appropriate fallbacks
- Auto-resize textarea for better mobile experience

## Styling

Components use Tailwind CSS with PostCSS. Customization can be done by:

1. Modifying Tailwind classes in component `<style>` blocks
2. Using CSS custom properties
3. Overriding styles via parent component classes

## Integration Notes

These components are designed to work with:
- SvelteKit routing and state management
- The backend API endpoints defined in `backend/main.py`
- TypeScript types from `src/lib/types/api.ts`
- Tailwind CSS utility classes
- lucide-svelte icon library
