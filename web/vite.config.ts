import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxy: Record<string, unknown> = {};

  if (env.VITE_SEARCH_PROXY_TARGET) {
    proxy['/api/search'] = {
      target: env.VITE_SEARCH_PROXY_TARGET,
      changeOrigin: true,
      rewrite: (path: string) => path.replace(/^\/api\/search/, ''),
    };
  }

  if (env.VITE_REVIEW_PROXY_TARGET) {
    proxy['/api/reviews'] = {
      target: env.VITE_REVIEW_PROXY_TARGET,
      changeOrigin: true,
      rewrite: (path: string) => path.replace(/^\/api\/reviews/, ''),
    };
  }

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy,
    },
    preview: {
      port: 4173,
    },
  };
});
