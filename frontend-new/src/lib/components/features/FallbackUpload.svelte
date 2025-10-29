<script lang="ts">
	import { Upload, Info } from 'lucide-svelte';

	interface Props {
		enabled: boolean;
		file?: File | null;
		onfileselected?: (file: File | null) => void;
	}

	let { enabled = false, file = $bindable(null), onfileselected }: Props = $props();

	let fileInput = $state<HTMLInputElement>();
	let isDragging = $state(false);

	function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		const selectedFile = target.files?.[0] || null;

		if (selectedFile && selectedFile.name.endsWith('.docx')) {
			file = selectedFile;
			onfileselected?.(file);
		} else if (selectedFile) {
			alert('Please select a .docx file');
			target.value = '';
		}
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		isDragging = false;

		const droppedFile = event.dataTransfer?.files[0];
		if (droppedFile && droppedFile.name.endsWith('.docx')) {
			file = droppedFile;
			onfileselected?.(file);
		} else if (droppedFile) {
			alert('Please select a .docx file');
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		isDragging = true;
	}

	function handleDragLeave() {
		isDragging = false;
	}

	function clearFile() {
		file = null;
		if (fileInput) {
			fileInput.value = '';
		}
		onfileselected?.(null);
	}
</script>

{#if enabled}
	<div class="space-y-2">
		<div class="flex items-center gap-2">
			<label for="fallback-upload" class="block text-sm font-medium text-surface-900-50">
				Fallback Document (Optional)
			</label>
			<div class="group relative">
				<Info class="h-4 w-4 text-surface-500 cursor-help" />
				<div class="invisible group-hover:visible absolute left-0 top-6 z-10 w-64 p-2 bg-surface-900 text-white text-xs rounded shadow-lg">
					Upload a fallback document containing tracked changes or requirements text. The system will extract these and apply them to your main document.
				</div>
			</div>
		</div>

		<!-- File upload area -->
		<div
			class="relative border-2 border-dashed rounded-lg p-6 transition-colors {isDragging
				? 'border-warning-500 bg-warning-50 dark:bg-warning-900/10'
				: file
					? 'border-success-500 bg-success-50 dark:bg-success-900/10'
					: 'border-warning-300 dark:border-warning-700 bg-surface-100-900 hover:border-warning-400 dark:hover:border-warning-600'}"
			ondrop={handleDrop}
			ondragover={handleDragOver}
			ondragleave={handleDragLeave}
			role="button"
			tabindex="0"
			aria-label="Fallback document upload area"
		>
			<input
				bind:this={fileInput}
				id="fallback-upload"
				type="file"
				accept=".docx"
				class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
				onchange={handleFileSelect}
				aria-label="Choose fallback document file"
			/>

			<div class="flex flex-col items-center justify-center text-center pointer-events-none">
				<Upload class="h-10 w-10 mb-3 text-warning-500" aria-hidden="true" />

				{#if file}
					<p class="text-sm font-medium text-success-700 dark:text-success-400 mb-1">
						{file.name}
					</p>
					<p class="text-xs text-surface-500">
						{(file.size / 1024).toFixed(2)} KB
					</p>
					<button
						type="button"
						class="mt-3 text-xs text-error-600 hover:text-error-700 underline pointer-events-auto"
						onclick={(e) => { e.stopPropagation(); clearFile(); }}
					>
						Remove file
					</button>
				{:else}
					<p class="text-sm text-surface-700 dark:text-surface-300 mb-1">
						Drop fallback document here or click to browse
					</p>
					<p class="text-xs text-surface-500">
						.docx files only
					</p>
				{/if}
			</div>
		</div>

		<p class="text-xs text-surface-600 dark:text-surface-400 flex items-start gap-1">
			<Info class="h-3 w-3 mt-0.5 flex-shrink-0" />
			<span>
				Fallback documents can contain tracked changes (preferred) or requirements text that will be merged with your instructions.
			</span>
		</p>
	</div>
{/if}
