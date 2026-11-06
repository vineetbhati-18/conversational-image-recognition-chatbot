/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bel: {
          navy: '#0F1E36',
          blue: '#1A365D',
          accent: '#2B6CB0',
          light: '#EBF8FF',
          gold: '#D69E2E',
          card: '#152544',
          border: '#2D3748',
        },
      },
    },
  },
  plugins: [],
}
