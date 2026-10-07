import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  build: { target: ["chrome109", "edge109"], sourcemap: true },
  server: { proxy: { "/api": "http://localhost:8001" } },
});
