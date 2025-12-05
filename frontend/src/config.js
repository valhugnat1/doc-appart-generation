// =============================================================================
// Environment Configuration
// =============================================================================
// Centralized config with validation and type safety
// Usage: import { config } from '@/config'
// =============================================================================

function getEnv(key, defaultValue = '') {
  const value = import.meta.env[`VITE_${key}`]
  return value !== undefined ? value : defaultValue
}

function getEnvBool(key, defaultValue = false) {
  const value = import.meta.env[`VITE_${key}`]
  if (value === undefined) return defaultValue
  return value === 'true' || value === '1'
}

export const config = {
  // API Configuration
  api: {
    baseUrl: getEnv('API_BASE_URL', 'http://localhost:8000'),
  },

  // App metadata
  app: {
    title: getEnv('APP_TITLE', 'Outil Immo'),
    version: import.meta.env.VITE_APP_VERSION || '1.0.0',
  },

  // Feature flags
  features: {
    debug: getEnvBool('ENABLE_DEBUG', false),
  },

  // Environment info
  env: {
    mode: import.meta.env.MODE, // 'development', 'staging', 'production'
    isDev: import.meta.env.DEV,
    isProd: import.meta.env.PROD,
    isStaging: import.meta.env.MODE === 'staging',
  },
}

export const API_BASE_URL = config.api.baseUrl

if (config.env.isDev || config.features.debug) {
  console.log('🔧 App Config:', {
    mode: config.env.mode,
    apiBaseUrl: config.api.baseUrl,
    debug: config.features.debug,
  })
}

if (config.env.isProd) {
  const requiredVars = ['API_BASE_URL']
  const missing = requiredVars.filter(
    (key) => !import.meta.env[`VITE_${key}`]
  )
  if (missing.length > 0) {
    console.warn(
      `⚠️ Missing environment variables: ${missing.map((k) => `VITE_${k}`).join(', ')}`
    )
  }
}

export default config