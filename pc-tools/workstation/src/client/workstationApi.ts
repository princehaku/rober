import type {
  EvidenceToolsResponse,
  HardwareMaterialsResponse,
  O7CloudArchiveTasksProbeResponse,
  O7CloudArchiveTasksResponse,
  O7CloudOperatorConsoleProbeResponse,
  O7LabelingPreviewResponse,
  O7LiveEndpointsManifestResponse,
  HealthResponse,
  O7OperatorConsoleResponse,
  O7PreviewsAcceptanceResponse,
  O7RealtimeElevatorProbeResponse,
  O7RealtimeElevatorPreviewResponse,
  O7RouteReplayPreviewResponse,
  O7RtcSignalingContractProbeResponse,
  O7SafeCommandPreviewResponse,
  O7VoicePreviewResponse,
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
  o7OperatorConsole: O7OperatorConsoleResponse;
  proofBoundary: ProofBoundaryResponse;
}

export type O7FixturePreviewKind = "realtimeElevator" | "routeReplay" | "labeling" | "voice" | "safeCommand";

export interface O7FixturePreviewInputs {
  realtimeElevator: string;
  routeReplay: string;
  labeling: string;
  voice: string;
  safeCommand: string;
}

export interface O7FixturePreviewResponses {
  realtimeElevator: O7RealtimeElevatorPreviewResponse;
  routeReplay: O7RouteReplayPreviewResponse;
  labeling: O7LabelingPreviewResponse;
  voice: O7VoicePreviewResponse;
  safeCommand: O7SafeCommandPreviewResponse;
}

// client 层集中维护 API 路径，避免组件散落字符串后破坏契约。
const API_ENDPOINTS = {
  health: "/api/health",
  routeDebugSummary: "/api/route/debug-summary",
  evidenceTools: "/api/tools/evidence",
  hardwareMaterials: "/api/hardware/wave-rover/material-coverage",
  trainingLabeling: "/api/tools/training-labeling",
  o7OperatorConsole: "/api/o7/operator-console",
  o7PreviewsAcceptance: "/api/o7/previews/acceptance",
  o7LiveEndpointsManifest: "/api/o7/live-endpoints/manifest",
  o7CloudOperatorConsoleProbe: "/api/o7/cloud-operator-console-probe",
  o7CloudArchiveTasksProbe: "/api/o7/cloud-archive/tasks-probe",
  o7RealtimeElevatorProbe: "/api/o7/realtime-elevator-probe",
  o7RtcSignalingContractProbe: "/api/o7/rtc-signaling-contract-probe",
  o7RealtimeElevatorPreview: "/api/o7/realtime-elevator-preview",
  o7RouteReplayPreview: "/api/o7/route-replay-preview",
  o7LabelingPreview: "/api/o7/labeling-preview",
  o7VoicePreview: "/api/o7/voice-preview",
  o7SafeCommandPreview: "/api/o7/safe-command-preview",
  o7CloudArchiveTasks: "/api/o7/cloud-archive/tasks",
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

function previewUrl(endpoint: string, fixtureJson: string): string {
  // 空路径不拼 query，让后端返回 not_provided，而不是由前端伪造 not_loaded。
  const trimmed = fixtureJson.trim();
  if (!trimmed) {
    return endpoint;
  }
  const params = new URLSearchParams();
  params.set("fixtureJson", trimmed);
  return `${endpoint}?${params.toString()}`;
}

function cloudArchiveTasksUrl(archiveJson: string): string {
  // archive 路径只在 operator 点击后拼入 query，页面加载不会自动读取本机文件。
  const trimmed = archiveJson.trim();
  if (!trimmed) {
    return API_ENDPOINTS.o7CloudArchiveTasks;
  }
  const params = new URLSearchParams();
  params.set("archiveJson", trimmed);
  return `${API_ENDPOINTS.o7CloudArchiveTasks}?${params.toString()}`;
}

function cloudOperatorConsoleProbeUrl(baseUrl: string): string {
  // probe 只把 operator 输入交给 PC 后端；SSRF 和 schema 风险由后端统一 fail-closed。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  return `${API_ENDPOINTS.o7CloudOperatorConsoleProbe}?${params.toString()}`;
}

function cloudArchiveTasksProbeUrl(baseUrl: string): string {
  // archive probe 与 operator-console probe 共用本机回环约束，实际 SSRF 防护仍由后端执行。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  return `${API_ENDPOINTS.o7CloudArchiveTasksProbe}?${params.toString()}`;
}

function realtimeElevatorProbeUrl(baseUrl: string): string {
  // realtime/elevator probe 同样只把 base URL 交给后端，浏览器不直接访问 relay。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  return `${API_ENDPOINTS.o7RealtimeElevatorProbe}?${params.toString()}`;
}

function rtcSignalingContractProbeUrl(baseUrl: string): string {
  // RTC contract probe 只把本机 relay base URL 交给后端，浏览器不创建 WebRTC 或携带 token。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  return `${API_ENDPOINTS.o7RtcSignalingContractProbe}?${params.toString()}`;
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

export async function getO7OperatorConsole(): Promise<O7OperatorConsoleResponse> {
  // O7 console 必须由后端契约驱动，前端不自行拼接 KR 状态或控制能力。
  return loadJson<O7OperatorConsoleResponse>(API_ENDPOINTS.o7OperatorConsole);
}

export async function getO7PreviewsAcceptance(): Promise<O7PreviewsAcceptanceResponse> {
  // O7 Previews guard 只读取本机摘要 endpoint，不触发 probe、fixture 读取或真实控制链路。
  return loadJson<O7PreviewsAcceptanceResponse>(API_ENDPOINTS.o7PreviewsAcceptance);
}

export async function getO7LiveEndpointsManifest(): Promise<O7LiveEndpointsManifestResponse> {
  // manifest 只读取后端 env 脱敏摘要；它不是 ping/connect/test command。
  return loadJson<O7LiveEndpointsManifestResponse>(API_ENDPOINTS.o7LiveEndpointsManifest);
}

export async function getO7CloudOperatorConsoleProbe(baseUrl: string): Promise<O7CloudOperatorConsoleProbeResponse> {
  // 前端不直连 cloud relay；只调用本机 Node probe API，避免浏览器绕过后端安全检查。
  return loadJson<O7CloudOperatorConsoleProbeResponse>(cloudOperatorConsoleProbeUrl(baseUrl));
}

export async function getO7CloudArchiveTasksProbe(baseUrl: string): Promise<O7CloudArchiveTasksProbeResponse> {
  // 前端不直连 relay；PC 后端负责只读拉取本机 /api/o7/cloud-archive/tasks 并扫描危险字段。
  return loadJson<O7CloudArchiveTasksProbeResponse>(cloudArchiveTasksProbeUrl(baseUrl));
}

export async function getO7RealtimeElevatorProbe(baseUrl: string): Promise<O7RealtimeElevatorProbeResponse> {
  // 前端不直连 relay；PC 后端负责 loopback-only 拉取 snapshot 并扫描 KR1/KR2 危险字段。
  return loadJson<O7RealtimeElevatorProbeResponse>(realtimeElevatorProbeUrl(baseUrl));
}

export async function getO7RtcSignalingContractProbe(baseUrl: string): Promise<O7RtcSignalingContractProbeResponse> {
  // 前端不直连 relay、不发 bearer；PC 后端只拉取 fail-closed RTC signaling/media 合同。
  return loadJson<O7RtcSignalingContractProbeResponse>(rtcSignalingContractProbeUrl(baseUrl));
}

export async function getO7RealtimeElevatorPreview(fixtureJson: string): Promise<O7RealtimeElevatorPreviewResponse> {
  // preview 只读本地 JSON 摘要；路径拼接集中在 client，组件不能散落 API URL。
  return loadJson<O7RealtimeElevatorPreviewResponse>(previewUrl(API_ENDPOINTS.o7RealtimeElevatorPreview, fixtureJson));
}

export async function getO7RouteReplayPreview(fixtureJson: string): Promise<O7RouteReplayPreviewResponse> {
  // Route replay preview 不提供播放入口，只消费后端 fail-closed 摘要。
  return loadJson<O7RouteReplayPreviewResponse>(previewUrl(API_ENDPOINTS.o7RouteReplayPreview, fixtureJson));
}

export async function getO7LabelingPreview(fixtureJson: string): Promise<O7LabelingPreviewResponse> {
  // Labeling preview 不提交、不回滚、不导出，只读取 fixture summary。
  return loadJson<O7LabelingPreviewResponse>(previewUrl(API_ENDPOINTS.o7LabelingPreview, fixtureJson));
}

export async function getO7VoicePreview(fixtureJson: string): Promise<O7VoicePreviewResponse> {
  // Voice preview 不监听、不发送 TTS、不播放，只展示本地 fixture 摘要。
  return loadJson<O7VoicePreviewResponse>(previewUrl(API_ENDPOINTS.o7VoicePreview, fixtureJson));
}

export async function getO7SafeCommandPreview(fixtureJson: string): Promise<O7SafeCommandPreviewResponse> {
  // Safe command preview 不连接 command API 或 robot ACK，所有控制字段必须保持 false。
  return loadJson<O7SafeCommandPreviewResponse>(previewUrl(API_ENDPOINTS.o7SafeCommandPreview, fixtureJson));
}

export async function getO7CloudArchiveTasks(archiveJson: string): Promise<O7CloudArchiveTasksResponse> {
  // Cloud archive task API 只读本地 fixture，不连接 O6 云归档、实时、标注、语音或命令 API。
  return loadJson<O7CloudArchiveTasksResponse>(cloudArchiveTasksUrl(archiveJson));
}

export async function loadO7FixturePreview(
  kind: O7FixturePreviewKind,
  fixtureJson: string,
): Promise<O7FixturePreviewResponses[O7FixturePreviewKind]> {
  // switch 让五个 API 的路由集中收口，后续改 endpoint 不需要碰展示组件。
  switch (kind) {
    case "realtimeElevator":
      return getO7RealtimeElevatorPreview(fixtureJson);
    case "routeReplay":
      return getO7RouteReplayPreview(fixtureJson);
    case "labeling":
      return getO7LabelingPreview(fixtureJson);
    case "voice":
      return getO7VoicePreview(fixtureJson);
    case "safeCommand":
      return getO7SafeCommandPreview(fixtureJson);
  }
}

export async function loadWorkstationSnapshot(inputs: RouteDebugInputs): Promise<WorkstationSnapshot> {
  // 刷新同时拉取全部只读 API，避免分页面状态互相漂移。
  const [health, routeSummary, evidenceTools, hardwareMaterials, trainingLabeling, o7OperatorConsole, proofBoundary] = await Promise.all([
    getHealth(),
    getRouteDebugSummary(inputs),
    getEvidenceTools(),
    getHardwareMaterials(),
    getTrainingLabeling(),
    getO7OperatorConsole(),
    getProofBoundary(),
  ]);

  return {
    health,
    routeSummary,
    evidenceTools,
    hardwareMaterials,
    trainingLabeling,
    o7OperatorConsole,
    proofBoundary,
  };
}
