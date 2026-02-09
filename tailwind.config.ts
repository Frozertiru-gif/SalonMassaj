import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        blush: {
          50: "#fff7fb",
          100: "#fdeaf3",
          200: "#f9d4e5",
          300: "#f3b3cf",
          400: "#e889b4",
          500: "#d86a9d",
          600: "#c05284",
          700: "#9f3c69",
          800: "#7e3154",
          900: "#5f2640"
        },
        ink: {
          900: "#2a1f24",
          700: "#44323a"
        }
      },
      boxShadow: {
        soft: "0 20px 60px -40px rgba(90, 40, 60, 0.5)",
        card: "0 18px 40px -24px rgba(60, 30, 50, 0.35)"
      },
      borderRadius: {
        xl: "1.25rem",
        "2xl": "1.6rem",
        "3xl": "2rem"
      }
    }
  },
  plugins: []
};

export default config;
