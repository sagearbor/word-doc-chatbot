<script lang="ts">
	import { Download } from 'lucide-svelte';
	import { formatFileSize } from '$lib/utils/formatting';

	interface Props {
		filename: string;
		disabled?: boolean;
		fileSize?: number;
		onclick?: () => void;
	}

	let { filename, disabled = false, fileSize, onclick }: Props = $props();

	// Extract file extension for display
	const fileExtension = $derived(() => {
		const parts = filename.split('.');
		return parts.length > 1 ? `.${parts[parts.length - 1]}` : '';
	});

	function handleClick() {
		if (!disabled) {
			onclick?.();
		}
	}
</script>

<button
	type="button"
	class="btn variant-filled-success w-full sm:w-auto flex items-center justify-center gap-3 px-6 py-3 rounded-lg text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed bg-green-600 hover:bg-green-700 disabled:hover:bg-green-600"
	{disabled}
	onclick={handleClick}
>
	<Download class="w-5 h-5" />
	<div class="flex flex-col items-start">
		<span class="text-sm leading-tight">Download Processed Document</span>
		<span class="text-xs opacity-90 font-normal">
			{filename}
			{#if fileSize}
				<span class="ml-1">({formatFileSize(fileSize)})</span>
			{/if}
		</span>
	</div>
</button>

<style>
	button {
		min-height: 3.5rem;
	}
</style>
