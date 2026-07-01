import { promises as fs } from "fs";
import { join } from "path";
import { mkdtemp } from "fs";
import { promisify } from "util";
import { tmpdir } from "os";
import { initCommand } from "./init";

const mkdtempAsync = promisify(mkdtemp);

describe("initCommand", () => {
  let testDir: string;
  const originalCwd = process.cwd;

  beforeEach(async () => {
    testDir = await mkdtempAsync(join(tmpdir(), "ortho-test-"));
    process.cwd = () => testDir;
  });

  afterEach(async () => {
    process.cwd = originalCwd;
    try {
      await fs.rm(testDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  it("should create .ortho directory", async () => {
    await initCommand();
    const orthoDir = join(testDir, ".ortho");
    const stat = await fs.stat(orthoDir);
    expect(stat.isDirectory()).toBe(true);
  });

  it("should create ortho.db file", async () => {
    await initCommand();
    const dbPath = join(testDir, ".ortho", "ortho.db");
    const stat = await fs.stat(dbPath);
    expect(stat.isFile()).toBe(true);
  });

  it("should create vectors.db file", async () => {
    await initCommand();
    const vectorsPath = join(testDir, ".ortho", "vectors.db");
    const stat = await fs.stat(vectorsPath);
    expect(stat.isFile()).toBe(true);
  });

  it("should create config.toml file", async () => {
    await initCommand();
    const configPath = join(testDir, ".ortho", "config.toml");
    const stat = await fs.stat(configPath);
    expect(stat.isFile()).toBe(true);
  });

  it("should handle already initialized directory", async () => {
    // First init
    await initCommand();

    // Second init should not error
    await initCommand();

    // Files should still exist
    const orthoDir = join(testDir, ".ortho");
    const stat = await fs.stat(orthoDir);
    expect(stat.isDirectory()).toBe(true);
  });

  it("should create all required files in .ortho directory", async () => {
    await initCommand();
    const orthoDir = join(testDir, ".ortho");
    const files = await fs.readdir(orthoDir);

    expect(files).toContain("ortho.db");
    expect(files).toContain("vectors.db");
    expect(files).toContain("config.toml");
  });
});
