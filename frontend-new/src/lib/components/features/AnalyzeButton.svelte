<script lang="ts">
	import { FileSearch, Loader2 } from 'lucide-svelte';

	interface Props {
		loading?: boolean;
		disabled?: boolean;
		onclick?: () => void;
	}

	let { loading = false, disabled = false, onclick }: Props = $props();

	function handleClick() {
		if (!disabled && !loading) {
			onclick?.();
		}
	}
</script>

<button
	type="button"
	class="btn variant-filled-secondary w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed bg-blue-600 text-white hover:bg-blue-700 disabled:hover:bg-blue-600"
	disabled={disabled || loading}
	onclick={handleClick}
>
	{#if loading}
		<Loader2 class="w-5 h-5 animate-spin" />
		<span>Analyzing...</span>
	{:else}
		<FileSearch class="w-5 h-5" />
		<span>Analyze Document</span>
	{/if}
</button>

<style>
	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	.animate-spin {
		animation: spin 1s linear infinite;
	}
</style>
