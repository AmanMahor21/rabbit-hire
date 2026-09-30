import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// https://vite.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      // Use path.resolve to create an absolute path
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [react(), tailwindcss()],
  base: "/",
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
      },
    },
  },
});
