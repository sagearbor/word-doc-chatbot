<script lang="ts">
	import type { ProcessingOptions } from '$lib/types/api';

	interface Props {
		options: ProcessingOptions;
		onchange?: (options: ProcessingOptions) => void;
	}

	let { options = $bindable(), onchange }: Props = $props();

	function handleChange() {
		onchange?.(options);
	}

	// Note: No $effect needed - user interactions trigger handleChange via event handlers
	// (oninput/onchange on input elements below)
</script>

<div class="options-panel">
	<div class="space-y-4">
		<!-- Author Name -->
		<div class="form-group">
			<label for="author-name" class="form-label">
				Author Name
			</label>
			<input
				id="author-name"
				type="text"
				bind:value={options.authorName}
				oninput={handleChange}
				class="form-input"
				placeholder="Enter author name"
				aria-label="Author name for tracked changes"
			/>
			<p class="form-help-text">Name displayed in tracked changes</p>
		</div>

		<div class="divider" />

		<!-- Checkboxes Group -->
		<div class="space-y-3">
			<!-- Case-Sensitive Search -->
			<div class="checkbox-group">
				<input
					id="case-sensitive"
					type="checkbox"
					bind:checked={options.caseSensitive}
					onchange={handleChange}
					class="form-checkbox"
					aria-label="Enable case-sensitive text matching"
				/>
				<label for="case-sensitive" class="checkbox-label">
					<span class="font-medium">Case-Sensitive Search</span>
					<span class="text-xs text-gray-500 block">Match text exactly as written</span>
				</label>
			</div>

			<!-- Add Comments -->
			<div class="checkbox-group">
				<input
					id="add-comments"
					type="checkbox"
					bind:checked={options.addComments}
					onchange={handleChange}
					class="form-checkbox"
					aria-label="Add explanatory comments to changes"
				/>
				<label for="add-comments" class="checkbox-label">
					<span class="font-medium">Add Comments to Changes</span>
					<span class="text-xs text-gray-500 block">Include reasons for each edit</span>
				</label>
			</div>
		</div>

	</div>
</div>

<style lang="postcss">
	.options-panel {
		@apply p-4 bg-gray-50 border border-gray-200 rounded-lg;
	}

	.form-group {
		@apply space-y-1;
	}

	.form-label {
		@apply block text-sm font-medium text-gray-700;
	}

	.form-input {
		@apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm;
		@apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500;
		@apply text-sm text-gray-900 placeholder-gray-400;
		@apply transition-colors duration-200;
	}

	.form-input:hover {
		@apply border-gray-400;
	}

	.form-help-text {
		@apply text-xs text-gray-500 mt-1;
	}

	.divider {
		@apply border-t border-gray-300;
	}

	.checkbox-group {
		@apply flex items-start space-x-3;
	}

	.form-checkbox {
		@apply w-4 h-4 mt-0.5 text-blue-600 border-gray-300 rounded;
		@apply focus:ring-2 focus:ring-blue-500 focus:ring-offset-0;
		@apply transition-colors duration-200 cursor-pointer;
	}

	.form-checkbox:disabled {
		@apply cursor-not-allowed opacity-50;
	}

	.checkbox-label {
		@apply flex-1 text-sm text-gray-700 cursor-pointer select-none;
	}
</style>
