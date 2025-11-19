import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),

  {
    files: ['**/*.{js,jsx}'],

    // Plugins must be objects in Flat Config
    plugins: {
      'react-hooks': reactHooks,
    },

    // Base ESLint rules (equivalent to eslint:recommended)
    rules: {
      ...js.configs.recommended.rules,

      // React Hooks recommended rules
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
    },

    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'module',
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
      },
    },
  },
])