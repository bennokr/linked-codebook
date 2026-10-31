// ESLint baseline for TypeScript projects (flat config). Copy to the repo root.
// Tier 1 (new code) uses these limits. Tier 2 (legacy code): raise the numbers to the current worst case
// (complexity 12, max-lines-per-function 60, add max-lines 600), set --max-warnings to today's count and
// lower them over time.
import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['**/generated/', '**/dist/', 'node_modules/'] },
  js.configs.recommended,
  tseslint.configs.strict,
  tseslint.configs.stylistic,
  {
    rules: {
      complexity: ['error', 8],
      'max-depth': ['error', 3],
      'max-lines-per-function': ['error', { max: 30, skipBlankLines: true, skipComments: true }],
      'max-params': ['error', 4],
      'max-statements': ['error', 12],
      'no-nested-ternary': 'error',
      eqeqeq: 'error',
      '@typescript-eslint/consistent-type-imports': 'error',
    },
  },
  { files: ['**/test/**'], rules: { 'max-lines-per-function': 'off', 'max-statements': 'off' } },
);
