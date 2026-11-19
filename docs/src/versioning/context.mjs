import { readFileSync } from "node:fs";
import { SITE_BASE } from "./versions.mjs";

export function getVersionContext() {
  if (process.env.PYDELITY_DOCS_CONTEXT) {
    return JSON.parse(readFileSync(process.env.PYDELITY_DOCS_CONTEXT, "utf8"));
  }
  // A build of the current tree has no version label.
  return {
    currentVersion: null,
    currentBase: SITE_BASE,
    versions: [],
  };
}
