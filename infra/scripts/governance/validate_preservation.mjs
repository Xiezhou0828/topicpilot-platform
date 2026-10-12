#!/usr/bin/env node

import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";

function hash(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

const manifestPath = process.argv[2];
if (!manifestPath) throw new Error("Usage: validate_preservation.mjs <manifest.json>");
const rows = JSON.parse(readFileSync(manifestPath, "utf8"));
const copied = rows.filter((row) => row.copied);
const missing = copied.filter((row) => !existsSync(row.sourcePath) || !existsSync(row.backupPath));
const mismatched = copied.filter((row) => {
  if (!existsSync(row.sourcePath) || !existsSync(row.backupPath)) return true;
  return hash(row.sourcePath) !== hash(row.backupPath) || hash(row.sourcePath) !== row.sha256 || hash(row.backupPath) !== row.backupSha256;
});
const result = {
  manifestPath,
  rows: rows.length,
  copied: copied.length,
  skipped: rows.length - copied.length,
  missing: missing.map((row) => row.sourcePath ?? row.relativePath),
  mismatched: mismatched.map((row) => row.sourcePath ?? row.relativePath),
  status: missing.length === 0 && mismatched.length === 0 ? "PRESERVATION_VERIFIED" : "PRESERVATION_FAILED",
};
process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
process.exitCode = result.status === "PRESERVATION_VERIFIED" ? 0 : 2;
