/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Bảng màu rút từ mockup Figma
        sidebar: '#0d1424',       // navy tối của thanh điều hướng
        'sidebar-muted': '#8a93a6',
        brand: {
          DEFAULT: '#2563eb',     // blue-600, màu primary
          dark: '#1d4ed8',
        },
        canvas: '#f6f7f9',        // nền vùng nội dung
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
