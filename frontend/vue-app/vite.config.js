import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
  // 루트(.env)를 그대로 읽도록 envDir을 상위 상위로 지정
  envDir: path.resolve(__dirname, "../.."),
  plugins: [vue()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5174
  }
});
