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
          "accent-ink": "var(--mh-accent-ink)",
          "accent-surface": "var(--mh-accent-surface)",
          cream: "var(--mh-cream)",
          "cream-deep": "var(--mh-cream-deep)",
          "cream-ink": "var(--mh-cream-ink)",
          ai: "var(--mh-ai)",
          "ai-border": "var(--mh-ai-border)",
          "ai-surface": "var(--mh-ai-surface)",
          "ai-ink": "var(--mh-ai-ink)",
          success: "var(--mh-success)",
          "success-surface": "var(--mh-success-surface)",
          warning: "var(--mh-warning)",
          "warning-surface": "var(--mh-warning-surface)",
          danger: "var(--mh-danger)",
          "danger-surface": "var(--mh-danger-surface)",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      fontSize: {
        display: ["40px", { lineHeight: "48px", fontWeight: "600" }],
        h1: ["var(--mh-size-h1)", { lineHeight: "1.25", fontWeight: "600" }],
        h2: ["24px", { lineHeight: "32px", fontWeight: "600" }],
        h3: ["20px", { lineHeight: "28px", fontWeight: "600" }],
        body: ["var(--mh-size-body)", { lineHeight: "1.6" }],
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
