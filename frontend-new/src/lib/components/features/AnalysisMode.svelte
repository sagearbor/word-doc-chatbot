<script lang="ts">
	import { FileSearch, Code } from 'lucide-svelte';

	interface Props {
		value: 'summary' | 'raw_xml';
		onchange?: (value: 'summary' | 'raw_xml') => void;
	}

	let { value = $bindable('summary'), onchange }: Props = $props();

	// Handle change from user interaction
	function handleChange() {
		onchange?.(value);
	}

	const options = [
		{
			value: 'summary',
			label: 'Summarize Extracted Changes',
			description: 'Extract tracked changes and generate a summary',
			icon: FileSearch
		},
		{
			value: 'raw_xml',
			label: 'Summarize from Raw XML',
			description: 'Analyze document XML structure directly',
			icon: Code
		}
	] as const;
</script>

<div class="space-y-3">
	<label class="block text-sm font-semibold text-gray-900 dark:text-white">
		Analysis Mode
	</label>

	<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
		{#each options as option}
			<label
				class="relative flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all duration-200
					{value === option.value
						? 'border-blue-600 bg-blue-50 dark:bg-blue-950 dark:border-blue-500'
						: 'border-gray-300 bg-white dark:bg-gray-800 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'}"
			>
				<input
					type="radio"
					name="analysis-mode"
					bind:group={value}
					value={option.value}
					onchange={handleChange}
					class="sr-only"
				/>

				<div class="flex items-start gap-3 w-full">
					<svelte:component
						this={option.icon}
						class="w-5 h-5 flex-shrink-0 mt-0.5 {value === option.value
							? 'text-blue-600 dark:text-blue-400'
							: 'text-gray-500 dark:text-gray-400'}"
					/>

					<div class="flex-1 min-w-0">
						<div
							class="text-sm font-medium {value === option.value
								? 'text-blue-900 dark:text-blue-100'
								: 'text-gray-900 dark:text-white'}"
						>
							{option.label}
						</div>
						<div
							class="mt-1 text-xs {value === option.value
								? 'text-blue-700 dark:text-blue-300'
								: 'text-gray-600 dark:text-gray-400'}"
						>
							{option.description}
						</div>
					</div>

					{#if value === option.value}
						<div class="flex-shrink-0">
							<div class="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center">
								<svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 12 12">
									<path d="M3.707 5.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414-1.414L5 6.586 3.707 5.293z"/>
								</svg>
							</div>
						</div>
					{/if}
				</div>
			</label>
		{/each}
	</div>

	<div class="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
		<strong>Note:</strong> The "Summarize Extracted Changes" mode is recommended for documents with tracked changes.
		Use "Summarize from Raw XML" if you need to analyze the raw document structure.
	</div>
</div>
