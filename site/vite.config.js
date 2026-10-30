import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base matches the GitHub Pages path: /<repo>/
export default defineConfig({ plugins: [react()], base: '/Real-time-Visual-Identification-System/' })
