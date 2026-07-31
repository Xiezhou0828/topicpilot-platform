import { copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = resolve(packageRoot, "src/schema.d.ts");
const destination = resolve(packageRoot, "../../apps/web/app/lib/generated-api.d.ts");

await mkdir(dirname(destination), { recursive: true });
await copyFile(source, destination);

console.log(`Synchronized generated API types to ${destination}`);
