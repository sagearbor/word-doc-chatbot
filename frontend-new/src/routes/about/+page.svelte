<script lang="ts">
	/**
	 * About Page
	 * Explains the document processing workflow with visual data flow diagram
	 */

	import { onMount } from 'svelte';
	import { ArrowLeft, CheckCircle, FileText, Upload, Cog, Download } from 'lucide-svelte';
	import Card from '$lib/components/shared/Card.svelte';
	import Navbar from '$lib/components/core/Navbar.svelte';
	import { base } from '$app/paths';

	let diagramSvg = $state('');
	let diagramError = $state('');
	let isLoading = $state(true);

	const mermaidCode = `
graph TB
    Start([User Uploads<br/>DOCX File]) --> Upload[FileUpload<br/>Component]
    Upload --> Validate{File<br/>Validation}
    Validate -->|Invalid| Error[Show Error<br/>Toast]
    Validate -->|Valid| Instructions[User Provides<br/>Instructions]

    Instructions --> CheckFallback{Fallback<br/>Mode?}

    CheckFallback -->|No Fallback| DirectLLM[Process<br/>with LLM]
    CheckFallback -->|Fallback Document| FallbackChoice{Fallback<br/>Type?}

    FallbackChoice -->|Has Tracked Changes| ExtractChanges[Extract<br/>TrackedChange<br/>Objects]
    FallbackChoice -->|Requirements Text| ExtractReqs[Extract<br/>Requirements]

    ExtractChanges --> ApplyDirect[Apply Changes<br/>Directly to<br/>Main Doc]
    ExtractReqs --> MergeInstructions[Merge with<br/>User Instructions]
    MergeInstructions --> DirectLLM

    DirectLLM --> LLMHandler[LLM Handler<br/>with Provider]
    LLMHandler --> GenerateEdits[Generate<br/>Structured<br/>JSON Edits]
    GenerateEdits --> WordProcessor[Word Processor<br/>XML Manipulation]

    ApplyDirect --> WordProcessor

    WordProcessor --> BuildTextMap[Build Visible<br/>Text Map]
    BuildTextMap --> ApplyTracked[Apply Tracked<br/>Changes to XML]
    ApplyTracked --> SaveDoc[Save Modified<br/>DOCX]

    SaveDoc --> Return[Return to<br/>Frontend]
    Return --> Results[Display Results<br/>& Download]
    Results --> Done([User Downloads<br/>Processed File])

    style Start fill:#e3f2fd
    style Done fill:#c8e6c9
    style Error fill:#ffcdd2
    style DirectLLM fill:#fff9c4
    style ExtractChanges fill:#b3e5fc
    style WordProcessor fill:#ce93d8
    style Results fill:#c8e6c9
`;

	onMount(async () => {
		try {
			console.log('Loading Mermaid...');
			// Dynamically import mermaid (client-side only)
			const mermaid = (await import('mermaid')).default;
			console.log('Mermaid loaded successfully');

			// Initialize Mermaid with configuration
			mermaid.initialize({
				startOnLoad: false,
				theme: 'default',
				securityLevel: 'loose',
				fontFamily: 'Inter, system-ui, sans-serif',
				fontSize: 13,
				flowchart: {
					useMaxWidth: true,
					htmlLabels: true,
					curve: 'basis',
					padding: 15,
					nodeSpacing: 50,
					rankSpacing: 50,
					width: '100%'
				}
			});

			console.log('Rendering Mermaid diagram...');
			// Render the diagram
			const { svg } = await mermaid.render('mermaid-diagram', mermaidCode);
			console.log('Mermaid diagram rendered successfully');

			diagramSvg = svg;
			isLoading = false;
		} catch (error) {
			console.error('Failed to load/render Mermaid:', error);
			diagramError = error instanceof Error ? error.message : 'Unknown error';
			isLoading = false;
		}
	});
</script>

<svelte:head>
	<title>About - Word Document Assistant</title>
</svelte:head>

<!-- Navbar with Dark Mode Toggle -->
<Navbar title="Word Document Assistant" />

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Page Header -->
	<div class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<h1 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-50 mb-2">
				About Word Document Assistant
			</h1>
			<p class="text-lg text-gray-600 dark:text-gray-300">
				AI-powered document editing with tracked changes
			</p>
		</div>
	</div>

	<!-- Main Content -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
		<!-- Overview Section -->
		<Card elevated={false} padding="lg">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-gray-50 mb-4">
				What is This Application?
			</h2>
			<p class="text-gray-700 dark:text-gray-300 text-base leading-relaxed mb-4">
				The Word Document Tracked Changes Assistant is a powerful tool that uses artificial intelligence
				to suggest and apply edits to Microsoft Word documents (.docx files) with tracked changes.
				This preserves the document's edit history and allows reviewers to see exactly what changed and why.
			</p>
			<p class="text-gray-700 dark:text-gray-300 text-base leading-relaxed">
				The system is configured to use a single AI provider (OpenAI, Azure OpenAI, Anthropic, or Google) set by the administrator.
				It offers advanced features like fallback document processing, requirements extraction, and detailed debug logging.
			</p>
		</Card>

		<!-- Features Section -->
		<Card elevated={false} padding="lg">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-gray-50 mb-6">
				Key Features
			</h2>
			<div class="grid md:grid-cols-2 gap-6">
				<div class="flex gap-4">
					<div class="flex-shrink-0">
						<div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
							<FileText class="w-5 h-5 text-blue-600 dark:text-blue-400" />
						</div>
					</div>
					<div>
						<h3 class="font-semibold text-gray-900 dark:text-gray-50 mb-1">
							Tracked Changes
						</h3>
						<p class="text-sm text-gray-600 dark:text-gray-400">
							All edits are applied as Word's native tracked changes with author attribution and timestamps
						</p>
					</div>
				</div>

				<div class="flex gap-4">
					<div class="flex-shrink-0">
						<div class="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
							<Upload class="w-5 h-5 text-green-600 dark:text-green-400" />
						</div>
					</div>
					<div>
						<h3 class="font-semibold text-gray-900 dark:text-gray-50 mb-1">
							Fallback Processing
						</h3>
						<p class="text-sm text-gray-600 dark:text-gray-400">
							Upload a fallback document with tracked changes or requirements to guide the AI
						</p>
					</div>
				</div>

				<div class="flex gap-4">
					<div class="flex-shrink-0">
						<div class="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
							<Cog class="w-5 h-5 text-purple-600 dark:text-purple-400" />
						</div>
					</div>
					<div>
						<h3 class="font-semibold text-gray-900 dark:text-gray-50 mb-1">
							AI Provider Support
						</h3>
						<p class="text-sm text-gray-600 dark:text-gray-400">
							Supports OpenAI, Azure OpenAI, Anthropic Claude, or Google Gemini (one provider configured by admin)
						</p>
					</div>
				</div>

				<div class="flex gap-4">
					<div class="flex-shrink-0">
						<div class="w-10 h-10 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
							<CheckCircle class="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
						</div>
					</div>
					<div>
						<h3 class="font-semibold text-gray-900 dark:text-gray-50 mb-1">
							Debug & Analysis
						</h3>
						<p class="text-sm text-gray-600 dark:text-gray-400">
							Detailed processing logs, edit summaries, and document analysis capabilities
						</p>
					</div>
				</div>
			</div>
		</Card>

		<!-- Data Flow Diagram -->
		<Card elevated={false} padding="lg">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-gray-50 mb-4">
				How It Works - Data Flow
			</h2>
			<p class="text-gray-700 dark:text-gray-300 text-base leading-relaxed mb-6">
				The diagram below shows the complete data flow from document upload to final download.
				The system intelligently handles different processing modes based on your input.
			</p>

			<div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 overflow-x-auto">
				{#if isLoading}
					<div class="flex items-center justify-center py-12">
						<div class="text-center">
							<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
							<p class="text-gray-600 dark:text-gray-400">Loading diagram...</p>
						</div>
					</div>
				{:else if diagramError}
					<div class="text-center py-8">
						<p class="text-red-600 dark:text-red-400 font-semibold mb-2">Failed to render diagram</p>
						<p class="text-sm text-gray-500 dark:text-gray-400">{diagramError}</p>
						<p class="text-xs text-gray-400 dark:text-gray-500 mt-2">Check browser console for details</p>
					</div>
				{:else if diagramSvg}
					<div class="flex justify-center">
						{@html diagramSvg}
					</div>
				{/if}
			</div>
		</Card>

		<!-- Processing Modes Section -->
		<Card elevated={false} padding="lg">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-gray-50 mb-6">
				Processing Modes
			</h2>
			<div class="space-y-6">
				<div>
					<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-50 mb-2">
						Standard Processing
					</h3>
					<p class="text-gray-700 dark:text-gray-300 text-base leading-relaxed">
						Upload a document and provide editing instructions. The AI analyzes the content and generates
						structured edits that are applied as tracked changes to your document.
					</p>
				</div>

				<div>
					<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-50 mb-2">
						Fallback Mode (Tracked Changes)
					</h3>
					<p class="text-gray-700 dark:text-gray-300 text-base leading-relaxed">
						Upload a main document and a fallback document that already contains tracked changes. The system
						extracts the changes from the fallback and applies them directly to the main document—bypassing
						the LLM for faster, more accurate processing.
					</p>
				</div>

				<div>
					<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-50 mb-2">
						Fallback Mode (Requirements)
					</h3>
					<p class="text-gray-700 dark:text-gray-300 text-base leading-relaxed">
						Upload a main document and a fallback document containing requirements or guidelines. The system
						extracts these requirements, merges them with your instructions, and uses the combined input to
						guide the AI's editing process.
					</p>
				</div>

				<div>
					<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-50 mb-2">
						Document Analysis
					</h3>
					<p class="text-gray-700 dark:text-gray-300 text-base leading-relaxed">
						Analyze existing tracked changes in a document without making new edits. Choose between a summary
						view or raw XML inspection for detailed technical analysis.
					</p>
				</div>
			</div>
		</Card>

		<!-- Technical Details -->
		<Card elevated={false} padding="lg">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-gray-50 mb-4">
				Technical Architecture
			</h2>
			<div class="prose dark:prose-invert max-w-none">
				<ul class="space-y-2 text-gray-700 dark:text-gray-300">
					<li><strong>Frontend:</strong> SvelteKit with TypeScript, TailwindCSS, and Skeleton UI</li>
					<li><strong>Backend:</strong> FastAPI (Python) with async request handling</li>
					<li><strong>Document Processing:</strong> python-docx with direct XML manipulation for tracked changes</li>
					<li><strong>AI Integration:</strong> LiteLLM with configurable provider (single provider per deployment)</li>
					<li><strong>Deployment:</strong> Single Docker container with SvelteKit adapter-static</li>
				</ul>
			</div>
		</Card>

		<!-- Getting Started -->
		<Card elevated={false} padding="lg">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-gray-50 mb-4">
				Getting Started
			</h2>
			<ol class="list-decimal list-inside space-y-3 text-gray-700 dark:text-gray-300 text-base">
				<li>Upload your Word document (.docx format)</li>
				<li>Optionally enable fallback mode and upload a fallback document</li>
				<li>Provide clear editing instructions describing what changes you want</li>
				<li>Configure processing options (author name, case sensitivity, comments)</li>
				<li>Set debug level if you want detailed processing logs</li>
				<li>Click "Process Document" to apply AI-suggested edits</li>
				<li>Review the results and download your processed document</li>
			</ol>

			<div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
				<p class="text-sm text-blue-900 dark:text-blue-200">
					<strong>Tip:</strong> Use keyboard shortcut <kbd class="px-2 py-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-xs font-mono">Ctrl+Enter</kbd>
					to quickly process your document!
				</p>
			</div>
		</Card>
	</div>
</div>

<style>
	kbd {
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	:global(.mermaid) {
		display: flex;
		justify-content: center;
	}

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
