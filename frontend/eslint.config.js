import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import { defineConfig, globalIgnores } from 'eslint/config'
import { FlatCompat } from '@eslint/eslintrc'

// Compatibility wrapper for old-style configs
const compat = new FlatCompat()

export default defineConfig([
  globalIgnores(['dist']),

  // Convert legacy configs (`js.configs.recommended`, react-hooks)
  ...compat.extends(
    js.configs.recommended,
    reactHooks.configs.recommended
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
    },
  },
])