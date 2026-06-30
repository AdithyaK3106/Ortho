import { promises as fs } from "fs";
import { join } from "path";

export async function initCommand(): Promise<void> {
  const projectRoot = process.cwd();
  const orthoDir = join(projectRoot, ".ortho");

  try {
    await fs.mkdir(orthoDir, { recursive: true });
    console.log("✓ Created .ortho/ directory");

    // Copy config template
    const configSource = join(__dirname, "../../../.ortho/config.toml");
    const configDest = join(orthoDir, "config.toml");
    await fs.copyFile(configSource, configDest);
    console.log("✓ Created .ortho/config.toml");

    // Create database files (empty, will be initialized on first use)
    const dbPath = join(orthoDir, "ortho.db");
    await fs.writeFile(dbPath, "");
    console.log("✓ Created .ortho/ortho.db");

    const vectorDbPath = join(orthoDir, "vectors.db");
    await fs.writeFile(vectorDbPath, "");
    console.log("✓ Created .ortho/vectors.db");

    console.log("\n✓ Ortho initialized successfully!");
    console.log("Next: ortho scan");
  } catch (error) {
    console.error("✗ Initialization failed:", error);
    process.exit(1);
  }
}
