import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

const typeCheckedConfigs = tseslint.configs.recommendedTypeChecked.map((config) => ({
  ...config,
  files: ["**/*.{ts,tsx}"],
}));

export default tseslint.config(
  {
    ignores: [".next/**", "node_modules/**"],
  },
  eslint.configs.recommended,
  ...typeCheckedConfigs,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
);
