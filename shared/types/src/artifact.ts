export type ArtifactType =
  | "frd"
  | "adr"
  | "architecture"
  | "spec"
  | "decision"
  | "lesson_learned"
  | "dev_note"
  | "benchmark"
  | "conversation"
  | "git_metadata"
  | "project_memory"
  | "evidence"
  | "workflow_run";

export interface Artifact {
  id: string;
  repo_id: string;
  type: ArtifactType;
  title: string;
  content: string;
  source: string;
  created_at: Date;
  last_modified: Date;
  relevance_scope: "global" | "project" | "module" | "file";
  tags: string[];
  related_symbols?: string[];
  embedding?: number[];
  estimated_tokens: number;
}
