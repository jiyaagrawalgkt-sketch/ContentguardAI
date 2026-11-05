import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        midnight: {
          950: "#060911",
          900: "#0B0F19",
          850: "#0E1422",
          800: "#131C2E",
          700: "#1E293B",
          600: "#334155",
        },
        lavender: {
          50: "#FAF9FF",
          100: "#F4F1FD",
          200: "#E9E3FA",
          300: "#D8CCF6",
          400: "#BBA5EE",
        },
        brand: {
          50: "#EEF2FF",
          100: "#E0E7FF",
          200: "#C7D2FE",
          300: "#A5B4FC",
          400: "#818CF8",
          500: "#6366F1",
          600: "#4F46E5",
          700: "#4338CA",
          800: "#3730A3",
          900: "#312E81",
        },
        compliance: {
          pass: "#10B981",
          warning: "#F59E0B",
          danger: "#EF4444",
          info: "#3B82F6",
        }
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        subtle: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)",
        card: "0 4px 20px -2px rgba(11, 15, 25, 0.05), 0 2px 6px -2px rgba(11, 15, 25, 0.02)",
        elevated: "0 10px 30px -4px rgba(11, 15, 25, 0.08), 0 4px 10px -3px rgba(11, 15, 25, 0.03)",
        glow: "0 0 25px -5px rgba(99, 102, 241, 0.25)",
      },
      borderRadius: {
        'xl': '0.875rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      }
    },
  },
  plugins: [],
};

export default config;
