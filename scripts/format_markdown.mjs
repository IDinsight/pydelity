#!/usr/bin/env node
// Format every Markdown file git tracks or would track with the pinned Prettier, then,
// where the STANDARDS workflow is installed, run its consistency check. Files listed in
// .prettierignore (CHANGELOG.md, which release-please writes) are skipped.
//
// Project Markdown gets Prettier's output as is. STANDARDS workflow files may only
// change in whitespace, so for those this script applies a guard: it writes Prettier's
// output only when, with all whitespace removed, it equals the file. Otherwise it leaves
// the file byte-identical and prints a warning.
//
// Not every branch has STANDARDS installed. Without it there are no STANDARDS files to
// guard and no check to run, and the script only formats.
//
// Prettier is not imported from node_modules: the hook environment (prek, `language:
// node`) installs it and puts its `prettier` command on PATH, so the package is found
// through that command.
//
// Run it from the repo root through prek: `uv run --locked prek exec prettier-markdown
// -- node scripts/format_markdown.mjs` (the `lint-markdown` just recipe does this).

import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { delimiter, dirname, join } from "node:path";
import { pathToFileURL } from "node:url";

// The STANDARDS consistency check, present only where STANDARDS is installed.
const STANDARDS_CHECK = ".standards/bin/check.mjs";

// Paths owned by the STANDARDS workflow, when it is installed.
const STANDARDS_PATH =
  /^(\.standards\/|\.agents\/|\.claude\/skills\/|AGENTS\.md$|CLAUDE\.md$)/;

/**
 * List the Markdown files git tracks or would track, relative to the repo root.
 *
 * @returns {string[]} Sorted file paths.
 */
function listMarkdownFiles() {
  const output = execFileSync(
    "git",
    ["ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "*.md"],
    { encoding: "utf8" },
  );
  // Deleted but still tracked files are listed too; skip them.
  return [...new Set(output.split("\0").filter(Boolean))]
    .filter((file) => existsSync(file))
    .sort();
}

/**
 * Load the Prettier package installed next to the `prettier` command on PATH.
 *
 * @returns {Promise<object>} The Prettier module.
 */
async function loadPrettier() {
  for (const directory of (process.env.PATH ?? "").split(delimiter)) {
    const command = join(directory, "prettier");
    if (!existsSync(command)) {
      continue;
    }
    // <prefix>/bin/prettier -> <package>/bin/prettier.cjs
    const packageDir = dirname(dirname(realpathSync(command)));
    return import(pathToFileURL(join(packageDir, "index.mjs")).href);
  }
  throw new Error(
    "prettier is not on PATH; run this script through `prek exec prettier-markdown`.",
  );
}

/**
 * Remove every whitespace character.
 *
 * @param {string} text Text to strip.
 * @returns {string} The text without whitespace.
 */
function withoutWhitespace(text) {
  return text.replace(/\s+/gu, "");
}

/**
 * Format the Markdown files and report what changed.
 *
 * @returns {Promise<number>} The process exit code.
 */
async function main() {
  const prettier = await loadPrettier();
  let rewritten = 0;
  let skipped = 0;

  for (const file of listMarkdownFiles()) {
    // prettier.format() does not read .prettierignore by itself.
    const { ignored } = await prettier.getFileInfo(file, {
      ignorePath: ".prettierignore",
    });
    if (ignored) {
      continue;
    }
    const original = readFileSync(file, "utf8");
    const options = (await prettier.resolveConfig(file)) ?? {};
    const formatted = await prettier.format(original, { ...options, filepath: file });

    if (formatted === original) {
      continue;
    }
    if (
      STANDARDS_PATH.test(file) &&
      withoutWhitespace(formatted) !== withoutWhitespace(original)
    ) {
      console.warn(
        `warning: ${file}: left unformatted; Prettier would change more than whitespace in a STANDARDS file`,
      );
      skipped += 1;
      continue;
    }
    writeFileSync(file, formatted);
    console.log(`formatted ${file}`);
    rewritten += 1;
  }

  // Mention STANDARDS only where it is installed, so other readers are not puzzled.
  const left = skipped > 0 ? `; ${skipped} STANDARDS file(s) left unformatted` : "";
  console.log(`Markdown: ${rewritten} file(s) formatted${left}.`);

  if (!existsSync(STANDARDS_CHECK)) {
    return 0;
  }

  // The STANDARDS check must still pass after formatting.
  console.log(`Running the STANDARDS workflow check (${STANDARDS_CHECK}).`);
  const check = spawnSync(process.execPath, [STANDARDS_CHECK], { stdio: "inherit" });
  return check.status ?? 1;
}

process.exitCode = await main();
