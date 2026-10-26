/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          50: '#FDFCF7',
          100: '#F8F6EF',
          200: '#F0EDE2',
        },
        forest: {
          50: '#EAF1E5',
          100: '#C8D9BF',
          200: '#A9BEA3',
          300: '#7FA88A',
          400: '#4E8B64',
          500: '#245B43',
          600: '#1C4A35',
          700: '#153826',
          800: '#0E2619',
          900: '#07140C',
        },
        charcoal: {
          100: '#788078',
          500: '#3D4A3E',
          900: '#26332B',
        },
        gold: {
          100: '#FFF3CD',
          300: '#F5C842',
          500: '#D4A017',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Manrope', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 4px 0 rgba(36,91,67,0.08), 0 1px 2px 0 rgba(0,0,0,0.04)',
        'card-hover': '0 4px 16px 0 rgba(36,91,67,0.12), 0 2px 4px 0 rgba(0,0,0,0.06)',
        modal: '0 20px 60px 0 rgba(36,91,67,0.15)',
      },
      borderRadius: {
        xl: '12px',
        '2xl': '16px',
        '3xl': '24px',
      },
    },
  },
  plugins: [],
}
