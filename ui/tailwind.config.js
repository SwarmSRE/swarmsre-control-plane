/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'slate-grey-base': '#0B1120',
        'slate-grey-panel': '#111827',
        'slate-grey-border': '#1E293B',
        'electric-cyan': '#00F0FF',
        'healthy-green': '#10B981',
        'warning-yellow': '#F59E0B',
        'critical-red': '#EF4444',
        'text-primary': '#F8FAFC',
        'text-secondary': '#94A3B8',
      }
    },
  },
  plugins: [],
}
