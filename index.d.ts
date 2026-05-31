import type { UserConfig } from 'vite-plus'
import type { OxlintConfig } from 'vite-plus/lint'

// Shared vite-plus config consumed by janosh's Svelte/Vite projects.
// - `fmt`/`build` are typed as the canonical UserConfig members so that spreading the
//   whole object (`defineConfig({ ...config, ... })`) compares as identity against
//   UserConfig instead of blowing TS's instantiation depth.
// - `lint` is OxlintConfig (not the inferred 143-key literal) with non-optional
//   ignorePatterns/rules so projects can spread + extend them
//   (`{ ...config.lint, ignorePatterns: [...config.lint.ignorePatterns, `static/**`] }`).
export declare const config: {
    lint: OxlintConfig & {
        ignorePatterns: string[]
        rules: NonNullable<OxlintConfig['rules']>
    }
    fmt: NonNullable<UserConfig['fmt']>
    build: NonNullable<UserConfig['build']>
    staged: NonNullable<UserConfig['staged']>
}
