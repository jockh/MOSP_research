import { fileURLToPath } from 'node:url';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, fileURLToPath(new URL('.', import.meta.url)), 'MOSP_');
  const proxy = {
    '/api': {
      target: process.env.MOSP_API_PROXY_TARGET || env.MOSP_API_PROXY_TARGET || 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  };
  return {
    plugins: [react()],
    server: { port: 5173, proxy },
    preview: { proxy },
  };
});
