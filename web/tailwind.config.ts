import type { Config } from "tailwindcss";

/**
 * Tokens mapeados 1:1 desde `design/stitch/tokens.css` (sección "Mapeo a Tailwind").
 * El proyecto es dark-only: no se generan variantes light.
 */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        mh: {
          canvas: "var(--mh-canvas)",
          surface: "var(--mh-surface)",
          raised: "var(--mh-surface-raised)",
          sunken: "var(--mh-surface-sunken)",
          chrome: "var(--mh-chrome)",
          border: "var(--mh-border)",
          "border-strong": "var(--mh-border-strong)",
          "border-control": "var(--mh-border-control)",
          text: "var(--mh-text)",
          secondary: "var(--mh-text-secondary)",
          muted: "var(--mh-text-muted)",
          "on-accent": "var(--mh-text-on-accent)",
          accent: "var(--mh-accent)",
          "accent-deep": "var(--mh-accent-deep)",
          "accent-surface": "var(--mh-accent-surface)",
          ai: "var(--mh-ai)",
          success: "var(--mh-success)",
          warning: "var(--mh-warning)",
          danger: "var(--mh-danger)",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      fontSize: {
        display: ["40px", { lineHeight: "48px", fontWeight: "600" }],
        h1: ["32px", { lineHeight: "40px", fontWeight: "600" }],
        h2: ["24px", { lineHeight: "32px", fontWeight: "600" }],
        h3: ["20px", { lineHeight: "28px", fontWeight: "600" }],
        body: ["17px", { lineHeight: "27px" }],
        "body-sm": ["15px", { lineHeight: "24px" }],
        label: ["16px", { lineHeight: "24px", fontWeight: "500" }],
        "label-xs": ["14px", { lineHeight: "20px", fontWeight: "600" }],
      },
      borderRadius: {
        cell: "8px",
        sm: "10px",
        md: "14px",
        lg: "20px",
      },
      boxShadow: {
        card: "0 16px 40px rgba(0, 0, 0, 0.5)",
      },
    },
  },
  plugins: [],
} satisfies Config;
