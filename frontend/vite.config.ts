/// <reference types="@tailwindcss/vite" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  // Adjust this base path to match your GitHub repository name exactly
  base: '/song-guessing-app/', 
});
