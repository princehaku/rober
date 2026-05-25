import type {
  EvidenceToolsResponse,
  HardwareMaterialsResponse,
  HealthResponse,
  ProofBoundaryResponse,
  RouteDebugSummaryResponse,
  TrainingLabelingResponse,
} from "../shared/contracts";

export interface RouteDebugInputs {
  statusJson: string;
  taskRecord: string;
  taskRecordDir: string;
  elevatorRouteReconciliation: string;
}

export interface WorkstationSnapshot {
  health: HealthResponse;
  routeSummary: RouteDebugSummaryResponse;
  evidenceTools: EvidenceToolsResponse;
  hardwareMaterials: HardwareMaterialsResponse;
  trainingLabeling: TrainingLabelingResponse;
  proofBoundary: ProofBoundaryResponse;
}

// client 层集中维护 API 路径，避免组件散落字符串后破坏契约。
const API_ENDPOINTS = {
  health: "/api/health",
  routeDebugSummary: "/api/route/debug-summary",
  evidenceTools: "/api/tools/evidence",
  hardwareMaterials: "/api/tools/hardware-materials",
  trainingLabeling: "/api/tools/training-labeling",
  proofBoundary: "/api/proof-boundary",
} as const;

async function loadJson<T>(url: string): Promise<T> {
  // fetch 失败只抛出 API 层错误；App 负责把错误保持在 fail-closed 展示。
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return (await response.json()) as T;
}

function routeDebugUrl(inputs: RouteDebugInputs): string {
  // 空字段不进入 query，让后端明确返回 not_provided，而不是读取空路径。
  const params = new URLSearchParams();
  Object.entries(inputs).forEach(([key, value]) => {
    const trimmed = value.trim();
    if (trimmed) {
      params.set(key, trimmed);
    }
  });
  const query = params.toString();
  return query ? `${API_ENDPOINTS.routeDebugSummary}?${query}` : API_ENDPOINTS.routeDebugSummary;
}

export async function getHealth(): Promise<HealthResponse> {
  // health 只证明工作站 API 在线，不代表机器人或云端在线。
  return loadJson<HealthResponse>(API_ENDPOINTS.health);
}

export async function getRouteDebugSummary(inputs: RouteDebugInputs): Promise<RouteDebugSummaryResponse> {
  // Route Debug query 拼接只允许从统一 client 进入，组件只传本地表单状态。
  return loadJson<RouteDebugSummaryResponse>(routeDebugUrl(inputs));
}

export async function getEvidenceTools(): Promise<EvidenceToolsResponse> {
  // Evidence Tools 只读 JSON fixture 索引，不触发旧 Python gate。
  return loadJson<EvidenceToolsResponse>(API_ENDPOINTS.evidenceTools);
}

export async function getHardwareMaterials(): Promise<HardwareMaterialsResponse> {
  // WAVE ROVER materials 只读扫描本地 fixture，不连接真实硬件或恢复 Python gate。
  return loadJson<HardwareMaterialsResponse>(API_ENDPOINTS.hardwareMaterials);
}

export async function getTrainingLabeling(): Promise<TrainingLabelingResponse> {
  // Training/Labeling 当前是占位 API，必须保留 real_pipeline_connected=false。
  return loadJson<TrainingLabelingResponse>(API_ENDPOINTS.trainingLabeling);
}

export async function getProofBoundary(): Promise<ProofBoundaryResponse> {
  // Proof Boundary 是页面安全锚点，所有主动作能力都由后端契约给出。
  return loadJson<ProofBoundaryResponse>(API_ENDPOINTS.proofBoundary);
}

export async function loadWorkstationSnapshot(inputs: RouteDebugInputs): Promise<WorkstationSnapshot> {
  // 刷新同时拉取全部只读 API，避免分页面状态互相漂移。
  const [health, routeSummary, evidenceTools, hardwareMaterials, trainingLabeling, proofBoundary] = await Promise.all([
    getHealth(),
    getRouteDebugSummary(inputs),
    getEvidenceTools(),
    getHardwareMaterials(),
    getTrainingLabeling(),
    getProofBoundary(),
  ]);

  return {
    health,
    routeSummary,
    evidenceTools,
    hardwareMaterials,
    trainingLabeling,
    proofBoundary,
  };
}
