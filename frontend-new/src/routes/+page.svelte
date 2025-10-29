<script lang="ts">
	import { onMount } from 'svelte';
	import Navbar from '$lib/components/core/Navbar.svelte';
	import Sidebar from '$lib/components/core/Sidebar.svelte';
	import { ToastContainer } from '$lib/components/shared';
	import {
		FileUpload,
		InstructionsInput,
		ProcessButton,
		OptionsPanel,
		ResultsDisplay,
		DownloadButton,
		ProcessingLog,
		AnalysisResults,
		AnalysisMode,
		AnalyzeButton,
		FallbackUpload,
		MergeStrategy,
		DebugOptions,
		DebugInfo,
		LLMConfig,
		FallbackAnalysis
	} from '$lib/components/features';
	import { LoadingSpinner, Card, Divider } from '$lib/components/shared';
	import { appStore, resultsStore, uiStore, validationStore, isValid } from '$lib/stores';
	import { toastStore } from '$lib/stores/toast';
	import {
		processDocument,
		analyzeDocument,
		processWithFallback,
		analyzeFallbackRequirements,
		getLLMConfig,
		setLLMConfig,
		downloadFile,
		triggerDownload
	} from '$lib/api';
	import type { ProcessingOptions } from '$lib/types/api';
	import { ArrowRight, Sparkles, Settings } from 'lucide-svelte';

	// Reactive store access - use $storeName syntax directly in templates
	// No $derived needed - Svelte 5 auto-tracks store subscriptions

	// Local state
	let isMobile = $state(false);
	let sidebarOpen = $state(false);

	// Handle window resize
	function handleResize() {
		isMobile = window.innerWidth < 768;
		if (!isMobile) sidebarOpen = false;
	}

	// Sidebar handlers
	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}

	function closeSidebar() {
		sidebarOpen = false;
	}

	// File upload handlers - these are direct function calls, not CustomEvents
	function handleFileSelected(file: File) {
		appStore.setFile(file);
		validationStore.validateFile(file);
		toastStore.showToast(`File selected: ${file.name}`, 'info');
	}

	function handleFileRemoved() {
		appStore.setFile(null);
		validationStore.clearFileError();
		toastStore.showToast('File removed', 'info');
	}

	function handleFileError(error: string) {
		toastStore.showToast(error, 'error');
	}

	function handleFallbackFileSelected(file: File | null) {
		if (file) {
			appStore.setFallbackFile(file);
			toastStore.showToast(`Fallback file selected: ${file.name}`, 'info');
		} else {
			appStore.setFallbackFile(null);
		}
	}

	// Instructions handler
	function handleInstructionsChange(event: Event) {
		const target = event.target as HTMLTextAreaElement;
		const value = target.value;
		appStore.setInstructions(value);
		validationStore.validateInstructions(value);
	}

	// Options handler
	function handleOptionsChange(options: ProcessingOptions) {
		appStore.updateOptions(options);
	}

	// Process document
	async function handleProcess() {
		const uploadedFile = $appStore.uploadedFile;
		if (!uploadedFile) {
			toastStore.showToast('Please upload a document first', 'error');
			return;
		}

		if (!$isValid) {
			toastStore.showToast('Please fix validation errors', 'error');
			return;
		}

		try {
			appStore.setProcessing(true);
			resultsStore.clearProcessedResult();

			// Map debug level to boolean flags
			const debugLevel = $uiStore.debugLevel;
			const debugMode = debugLevel !== 'off';
			const extendedDebugMode = debugLevel === 'extended';

			const options = {
				...$appStore.processingOptions,
				debugMode,
				extendedDebugMode
			};

			let result;
			const fallbackFile = $appStore.fallbackFile;
			if ($uiStore.useFallbackMode && fallbackFile) {
				result = await processWithFallback(
					uploadedFile,
					fallbackFile,
					$appStore.instructions,
					$uiStore.mergeStrategy,
					options
				);
			} else {
				result = await processDocument(uploadedFile, $appStore.instructions, options);
			}

			resultsStore.setProcessedResult(result);
			toastStore.showToast('Document processed successfully!', 'success');
		} catch (error: any) {
			toastStore.showToast(`Processing failed: ${error.message}`, 'error');
			console.error('Processing error:', error);
		} finally {
			appStore.setProcessing(false);
		}
	}

	// Analyze document
	async function handleAnalyze() {
		const uploadedFile = $appStore.uploadedFile;
		if (!uploadedFile) {
			toastStore.showToast('Please upload a document first', 'error');
			return;
		}

		try {
			appStore.setAnalyzing(true);
			resultsStore.clearAnalysisResult();

			const result = await analyzeDocument(uploadedFile, $uiStore.analysisMode);
			resultsStore.setAnalysisResult(result);
			toastStore.showToast('Analysis completed!', 'success');
		} catch (error: any) {
			toastStore.showToast(`Analysis failed: ${error.message}`, 'error');
			console.error('Analysis error:', error);
		} finally {
			appStore.setAnalyzing(false);
		}
	}

	// Analyze fallback
	async function handleAnalyzeFallback() {
		const fallbackFile = $appStore.fallbackFile;
		if (!fallbackFile) {
			toastStore.showToast('Please upload a fallback document first', 'error');
			return;
		}

		try {
			const context = $appStore.instructions || 'General document processing';
			const result = await analyzeFallbackRequirements(fallbackFile, context);
			resultsStore.setFallbackAnalysis(result);
			toastStore.showToast('Fallback analysis completed!', 'success');
		} catch (error: any) {
			toastStore.showToast(`Fallback analysis failed: ${error.message}`, 'error');
			console.error('Fallback analysis error:', error);
		}
	}

	// Download processed file
	async function handleDownload() {
		const processedResult = $resultsStore.processedResult;
		if (!processedResult?.filename) {
			toastStore.showToast('No processed file available', 'error');
			return;
		}

		try {
			const blob = await downloadFile(processedResult.filename);
			triggerDownload(blob, processedResult.filename);
			toastStore.showToast('Download started!', 'success');
		} catch (error: any) {
			toastStore.showToast(`Download failed: ${error.message}`, 'error');
			console.error('Download error:', error);
		}
	}

	// Load LLM config on mount
	async function loadLLMConfig() {
		try {
			const config = await getLLMConfig();
			resultsStore.setLLMConfig(config);
		} catch (error: any) {
			console.error('Failed to load LLM config:', error);
		}
	}

	// Update LLM config
	async function handleLLMConfigUpdate(config: { extraction_method: string; instruction_method: string }) {
		const { extraction_method: extractionMethod, instruction_method: instructionMethod } = config;
		try {
			const config = await setLLMConfig(extractionMethod, instructionMethod);
			resultsStore.setLLMConfig(config);
			toastStore.showToast('LLM configuration updated!', 'success');
		} catch (error: any) {
			toastStore.showToast(`Failed to update LLM config: ${error.message}`, 'error');
			console.error('LLM config update error:', error);
		}
	}

	// Initialize
	onMount(() => {
		handleResize();
		window.addEventListener('resize', handleResize);
		loadLLMConfig();
		return () => window.removeEventListener('resize', handleResize);
	});
</script>

<ToastContainer />

<div class="flex flex-col h-screen overflow-hidden">
	<Navbar title="Word Document Assistant" onMenuToggle={toggleSidebar} />

	<div class="flex flex-1 overflow-hidden">
		<Sidebar {isMobile} isOpen={isMobile ? sidebarOpen : true} onClose={closeSidebar}>
			<div class="space-y-4">
				<!-- Advanced Options Header -->
				<div class="flex items-center gap-2 text-gray-700 dark:text-gray-300 mb-2">
					<Settings class="w-5 h-5" />
					<h2 class="text-lg font-semibold">Advanced Options</h2>
				</div>

				<Divider />

				<!-- Fallback Mode Section -->
				<section>
					<div class="flex items-center justify-between mb-3">
						<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider">
							Fallback Document
						</h3>
						<label class="flex items-center gap-2 cursor-pointer">
							<input
								type="checkbox"
								checked={$uiStore.useFallbackMode}
								onchange={() => uiStore.toggleFallbackMode()}
								class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
							/>
							<span class="text-sm">Enable</span>
						</label>
					</div>

					{#if $uiStore.useFallbackMode}
						<div class="space-y-4">
							<FallbackUpload enabled={true} onfileselected={handleFallbackFileSelected} />
							<MergeStrategy value={$uiStore.mergeStrategy} onchange={(value) => uiStore.setMergeStrategy(value)} />
							{#if $appStore.fallbackFile}
								<button
									type="button"
									onclick={handleAnalyzeFallback}
									class="w-full px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-300 rounded-lg hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/30 dark:border-blue-700 dark:hover:bg-blue-900/50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
								>
									Analyze Fallback
								</button>
							{/if}
						</div>
					{/if}
				</section>

				<Divider />

				<!-- Processing Options -->
				<section>
					<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider mb-3">
						Processing Options
					</h3>
					<OptionsPanel options={$appStore.processingOptions} onchange={handleOptionsChange} />
				</section>

				<Divider />

				<!-- Debug Options -->
				<section>
					<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider mb-3">
						Debug Level
					</h3>
					<DebugOptions debugLevel={$uiStore.debugLevel} onchange={(level) => uiStore.setDebugLevel(level)} />
				</section>

				<Divider />

				<!-- Analysis Mode -->
				<section>
					<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider mb-3">
						Analysis Options
					</h3>
					<AnalysisMode value={$uiStore.analysisMode} onchange={(mode) => uiStore.setAnalysisMode(mode)} />

					<div class="mt-3">
						<AnalyzeButton loading={$appStore.isAnalyzing} disabled={!$appStore.uploadedFile || $appStore.isAnalyzing} onclick={handleAnalyze} />
					</div>
				</section>

				<!-- LLM Config (Advanced) -->
				{#if $resultsStore.llmConfig}
					<Divider />
					<details class="mt-4">
						<summary class="text-sm font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
							LLM Configuration
						</summary>
						<div class="mt-3">
							<LLMConfig currentConfig={$resultsStore.llmConfig} onupdate={handleLLMConfigUpdate} />
						</div>
					</details>
				{/if}
			</div>
		</Sidebar>

		<!-- Main Content -->
		<main class="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
			<!-- Hero Section (before processing) -->
			{#if !$resultsStore.processedResult && !$resultsStore.analysisResult && !$appStore.isProcessing && !$appStore.isAnalyzing}
				<div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
					<!-- Hero Header -->
					<div class="text-center mb-8 sm:mb-12">
						<div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900/30 mb-4">
							<Sparkles class="w-8 h-8 text-blue-600 dark:text-blue-400" />
						</div>
						<h1 class="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-50 mb-4">
							AI-Powered Document Editing
						</h1>
						<p class="text-lg sm:text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
							Upload your Word document and let AI suggest professional edits with tracked changes
						</p>
					</div>

					<!-- Main Upload Card -->
					<Card elevated={true} padding="xl">
						<div class="space-y-6">
							<!-- Step 1: Upload -->
							<div>
								<div class="flex items-center gap-2 mb-3">
									<div class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white text-sm font-bold">
										1
									</div>
									<h2 class="text-xl font-semibold text-gray-900 dark:text-gray-50">
										Upload Your Document
									</h2>
								</div>
								<FileUpload
									label="Main Document"
									accept=".docx"
									required={true}
									onfileselected={handleFileSelected}
									onfileremoved={handleFileRemoved}
									onfileerror={handleFileError}
								/>
							</div>

							<Divider />

							<!-- Step 2: Instructions -->
							<div>
								<div class="flex items-center gap-2 mb-3">
									<div class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white text-sm font-bold">
										2
									</div>
									<h2 class="text-xl font-semibold text-gray-900 dark:text-gray-50">
										Provide Instructions
									</h2>
								</div>
								<InstructionsInput
									value={$appStore.instructions}
									placeholder="Enter your editing instructions here... (e.g., 'Make the tone more formal', 'Fix grammar and spelling', 'Simplify technical jargon')"
									rows={6}
									oninput={handleInstructionsChange}
								/>
							</div>

							<Divider />

							<!-- Step 3: Process -->
							<div>
								<div class="flex items-center gap-2 mb-4">
									<div class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white text-sm font-bold">
										3
									</div>
									<h2 class="text-xl font-semibold text-gray-900 dark:text-gray-50">
										Process Document
									</h2>
								</div>
								<ProcessButton
									loading={$appStore.isProcessing}
									disabled={!$isValid || $appStore.isProcessing}
									onclick={handleProcess}
								/>

								{#if $appStore.uploadedFile}
									<p class="mt-3 text-sm text-center text-gray-600 dark:text-gray-400">
										Press <kbd class="px-2 py-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-xs font-mono shadow-sm">Ctrl+Enter</kbd>
										to process quickly
									</p>
								{/if}
							</div>
						</div>
					</Card>

					<!-- Quick Tips -->
					<div class="mt-8 grid sm:grid-cols-2 gap-4">
						<div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
							<h3 class="font-semibold text-blue-900 dark:text-blue-200 mb-2">
								Need more control?
							</h3>
							<p class="text-sm text-blue-800 dark:text-blue-300">
								Use the sidebar to configure fallback documents, processing options, and debug settings
							</p>
						</div>
						<div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
							<h3 class="font-semibold text-green-900 dark:text-green-200 mb-2">
								How does it work?
							</h3>
							<p class="text-sm text-green-800 dark:text-green-300">
								Visit the <a href="/about" class="underline hover:text-green-600">About page</a> to see the complete data flow diagram
							</p>
						</div>
					</div>
				</div>
			{/if}

			<!-- Processing Indicator -->
			{#if $appStore.isProcessing}
				<div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
					<Card elevated={true} padding="xl">
						<div class="flex flex-col items-center justify-center py-8">
							<LoadingSpinner size="lg" message="Processing your document with AI..." />
							<p class="mt-4 text-sm text-gray-600 dark:text-gray-400 text-center">
								This may take a minute. We're analyzing the content and generating tracked changes.
							</p>
						</div>
					</Card>
				</div>
			{/if}

			<!-- Analysis Indicator -->
			{#if $appStore.isAnalyzing}
				<div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
					<Card elevated={true} padding="xl">
						<div class="flex flex-col items-center justify-center py-8">
							<LoadingSpinner size="lg" message="Analyzing document..." />
						</div>
					</Card>
				</div>
			{/if}

			<!-- Results Section -->
			{#if $resultsStore.processedResult || $resultsStore.analysisResult || $resultsStore.fallbackAnalysis}
				<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
					<!-- Processing Results -->
					{#if $resultsStore.processedResult && !$appStore.isProcessing}
						<ResultsDisplay result={$resultsStore.processedResult} />

						{#if $resultsStore.processedResult.filename}
							<Card elevated={false} padding="lg">
								<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-50 mb-4">Download Processed Document</h3>
								<DownloadButton filename={$resultsStore.processedResult.filename} disabled={false} onclick={handleDownload} />
							</Card>
						{/if}

						{#if $resultsStore.processedResult.processing_log && $uiStore.showProcessingLog}
							<ProcessingLog logContent={$resultsStore.processedResult.processing_log} expanded={true} />
						{:else if $resultsStore.processedResult.processing_log}
							<button
								type="button"
								onclick={() => uiStore.toggleProcessingLog()}
								class="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-gray-300 transition-colors"
							>
								Show Processing Log
							</button>
						{/if}

						{#if $resultsStore.processedResult.debug_info && ($uiStore.debugLevel === 'standard' || $uiStore.debugLevel === 'extended')}
							<DebugInfo debugInfo={$resultsStore.processedResult.debug_info} />
						{/if}

						<!-- Start New Button -->
						<div class="flex justify-center pt-4">
							<button
								type="button"
								onclick={() => {
									resultsStore.clearProcessedResult();
									resultsStore.clearAnalysisResult();
									appStore.setFile(null);
									appStore.setInstructions('');
								}}
								class="inline-flex items-center gap-2 px-6 py-3 text-base font-semibold text-blue-700 bg-blue-50 border-2 border-blue-300 rounded-lg hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/30 dark:border-blue-700 dark:hover:bg-blue-900/50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
							>
								<ArrowRight class="w-5 h-5" />
								Process Another Document
							</button>
						</div>
					{/if}

					<!-- Analysis Results -->
					{#if $resultsStore.analysisResult && !$appStore.isAnalyzing}
						<Card elevated={false} padding="lg">
							<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-50 mb-4">Analysis Results</h3>
							<AnalysisResults analysisContent={$resultsStore.analysisResult.analysis} />
						</Card>

						<!-- Start New Button -->
						<div class="flex justify-center pt-4">
							<button
								type="button"
								onclick={() => {
									resultsStore.clearAnalysisResult();
									appStore.setFile(null);
								}}
								class="inline-flex items-center gap-2 px-6 py-3 text-base font-semibold text-blue-700 bg-blue-50 border-2 border-blue-300 rounded-lg hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/30 dark:border-blue-700 dark:hover:bg-blue-900/50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
							>
								<ArrowRight class="w-5 h-5" />
								Analyze Another Document
							</button>
						</div>
					{/if}

					<!-- Fallback Analysis Results -->
					{#if $resultsStore.fallbackAnalysis}
						<FallbackAnalysis analysisData={$resultsStore.fallbackAnalysis} />
					{/if}
				</div>
			{/if}
		</main>
	</div>
</div>

<style>
	main {
		scroll-behavior: smooth;
		scrollbar-width: thin;
		scrollbar-color: rgb(148 163 184) transparent;
	}

	main::-webkit-scrollbar {
		width: 8px;
	}

	main::-webkit-scrollbar-track {
		background: transparent;
	}

	main::-webkit-scrollbar-thumb {
		background-color: rgb(148 163 184);
		border-radius: 4px;
	}

	main::-webkit-scrollbar-thumb:hover {
		background-color: rgb(100 116 139);
	}

	kbd {
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
</style>
