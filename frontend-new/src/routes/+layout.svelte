<script lang="ts">
	/**
	 * Root Layout Component
	 * Provides global layout structure
	 * Initializes theme and global styles
	 */

	import '../app.pcss';
	import { onMount } from 'svelte';
	import { theme } from '$lib/stores/theme';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();

	// Initialize theme on mount
	onMount(() => {
		theme.init();
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<meta name="theme-color" content="#ffffff" />
</svelte:head>

<!-- Main content slot -->
{@render children?.()}

<style>
	/**
	 * Global styles are imported from app.pcss
	 * Component-specific styles are defined in individual components
	 */

	/* Ensure full height layout */
	:global(html, body) {
		height: 100%;
		overflow: hidden;
	}

	/* Smooth transitions for theme changes */
	:global(*) {
		transition-property: color, background-color, border-color;
		transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
		transition-duration: 150ms;
	}

	/* Disable transitions on page load to prevent flash */
	:global(.preload *) {
		transition: none !important;
	}
</style>
