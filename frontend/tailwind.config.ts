import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        earnings: "#1e293b",
        dividend: "#64748b",
        split: "#cbd5e1",
        ipo: "#94a3b8",
        beat: "#22c55e",
        miss: "#ef4444",
      },
    },
  },
  plugins: [],
};

export default config;
