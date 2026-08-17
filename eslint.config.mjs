import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

const typeCheckedConfigs = tseslint.configs.recommendedTypeChecked.map((config) => ({
  ...config,
  files: ["**/*.ts"],
}));

export default tseslint.config(
  {
    ignores: ["**/dist/**", "**/node_modules/**", "**/coverage/**"],
  },
  {
    linterOptions: {
      reportUnusedDisableDirectives: "error",
    },
  },
  eslint.configs.recommended,
  ...typeCheckedConfigs,
  {
    files: ["**/*.ts"],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
);
