<script lang="ts">
	import { Loader2, Info, Settings } from 'lucide-svelte';
	import type { LLMConfig } from '$lib/types/api';
	import Button from '$lib/components/shared/Button.svelte';

	interface Props {
		currentConfig: LLMConfig | null;
		onupdate?: (config: { extraction_method: string; instruction_method: string }) => void;
	}

	let { currentConfig = null, onupdate }: Props = $props();

	let extractionMethod = $state(currentConfig?.extraction_method || 'llm');
	let instructionMethod = $state(currentConfig?.instruction_method || 'llm');
	let loading = $state(false);

	const extractionMethods = [
		{
			value: 'llm',
			label: 'LLM Extraction',
			description: 'Use AI to intelligently extract requirements (more accurate, slower)'
		},
		{
			value: 'regex',
			label: 'Regex Extraction',
			description: 'Use pattern matching to extract requirements (faster, less flexible)'
		}
	];

	const instructionMethods = [
		{
			value: 'llm',
			label: 'LLM Instructions',
			description: 'Generate instructions using AI (adaptive, context-aware)'
		},
		{
			value: 'hardcoded',
			label: 'Hardcoded Templates',
			description: 'Use predefined instruction templates (consistent, faster)'
		}
	];

	function handleUpdate() {
		loading = true;
		onupdate?.({
			extraction_method: extractionMethod,
			instruction_method: instructionMethod
		});

		// Simulate loading - parent component should handle actual update
		setTimeout(() => {
			loading = false;
		}, 1000);
	}

	// Update local state when currentConfig changes
	$effect(() => {
		if (currentConfig) {
			extractionMethod = currentConfig.extraction_method;
			instructionMethod = currentConfig.instruction_method;
		}
	});

	const hasChanges = $derived(
		extractionMethod !== currentConfig?.extraction_method ||
		instructionMethod !== currentConfig?.instruction_method
	);
</script>

<div class="space-y-4 border border-surface-300-700 rounded-lg p-4 bg-surface-50-950">
	<div class="flex items-center gap-2">
		<Settings class="h-5 w-5 text-primary-500" aria-hidden="true" />
		<h3 class="text-lg font-semibold text-surface-900-50">LLM Configuration</h3>
	</div>

	{#if currentConfig}
		<!-- Current Configuration Display -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-4 p-3 bg-surface-100-900 rounded-lg">
			<div>
				<div class="text-xs font-medium text-surface-600 dark:text-surface-400 mb-1">
					Extraction Method
				</div>
				<div class="text-sm font-semibold text-surface-900-50">
					{currentConfig.extraction_method.toUpperCase()}
				</div>
			</div>
			<div>
				<div class="text-xs font-medium text-surface-600 dark:text-surface-400 mb-1">
					Instruction Method
				</div>
				<div class="text-sm font-semibold text-surface-900-50">
					{currentConfig.instruction_method.toUpperCase()}
				</div>
			</div>
		</div>
	{/if}

	<!-- Extraction Method Selector -->
	<div class="space-y-2">
		<label for="extraction-method" class="block text-sm font-medium text-surface-900-50">
			Extraction Method
		</label>
		<select
			id="extraction-method"
			bind:value={extractionMethod}
			disabled={loading}
			class="w-full px-3 py-2 bg-surface-100-900 border border-surface-300-700 rounded-lg text-surface-900-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
		>
			{#each extractionMethods as method}
				<option value={method.value}>
					{method.label}
				</option>
			{/each}
		</select>
		{#each extractionMethods as method}
			{#if method.value === extractionMethod}
				<div class="flex items-start gap-2 p-2 bg-primary-50 dark:bg-primary-900/10 rounded-lg">
					<Info class="h-4 w-4 text-primary-500 mt-0.5 flex-shrink-0" aria-hidden="true" />
					<p class="text-xs text-surface-700 dark:text-surface-300">
						{method.description}
					</p>
				</div>
			{/if}
		{/each}
	</div>

	<!-- Instruction Method Selector -->
	<div class="space-y-2">
		<label for="instruction-method" class="block text-sm font-medium text-surface-900-50">
			Instruction Method
		</label>
		<select
			id="instruction-method"
			bind:value={instructionMethod}
			disabled={loading}
			class="w-full px-3 py-2 bg-surface-100-900 border border-surface-300-700 rounded-lg text-surface-900-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
		>
			{#each instructionMethods as method}
				<option value={method.value}>
					{method.label}
				</option>
			{/each}
		</select>
		{#each instructionMethods as method}
			{#if method.value === instructionMethod}
				<div class="flex items-start gap-2 p-2 bg-primary-50 dark:bg-primary-900/10 rounded-lg">
					<Info class="h-4 w-4 text-primary-500 mt-0.5 flex-shrink-0" aria-hidden="true" />
					<p class="text-xs text-surface-700 dark:text-surface-300">
						{method.description}
					</p>
				</div>
			{/if}
		{/each}
	</div>

	<!-- Update Button -->
	<div class="flex justify-end">
		<Button
			variant="primary"
			size="md"
			{loading}
			disabled={!hasChanges || loading}
			on:click={handleUpdate}
		>
			{#if loading}
				Updating...
			{:else}
				Update AI Mode
			{/if}
		</Button>
	</div>

	{#if !hasChanges && currentConfig}
		<p class="text-xs text-surface-500 text-center">
			Configuration is up to date
		</p>
	{/if}
</div>
