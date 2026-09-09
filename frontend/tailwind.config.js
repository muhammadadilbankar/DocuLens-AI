/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#132620',
        parchment: '#f5f2e9',
        moss: '#245c48',
        lime: '#c9f27f',
      },
      boxShadow: {
        lift: '0 24px 70px -34px rgba(19, 38, 32, 0.35)',
      },
    },
  },
  plugins: [],
}

