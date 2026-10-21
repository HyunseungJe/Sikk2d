import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import prettier from 'eslint-config-prettier';

export default tseslint.config(
  {
    ignores: [
      '**/dist/**',
      '**/node_modules/**',
      '.venv/**',
      'test-results/**',
      'playwright-report/**',
    ],
  },
  { files: ['**/*.js'], ...js.configs.recommended },
  {
    files: ['app/**/*.ts', 'app/**/*.tsx', 'playwright.config.ts'],
    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommendedTypeChecked,
    ],
    languageOptions: {
      parserOptions: {
        project: './app/tsconfig.json',
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  prettier,
);
