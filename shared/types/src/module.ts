export type ModuleType = "regular" | "namespace";

export interface Module {
  name: string;
  root_path: string;
  type: ModuleType;
  file_paths: string[];
}
