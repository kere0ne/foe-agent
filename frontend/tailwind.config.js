/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: { colors: {
    ink: { 950: '#0b0e14', 900: '#12161f', 800: '#1a2030', 700: '#242c40', 600: '#39435e' },
    accent: { DEFAULT: '#6366f1', bright: '#818cf8' } } } },
  plugins: [],
}
