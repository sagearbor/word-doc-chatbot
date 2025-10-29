<script lang="ts">
	import { Info } from 'lucide-svelte';
	import type { MergeStrategy } from '$lib/stores/ui';

	interface Props {
		value: MergeStrategy;
		onchange?: (value: MergeStrategy) => void;
	}

	let { value = $bindable('append'), onchange }: Props = $props();

	const strategies: Array<{ value: MergeStrategy; label: string; description: string }> = [
		{
			value: 'append',
			label: 'Append',
			description: 'Add fallback instructions after your custom instructions'
		},
		{
			value: 'prepend',
			label: 'Prepend',
			description: 'Add fallback instructions before your custom instructions'
		},
		{
			value: 'priority',
			label: 'Priority',
			description: 'Fallback instructions take precedence over custom instructions'
		}
	];

	function handleChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		value = target.value as MergeStrategy;
		onchange?.(value);
	}

	const selectedStrategy = $derived(strategies.find(s => s.value === value));
</script>

<div class="space-y-2">
	<label for="merge-strategy" class="block text-sm font-medium text-surface-900-50">
		Merge Strategy
	</label>

	<!-- Dropdown selector -->
	<select
		id="merge-strategy"
		class="w-full px-3 py-2 bg-surface-100-900 border border-surface-300-700 rounded-lg text-surface-900-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
		bind:value
		on:change={handleChange}
	>
		{#each strategies as strategy}
			<option value={strategy.value}>
				{strategy.label}
			</option>
		{/each}
	</select>

	<!-- Helper text for selected strategy -->
	{#if selectedStrategy}
		<div class="flex items-start gap-2 p-3 bg-surface-50-950 rounded-lg border border-surface-200-800">
			<Info class="h-4 w-4 text-primary-500 mt-0.5 flex-shrink-0" aria-hidden="true" />
			<p class="text-xs text-surface-700 dark:text-surface-300">
				{selectedStrategy.description}
			</p>
		</div>
	{/if}

	<!-- Radio group alternative (commented out, can be used instead of dropdown) -->
	<!-- <div class="space-y-3">
		{#each strategies as strategy}
			<label class="flex items-start gap-3 p-3 border border-surface-200-800 rounded-lg cursor-pointer hover:bg-surface-50-950 transition-colors {value === strategy.value ? 'bg-primary-50 dark:bg-primary-900/10 border-primary-500' : ''}">
				<input
					type="radio"
					name="merge-strategy"
					value={strategy.value}
					bind:group={value}
					on:change={handleChange}
					class="mt-0.5 h-4 w-4 text-primary-600 focus:ring-primary-500"
				/>
				<div class="flex-1">
					<div class="text-sm font-medium text-surface-900-50">
						{strategy.label}
					</div>
					<div class="text-xs text-surface-600 dark:text-surface-400 mt-1">
						{strategy.description}
					</div>
				</div>
			</label>
		{/each}
	</div> -->
</div>
