/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#181512',
        paper: '#f4efe5',
        cinnabar: '#a23a2b',
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