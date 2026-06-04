import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist', 'coverage', 'htmlcov', '*.config.*.timestamp-*'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      // eslint-plugin-react-hooks v7 introduced new React-Compiler-aligned rules
      // (set-state-in-effect, purity, immutability). They flag legitimate refactor
      // candidates but would block this dep bump on ~17 pre-existing call sites.
      // Downgraded to 'warn' so the upgrade lands now; cleanup tracked separately.
      // Classic rules-of-hooks / exhaustive-deps stay at recommended levels.
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/purity': 'warn',
      'react-hooks/immutability': 'warn',
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      // LEGO-friendly rules - balanced for productivity
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_' },
      ],
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-empty-object-type': 'off', // Allow empty interfaces
      'react-refresh/only-export-components': 'off', // Allow utility exports
      'prefer-const': 'error',
      'no-var': 'error',
    },
  }
)
