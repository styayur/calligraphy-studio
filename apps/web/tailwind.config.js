/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#25342b',
        paper: '#ffffff',
        cinnabar: '#456b52',
        bamboo: '#53655a',
      },
      fontFamily: {
        display: ['STKaiti', 'KaiTi', 'Noto Serif SC', 'serif'],
        sans: ['Inter', 'Segoe UI', 'Microsoft YaHei', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
