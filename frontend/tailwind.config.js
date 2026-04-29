/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        panel: "#f8fafc",
        line: "#d6dde7",
        hydro: "#148f77",
        wind: "#3867d6",
        nuclear: "#8b5cf6",
        alert: "#c2410c"
      }
    }
  },
  plugins: []
};

