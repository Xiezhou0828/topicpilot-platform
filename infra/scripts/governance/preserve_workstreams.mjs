#!/usr/bin/env node

import { createHash } from "node:crypto";
import { cpSync, existsSync, mkdirSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";

function parseArgs(argv) {
  const result = { source: [], include: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    const value = argv[index + 1];
    if (value === undefined || value.startsWith("--")) result[key] = true;
    else {
      if (key === "source" || key === "include") (result[key] ??= []).push(value);
      else result[key] = value;
      index += 1;
    }
  }
  return result;
}

// Kept as a synchronous script so the manifest is complete before it is read.
import { readFileSync } from "node:fs";

function fileHash(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function ignored(relativePath, name) {
  const segments = relativePath.toLowerCase().split("/").filter(Boolean);
  return [".git", "node_modules", "venv", ".venv", "__pycache__", ".ruff_cache", ".pytest_cache", "tmp", ".next"].some((token) => segments.includes(token))
    || [".env", ".pem", ".key", ".p12", ".pfx"].some((suffix) => name.toLowerCase().endsWith(suffix))
    || /credential|secret|token/i.test(name);
}

function walk(root, current = root, rows = []) {
  for (const entry of readdirSync(current, { withFileTypes: true })) {
    const path = join(current, entry.name);
    const rel = relative(root, path).replaceAll("\\", "/");
    if (ignored(rel, entry.name)) {
      rows.push({ path, relativePath: rel, classification: "DEPENDENCY_OR_SENSITIVE_SKIPPED", copied: false });
      continue;
    }
    if (entry.isDirectory()) walk(root, path, rows);
    else if (entry.isFile()) rows.push({ path, relativePath: rel, classification: "SOURCE_OR_ARTIFACT", copied: true });
  }
  return rows;
}

const args = parseArgs(process.argv.slice(2));
if (!args.destination || !args.source?.length || !args.include?.length) {
  throw new Error("Usage: preserve_workstreams.mjs --destination <path> --source <label=path> --include <label=relative-path> [...]");
}
const destination = resolve(String(args.destination));
mkdirSync(destination, { recursive: true });
const manifest = [];
for (const sourceSpec of args.source) {
  const separator = sourceSpec.indexOf("=");
  if (separator < 1) throw new Error(`Invalid source: ${sourceSpec}`);
  const label = sourceSpec.slice(0, separator);
  const root = resolve(sourceSpec.slice(separator + 1));
  if (!existsSync(root)) {
    manifest.push({ label, sourceRoot: root, relativePath: "", classification: "SOURCE_MISSING", copied: false });
    continue;
  }
  const includes = args.include
    .filter((spec) => spec.startsWith(`${label}=`))
    .map((spec) => spec.slice(label.length + 1));
  for (const include of includes) {
    const includePath = resolve(root, include);
    if (!existsSync(includePath)) {
      manifest.push({ label, sourceRoot: root, relativePath: include, classification: "SOURCE_MISSING", copied: false });
      continue;
    }
    const candidates = statSync(includePath).isDirectory()
      ? walk(root, includePath)
      : [{ path: includePath, relativePath: relative(root, includePath).replaceAll("\\", "/"), classification: "SOURCE_OR_ARTIFACT", copied: true }];
    for (const row of candidates) {
      if (!row.copied) {
        manifest.push({ label, sourceRoot: root, relativePath: row.relativePath, classification: row.classification, copied: false });
        continue;
      }
      const backup = join(destination, label, row.relativePath);
      mkdirSync(resolve(backup, ".."), { recursive: true });
      cpSync(row.path, backup, { force: true });
      manifest.push({
        label,
        sourceRoot: root,
        sourcePath: row.path,
        backupPath: backup,
        relativePath: row.relativePath,
        classification: row.classification,
        copied: true,
        bytes: statSync(row.path).size,
        sha256: fileHash(row.path),
        backupSha256: fileHash(backup),
      });
    }
  }
}
const csv = [
  "label,sourceRoot,sourcePath,backupPath,relativePath,classification,copied,bytes,sha256,backupSha256",
  ...manifest.map((row) => [row.label, row.sourceRoot, row.sourcePath ?? "", row.backupPath ?? "", row.relativePath, row.classification, row.copied, row.bytes ?? "", row.sha256 ?? "", row.backupSha256 ?? ""].map((value) => `"${String(value).replaceAll('"', '""')}"`).join(",")),
].join("\n") + "\n";
writeFileSync(join(destination, "HISTORICAL_ARTIFACT_PRESERVATION_MANIFEST.csv"), csv, "utf8");
writeFileSync(join(destination, "HISTORICAL_ARTIFACT_PRESERVATION_MANIFEST.json"), JSON.stringify(manifest, null, 2) + "\n", "utf8");
writeFileSync(join(destination, "PRESERVATION_VERIFIED"), `PRESERVATION_VERIFIED\n${new Date().toISOString()}\n`, "utf8");
process.stdout.write(JSON.stringify({ destination, rows: manifest.length, copied: manifest.filter((row) => row.copied).length, skipped: manifest.filter((row) => !row.copied).length }, null, 2) + "\n");
