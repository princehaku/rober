import {
  API_ROUTES,
  NOT_PROVEN_ITEMS,
  PROOF_FLAGS,
  WORKSTATION_VERSION,
} from "../shared/contracts";
import type { HealthResponse, ProofBoundaryResponse, TrainingLabelingResponse } from "../shared/contracts";

export async function buildTrainingLabelingResponse(): Promise<TrainingLabelingResponse> {
  // Training/Labeling 仍未接真实流水线，页面只能显示占位状态。
  const entries = ["training", "labeling"].map((name) => ({
    name,
    path: `pc-tools/${name}`,
    status: "placeholder_not_connected" as const,
    real_pipeline_connected: false as const,
  }));

  return {
    schema: "trashbot.pc_tools_workstation.training_labeling.v1",
    ...PROOF_FLAGS,
    entries,
  };
}

export function buildProofBoundary(): ProofBoundaryResponse {
  // Proof Boundary 把 Node/Vue 可证明的软件形状与真实机器人能力明确分开。
  return {
    schema: "trashbot.pc_tools_workstation.proof_boundary.v2",
    ...PROOF_FLAGS,
    can_prove: [
      "Node/Vue workstation can index local JSON fixtures under pc-tools/evidence/fixtures",
      "Node Route JSON Loader can read local status/task/reconciliation JSON into a safe summary",
      "UI/API expose fail-closed software proof fields",
    ],
    not_proven: [...NOT_PROVEN_ITEMS],
    enforced_fields: PROOF_FLAGS,
    control_policy: {
      workstation_executes_control: false,
      route_loader_mode: "local_json_readonly",
      recovery_path: "Load local JSON proof files in the Node workstation and attach resulting summaries to sprint evidence.",
    },
  };
}

export function buildHealth(): HealthResponse {
  // health 只证明 Node API 存活，不证明机器人、ROS2 或云端链路存活。
  return {
    schema: "trashbot.pc_tools_workstation.health.v1",
    ...PROOF_FLAGS,
    version: WORKSTATION_VERSION,
    mode: "pc_only_readonly_workstation",
    api_routes: [...API_ROUTES],
  };
}
