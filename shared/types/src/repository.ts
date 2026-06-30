export interface Repository {
  id: string;
  root_path: string;
  name: string;
  languages: string[];
  indexed_at: Date;
  git_remote?: string;
}

export interface File {
  id: string;
  repo_id: string;
  rel_path: string;
  language: string;
  size_bytes: number;
  last_modified: Date;
  git_last_commit?: string;
}
