import { promises as fs } from "fs";
import { join } from "path";

export async function initCommand(): Promise<void> {
  const projectRoot = process.cwd();
  const orthoDir = join(projectRoot, ".ortho");

  try {
    await fs.mkdir(orthoDir, { recursive: true });
    console.log("✓ Created .ortho/ directory");

    // flag "wx" = create only if missing, so re-running init never wipes an
    // existing config or database.
    const writeIfMissing = async (dest: string, content: string): Promise<boolean> => {
      try {
        await fs.writeFile(dest, content, { flag: "wx" });
        return true;
      } catch (err: any) {
        if (err.code === "EEXIST") return false;
        throw err;
      }
    };

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
    const configCreated = await writeIfMissing(configDest, defaultConfig);
    console.log(configCreated ? "✓ Created .ortho/config.toml" : "• .ortho/config.toml already exists, kept");

    // Create database files (empty, will be initialized on first use)
    const dbPath = join(orthoDir, "ortho.db");
    const dbCreated = await writeIfMissing(dbPath, "");
    console.log(dbCreated ? "✓ Created .ortho/ortho.db" : "• .ortho/ortho.db already exists, kept");

    const vectorDbPath = join(orthoDir, "vectors.db");
    const vecCreated = await writeIfMissing(vectorDbPath, "");
    console.log(vecCreated ? "✓ Created .ortho/vectors.db" : "• .ortho/vectors.db already exists, kept");

    console.log("\n✓ Ortho initialized successfully!");
    console.log("Next: ortho scan");
  } catch (error) {
    console.error("✗ Initialization failed:", error);
    process.exit(1);
  }
}
