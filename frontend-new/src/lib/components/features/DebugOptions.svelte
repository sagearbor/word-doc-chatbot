<script lang="ts">
	import { AlertTriangle, Info } from 'lucide-svelte';

	interface Props {
		debugLevel: 'off' | 'standard' | 'extended';
		onchange?: (level: 'off' | 'standard' | 'extended') => void;
	}

	let { debugLevel = $bindable('off'), onchange }: Props = $props();

	const debugLevels = [
		{
			value: 'off' as const,
			label: 'Off',
			description: 'No debug information will be collected'
		},
		{
			value: 'standard' as const,
			label: 'Standard Debug',
			description: 'Collect basic processing information and edit summaries'
		},
		{
			value: 'extended' as const,
			label: 'Extended Debug',
			description: 'Collect detailed processing logs, edit details, and full LLM responses',
			warning: true
		}
	];

	function handleChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		debugLevel = target.value as 'off' | 'standard' | 'extended';
		onchange?.(debugLevel);
	}

	const selectedLevel = $derived(debugLevels.find(l => l.value === debugLevel));
</script>

<div class="space-y-2">
	<label for="debug-options" class="block text-sm font-medium text-surface-900-50">
		Debug Mode
	</label>

	<!-- Dropdown selector -->
	<select
		id="debug-options"
		class="w-full px-3 py-2 bg-surface-100-900 border border-surface-300-700 rounded-lg text-surface-900-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
		bind:value={debugLevel}
		on:change={handleChange}
	>
		{#each debugLevels as level}
			<option value={level.value}>
				{level.label}
			</option>
		{/each}
	</select>

	<!-- Helper text for selected level -->
	{#if selectedLevel}
		<div class="flex items-start gap-2 p-3 bg-surface-50-950 rounded-lg border border-surface-200-800">
			{#if selectedLevel.warning}
				<AlertTriangle class="h-4 w-4 text-warning-500 mt-0.5 flex-shrink-0" aria-hidden="true" />
			{:else}
				<Info class="h-4 w-4 text-primary-500 mt-0.5 flex-shrink-0" aria-hidden="true" />
			{/if}
			<div class="flex-1">
				<p class="text-xs text-surface-700 dark:text-surface-300">
					{selectedLevel.description}
				</p>
				{#if selectedLevel.warning}
					<p class="text-xs text-warning-700 dark:text-warning-400 mt-1">
						Warning: Extended debug mode generates large log files that may impact performance.
					</p>
				{/if}
			</div>
		</div>
	{/if}
</div>
