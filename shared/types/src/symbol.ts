export type SymbolKind = "function" | "class" | "method" | "variable" | "constant" | "type";
export type Visibility = "public" | "private" | "protected" | "internal";

export interface Symbol {
  id: string;
  repo_id: string;
  file_id: string;
  name: string;
  qualified_name: string;
  kind: SymbolKind;
  visibility: Visibility;
  start_line: number;
  end_line: number;
  docstring?: string;
  signature?: string;
}

export interface CallEdge {
  caller_id: string;
  callee_id: string;
  call_site_line: number;
  confidence: number;
}

export interface ImportEdge {
  importer_file_id: string;
  imported_file_id?: string;
  imported_module: string;
  is_external: boolean;
  symbols_imported: string[];
}
