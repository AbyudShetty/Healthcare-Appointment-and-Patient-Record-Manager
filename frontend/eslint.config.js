import globals from 'globals'
import { defineConfig, globalIgnores } from 'eslint/config'
import { FlatCompat } from '@eslint/eslintrc'

// Create compat wrapper
const compat = new FlatCompat({/* optional: baseDirectory: __dirname */})

export default defineConfig([
  globalIgnores(['dist']),

  // Convert legacy/shareable configs by *name* (strings) — safe and simple
  ...compat.extends(
    'eslint:recommended',
    'plugin:react-hooks/recommended'
  ),

  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
      // keep other rules here
    },
  },
])