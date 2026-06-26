/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Claude.ai-identical colour tokens
        bg: {
          base:    "#1a1a1a",  // Main background (dark)
          sidebar: "#171717",  // Sidebar background
          input:   "#2f2f2f",  // Input area
          hover:   "#2a2a2a",  // Hover state
          artifact:"#1e1e1e",  // Artifact panel
          message: "#262626",  // AI message bubble
        },
        text: {
          primary:   "#ececec",
          secondary: "#8e8ea0",
          muted:     "#565869",
          link:      "#7c7cff",
        },
        border: {
          DEFAULT: "#383838",
          subtle:  "#2a2a2a",
        },
        accent: {
          primary:  "#cc785c",  // Claude brand orange
          hover:    "#b8684d",
          muted:    "#cc785c33",
        },
        chip: {
          bg:       "#2f2f2f",
          selected: "#cc785c22",
          border:   "#383838",
          selected_border: "#cc785c",
        }
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      fontSize: {
        xs:   ["11px", "16px"],
        sm:   ["13px", "20px"],
        base: ["14px", "22px"],
        lg:   ["16px", "24px"],
        xl:   ["18px", "28px"],
      },
      borderRadius: {
        DEFAULT: "8px",
        lg:      "12px",
        xl:      "16px",
        "2xl":   "20px",
        full:    "9999px",
      },
      width: {
        sidebar:  "260px",
        artifact: "420px",
      },
    },
  },
  plugins: [],
}
