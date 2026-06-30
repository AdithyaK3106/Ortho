export interface DependencyEdge {
  repo_id: string;
  package_name: string;
  version?: string;
  is_external: boolean;
}

export interface DependencyGraph {
  repo_id: string;
  edges: DependencyEdge[];
}
