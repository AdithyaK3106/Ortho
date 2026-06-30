export interface CallGraphBuilder {
  build_call_graph(): Promise<CallEdge[]>;
}

export type { CallEdge } from "./symbol";
