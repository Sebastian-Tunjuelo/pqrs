import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          900: "#1e3a5f"
        },
        primary: {
          DEFAULT: "#00693E",
          foreground: "#FFFFFF",
          muted: "#0d4d32"
        },
        accent: { DEFAULT: "#F5A800", foreground: "#1A1A1A" },
        danger: { DEFAULT: "#D32F2F", soft: "#FFEBEE" },
        warning: { DEFAULT: "#F57C00", soft: "#FFF3E0" },
        success: { DEFAULT: "#388E3C", soft: "#E8F5E9" },
        neutral: {
          50: "#F4F4F4",
          100: "#E8E8E8",
          900: "#1A1A1A"
        }
      },
      boxShadow: {
        card: "0 4px 24px rgba(0, 0, 0, 0.06)"
      },
      borderRadius: {
        card: "10px"
      }
    }
  },
  plugins: []
};

export default config;
