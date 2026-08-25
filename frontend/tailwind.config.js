/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cv: {
          cyan: '#A7EBF2',
          'cyan-strong': '#54ACBF',
          blue: '#266580',
          'blue-deep': '#023859',
          navy: '#011C40',
        },
        pastel: {
          bg: '#F1EEE7',
          surface: '#FBFAF6',
          'surface-soft': '#EAE7DE',
          lavender: '#E4E8D9',
          border: '#D9D3C7',
          'border-soft': '#E5E0D6',
          text: '#292824',
          muted: '#6F6B5F',
          subtle: '#918B7E',
          periwinkle: '#B9C6A5',
          action: '#266580',
          'action-hover': '#023859',
          accent: '#54ACBF',
          mint: '#A7EBF2',
          'mint-text': '#4D6548',
          amber: '#E8D9B7',
          'amber-text': '#78633A',
          rose: '#E2C2BA',
          'rose-text': '#8A4F4A',
          coral: '#D9A79B',
          'coral-text': '#87453F',
        },
        gov: {
          bg: '#011C40',
          surface: '#023859',
          card: '#0B2D4A',
          border: '#2B6C88',
          primary: '#266580',
          text: '#F2FBFF',
        }
      },
      fontFamily: {
        sans: ['Palatino Linotype', 'Book Antiqua', 'Palatino', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Inter', 'system-ui', 'sans-serif']
      },
      boxShadow: {
        'pastel-sm': '0 8px 20px rgba(1, 28, 64, 0.06)',
        'pastel-md': '0 12px 28px rgba(2, 56, 89, 0.10)',
        'pastel-lg': '0 18px 38px rgba(1, 28, 64, 0.12)',
        'pastel-glow': '0 0 24px rgba(167, 235, 242, 0.35)',
      }
    },
  },
  plugins: [],
}
