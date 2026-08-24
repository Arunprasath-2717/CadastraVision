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
          bg: '#EAF8FB',
          surface: '#F7FCFE',
          'surface-soft': '#EEF9FB',
          lavender: '#E9F6FB',
          border: '#C9E5EE',
          'border-soft': '#D8EDF5',
          text: '#0D2E46',
          muted: '#4F7285',
          subtle: '#6F8DA0',
          periwinkle: '#8ECDE6',
          action: '#266580',
          'action-hover': '#023859',
          accent: '#54ACBF',
          mint: '#A7EBF2',
          'mint-text': '#0B5463',
          amber: '#F6D7A6',
          'amber-text': '#7E560B',
          rose: '#E9BAC8',
          'rose-text': '#8A3348',
          coral: '#F0B7AE',
          'coral-text': '#9C3333',
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
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Cinzel', 'Inter', 'sans-serif']
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
