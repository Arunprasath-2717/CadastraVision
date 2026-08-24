/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        pastel: {
          bg: '#F6F7FB',             // Soft gray-blue background
          surface: '#FFFFFF',        // Primary white surface
          'surface-soft': '#FAFAFD', // Secondary surface
          lavender: '#F1EFFA',       // Accent background surface
          border: '#DDE2EC',         // Soft border line
          'border-soft': '#E8E5F0',    // Muted border
          text: '#273044',           // Primary dark text (WCAG AA compliant)
          muted: '#657086',          // Secondary text
          subtle: '#8A93A5',         // Muted text
          periwinkle: '#8FA7E8',     // Brand primary pastel
          action: '#5876C9',         // Accessible deep action blue
          'action-hover': '#4361B3',  // Hover action blue
          accent: '#B6A7D9',         // Soft lavender accent
          
          // Semantic GIS Pastel Colors (WCAG AA Dual Encoding)
          mint: '#A9D8C8',           // High confidence pastel mint
          'mint-text': '#24614E',      // High confidence text/icon
          amber: '#F1D98B',          // Medium confidence pastel amber
          'amber-text': '#85610D',     // Medium confidence text/icon
          rose: '#E7B5C5',           // Low confidence pastel rose
          'rose-text': '#96364C',      // Low confidence text/icon
          coral: '#F0B7AE',          // Validation error soft coral
          'coral-text': '#9C3333',     // Validation error text/icon
        },
        gov: {
          bg: '#0B1220',
          surface: '#111827',
          card: '#1E293B',
          border: '#334155',
          primary: '#1D4ED8',
          text: '#F8FAFC',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Cinzel', 'Inter', 'sans-serif']
      },
      boxShadow: {
        'pastel-sm': '0 2px 8px rgba(39, 48, 68, 0.04)',
        'pastel-md': '0 4px 16px rgba(39, 48, 68, 0.08)',
        'pastel-lg': '0 12px 32px rgba(39, 48, 68, 0.12)',
        'pastel-glow': '0 0 20px rgba(143, 167, 232, 0.3)',
      }
    },
  },
  plugins: [],
}
