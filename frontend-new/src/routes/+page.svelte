<script lang="ts">
	import { onMount } from 'svelte';
	import Header from '$lib/components/core/Header.svelte';
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

	// File upload handlers
	function handleFileSelected(event: CustomEvent<File>) {
		const file = event.detail;
		appStore.setFile(file);
		validationStore.validateFile(file);
		toastStore.showToast(`File selected: ${file.name}`, 'info');
	}

	function handleFileRemoved() {
		appStore.setFile(null);
		validationStore.clearFileError();
		toastStore.showToast('File removed', 'info');
	}

	function handleFileError(event: CustomEvent<string>) {
		const error = event.detail;
		toastStore.showToast(error, 'error');
	}

	function handleFallbackFileSelected(event: CustomEvent<File>) {
		const file = event.detail;
		appStore.setFallbackFile(file);
		toastStore.showToast(`Fallback file selected: ${file.name}`, 'info');
	}

	// Instructions handler
	function handleInstructionsChange(event: Event) {
		const target = event.target as HTMLTextAreaElement;
		const value = target.value;
		appStore.setInstructions(value);
		validationStore.validateInstructions(value);
	}

	// Options handler
	function handleOptionsChange(event: CustomEvent<ProcessingOptions>) {
		const options = event.detail;
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
	async function handleLLMConfigUpdate(event: CustomEvent<{ extractionMethod: string; instructionMethod: string }>) {
		const { extractionMethod, instructionMethod } = event.detail;
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
	<Header title="Word Document Tracked Changes Assistant" onMenuToggle={toggleSidebar} />

	<div class="flex flex-1 overflow-hidden">
		<Sidebar {isMobile} isOpen={isMobile ? sidebarOpen : true} onClose={closeSidebar}>
			<div class="space-y-6">
				<!-- File Upload Section -->
				<section>
					<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider mb-3">
						Main Document
					</h3>
					<FileUpload
						label="Upload Document"
						accept=".docx"
						required={true}
						onfileselected={handleFileSelected}
						onfileremoved={handleFileRemoved}
						onfileerror={handleFileError}
					/>
				</section>

				<Divider />

				<!-- Fallback Mode Section -->
				<section>
					<div class="flex items-center justify-between mb-3">
						<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider">
							Advanced Options
						</h3>
						<label class="flex items-center gap-2 cursor-pointer">
							<input
								type="checkbox"
								checked={$uiStore.useFallbackMode}
								onchange={() => uiStore.toggleFallbackMode()}
								class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
							/>
							<span class="text-sm">Use Fallback Document</span>
						</label>
					</div>

					{#if $uiStore.useFallbackMode}
						<div class="space-y-4">
							<FallbackUpload enabled={true} onfileselected={handleFallbackFileSelected} />
							<MergeStrategy value={$uiStore.mergeStrategy} onchange={(e) => uiStore.setMergeStrategy(e.detail)} />
							{#if $appStore.fallbackFile}
								<button
									type="button"
									onclick={handleAnalyzeFallback}
									class="w-full px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-300 rounded-lg hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
								>
									Analyze Fallback
								</button>
							{/if}
						</div>
					{/if}
				</section>

				<Divider />

				<!-- Instructions Section -->
				<section>
					<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider mb-3">
						Instructions
					</h3>
					<InstructionsInput
						value={$appStore.instructions}
						placeholder="Enter your editing instructions here..."
						rows={6}
						oninput={handleInstructionsChange}
					/>
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
						Debug Mode
					</h3>
					<DebugOptions debugLevel={$uiStore.debugLevel} onchange={(e) => uiStore.setDebugLevel(e.detail)} />
				</section>

				<Divider />

				<!-- Analysis Mode -->
				<section>
					<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider mb-3">
						Analysis Mode
					</h3>
					<AnalysisMode value={$uiStore.analysisMode} onchange={(e) => uiStore.setAnalysisMode(e.detail)} />
				</section>

				<Divider />

				<!-- Action Buttons -->
				<section class="space-y-3">
					<ProcessButton loading={$appStore.isProcessing} disabled={!$isValid || $appStore.isProcessing} onclick={handleProcess} />
					<AnalyzeButton loading={$appStore.isAnalyzing} disabled={!$appStore.uploadedFile || $appStore.isAnalyzing} onclick={handleAnalyze} />
				</section>

				<!-- LLM Config (Advanced) -->
				{#if $resultsStore.llmConfig}
					<details class="mt-6">
						<summary class="text-sm font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider cursor-pointer">
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
		<main class="flex-1 overflow-y-auto bg-gray-100 dark:bg-gray-800 p-4 sm:p-6 lg:p-8">
			<div class="max-w-7xl mx-auto space-y-6">
				<!-- Welcome / Status -->
				{#if !$resultsStore.processedResult && !$resultsStore.analysisResult && !$appStore.isProcessing && !$appStore.isAnalyzing}
					<Card elevated={false} padding="lg">
						<h2 class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-50 mb-4">
							Welcome to Word Document Assistant
						</h2>
						<p class="text-gray-600 dark:text-gray-300 text-lg mb-4">
							Upload a Word document (.docx) and provide instructions to apply AI-suggested edits with tracked changes.
						</p>
						<ul class="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
							<li>Upload your main Word document</li>
							<li>Optionally use a fallback document with requirements or tracked changes</li>
							<li>Provide clear editing instructions</li>
							<li>Configure processing options and debug level</li>
							<li>Click "Process Document" or "Analyze Document"</li>
						</ul>
					</Card>
				{/if}

				<!-- Processing Indicator -->
				{#if $appStore.isProcessing}
					<Card elevated={true} padding="lg">
						<div class="flex flex-col items-center justify-center py-8">
							<LoadingSpinner size="lg" message="Processing document..." />
						</div>
					</Card>
				{/if}

				<!-- Analysis Indicator -->
				{#if $appStore.isAnalyzing}
					<Card elevated={true} padding="lg">
						<div class="flex flex-col items-center justify-center py-8">
							<LoadingSpinner size="lg" message="Analyzing document..." />
						</div>
					</Card>
				{/if}

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
							class="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-transparent border border-gray-300 rounded-lg hover:bg-gray-50 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700"
						>
							Show Processing Log
						</button>
					{/if}

					{#if $resultsStore.processedResult.debug_info && ($uiStore.debugLevel === 'standard' || $uiStore.debugLevel === 'extended')}
						<DebugInfo debugInfo={$resultsStore.processedResult.debug_info} />
					{/if}
				{/if}

				<!-- Analysis Results -->
				{#if $resultsStore.analysisResult && !$appStore.isAnalyzing}
					<Card elevated={false} padding="lg">
						<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-50 mb-4">Analysis Results</h3>
						<AnalysisResults analysisContent={$resultsStore.analysisResult.analysis} />
					</Card>
				{/if}

				<!-- Fallback Analysis Results -->
				{#if $resultsStore.fallbackAnalysis}
					<FallbackAnalysis analysisData={$resultsStore.fallbackAnalysis} />
				{/if}
			</div>
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
</style>
