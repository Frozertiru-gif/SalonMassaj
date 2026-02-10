import fs from "node:fs";
import path from "node:path";

const pagesManifestPath = path.join(process.cwd(), ".next", "build-manifest.json");
const appManifestPath = path.join(process.cwd(), ".next", "app-build-manifest.json");

if (!fs.existsSync(pagesManifestPath) || !fs.existsSync(appManifestPath)) {
  console.error("Missing build manifests. Run `next build` first.");
  process.exit(1);
}

const pagesManifest = JSON.parse(fs.readFileSync(pagesManifestPath, "utf8"));
const appManifest = JSON.parse(fs.readFileSync(appManifestPath, "utf8"));

const files = [
  ...(pagesManifest.rootMainFiles ?? []),
  ...((appManifest.pages ?? {})["/page"] ?? [])
];

const uniqueFiles = [...new Set(files)];
const bySize = uniqueFiles
  .map((file) => {
    const fullPath = path.join(process.cwd(), ".next", file);
    const size = fs.existsSync(fullPath) ? fs.statSync(fullPath).size : 0;
    return { file, size };
  })
  .sort((a, b) => b.size - a.size);

const totalBytes = bySize.reduce((sum, item) => sum + item.size, 0);
const toKb = (bytes) => (bytes / 1024).toFixed(1);

console.log(`Route / initial JS (approx): ${toKb(totalBytes)} kB (${bySize.length} files)`);
console.log("Top chunks:");
for (const item of bySize.slice(0, 8)) {
  console.log(` - ${item.file}: ${toKb(item.size)} kB`);
}
