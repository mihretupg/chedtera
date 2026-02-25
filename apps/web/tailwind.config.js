/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f4f8f8',
          100: '#dcebeb',
          500: '#0f6b6b',
          700: '#0a4e4e',
        },
      },
    },
  },
  plugins: [],
}
