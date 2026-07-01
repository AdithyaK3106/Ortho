import { promises as fs } from "fs";
import { join } from "path";

export async function initCommand(): Promise<void> {
  const projectRoot = process.cwd();
  const orthoDir = join(projectRoot, ".ortho");

  try {
    await fs.mkdir(orthoDir, { recursive: true });
    console.log("✓ Created .ortho/ directory");

    // Create default config template
    const configDest = join(orthoDir, "config.toml");
    const defaultConfig = `[project]
name = "my-project"
root = "."
primary_language = "python"

[indexing]
languages = ["python"]
exclude_patterns = ["**/node_modules", "**/__pycache__"]

[context_hub]
embedding_model = "text-embedding-3-small"
embedding_provider = "openai"

[llm]
default_model = "claude-sonnet-4-6"
fallback_model = "claude-haiku-4-5-20251001"
max_tokens = 8192
`;
    await fs.writeFile(configDest, defaultConfig);
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
