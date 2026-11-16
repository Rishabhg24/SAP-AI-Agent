import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import fs from 'node:fs'
import path from 'node:path'

/**
 * Dynamically resolves backend webserver and client port from connections.json.
 * Eliminates hardcoded target URLs and ports.
 */
function getDynamicServerConfig() {
  const baseDir = (import.meta as any).dirname || process.cwd()
  const rootConnections = path.resolve(baseDir, '../connections.json')
  const backendConnections = path.resolve(baseDir, '../backend/connections.json')
  let config: any = null

  for (const p of [rootConnections, backendConnections]) {
    if (fs.existsSync(p)) {
      try {
        config = JSON.parse(fs.readFileSync(p, 'utf-8'))
        break
      } catch {
        // ignore and fallback
      }
    }
  }

  const host = config?.server?.host || '127.0.0.1'
  const port = config?.server?.port || 8000
  const frontendPort = config?.server?.frontend_port || 5173

  return {
    backendUrl: `http://${host}:${port}`,
    frontendPort,
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const dynamicConfig = getDynamicServerConfig()

  const targetBackend =
    env.VITE_BACKEND_URL ||
    env.BACKEND_URL ||
    (env.VITE_API_BASE ? env.VITE_API_BASE.replace(/\/api\/?$/, '') : dynamicConfig.backendUrl)
  const frontendPort = Number(env.PORT || env.VITE_PORT || dynamicConfig.frontendPort)

  return {
    plugins: [react()],
    server: {
      host: true,
      port: frontendPort,
      proxy: {
        '/api': {
          target: targetBackend,
          changeOrigin: true,
        },
      },
    },
  }
})
