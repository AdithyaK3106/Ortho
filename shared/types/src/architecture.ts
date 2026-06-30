export type ArchStyle = "layered" | "hexagonal" | "mvc" | "microservices" | "flat" | "unknown";

export interface ArchitectureModel {
  repo_id: string;
  style: ArchStyle;
  style_confidence: number;
  layers: Layer[];
  subsystems: Subsystem[];
  service_boundaries: ServiceBoundary[];
  detected_at: Date;
}

export interface Layer {
  id: string;
  name: string;
  file_ids: string[];
  depends_on: string[];
  confidence: number;
  evidence: string[];
}

export interface Subsystem {
  id: string;
  name: string;
  file_ids: string[];
  layer_id?: string;
  coupling_score: number;
}

export interface ServiceBoundary {
  id: string;
  name: string;
  modules: string[];
}
