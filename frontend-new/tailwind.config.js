import forms from '@tailwindcss/forms';
import typography from '@tailwindcss/typography';

export default {
	darkMode: 'class',
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			screens: {
				xs: '475px'
			}
		}
	},
	plugins: [forms, typography]
};
