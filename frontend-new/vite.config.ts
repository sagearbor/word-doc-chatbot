import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		port: 5173,
		proxy: {
			'/process-document': 'http://localhost:8000',
			'/analyze-document': 'http://localhost:8000',
			'/process-document-with-fallback': 'http://localhost:8000',
			'/analyze-fallback-requirements': 'http://localhost:8000',
			'/analyze-merge': 'http://localhost:8000',
			'/process-legal-document': 'http://localhost:8000',
			'/llm-config': 'http://localhost:8000',
			'/download': 'http://localhost:8000'
		}
	}
});
