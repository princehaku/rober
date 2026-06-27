import type {
  EvidenceToolsResponse,
  HardwareMaterialsResponse,
  O7CloudArchiveTasksProbeResponse,
  O7CloudArchiveTasksResponse,
  O7ConsumerTaskDetailResponse,
  O7ConsumerTaskListResponse,
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
  RobotControlProofRefreshProxyResponse,
  RobotControlCameraCloseProxyResponse,
  RobotControlCameraFirstFrameProbeProxyResponse,
  RobotControlCameraMjpegStatusResponse,
  RobotControlCameraOfferProxyResponse,
  RobotControlBaseCommandProxyResponse,
  RobotControlBaseCommandRequest,
  RobotControlBaseFeedbackSamplesProxyResponse,
  RobotControlFreeRoamAutonomyRequest,
  RobotControlFreeRoamAutonomyLatestResponse,
  RobotControlFreeRoamAutonomyResponse,
  RobotControlMapLifecycleRequest,
  RobotControlMapLifecycleResponse,
  RobotControlMapPreviewResponse,
  RobotControlNavGoalPreflightRequest,
  RobotControlNavGoalPreflightResponse,
  RobotControlNavGoalExecutionRequest,
  RobotControlNavGoalExecutionResponse,
  RobotControlNavGoalExecutionLatestResponse,
  RobotControlDeliveryCompleteRequest,
  RobotControlDeliveryCompleteResponse,
  RobotControlDeliveryLatestResponse,
  RobotControlDeliveryGapCheckResponse,
  RobotControlNav2LifecycleResponse,
  RobotControlOperatorReportProxyResponse,
  RobotControlOperatorReportRequest,
  RobotControlSummaryResponse,
  RobotControlRadarLifecycleResponse,
  RobotControlRadarStatusResponse,
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
  o7ConsumerTaskList: "/api/o7/consumer-read/tasks",
  o7CloudArchiveTasksProbe: "/api/o7/cloud-archive/tasks-probe",
  o7ConsumerTaskDetailPrefix: "/api/o7/consumer-read/tasks/",
  o7RealtimeElevatorProbe: "/api/o7/realtime-elevator-probe",
  o7RtcSignalingContractProbe: "/api/o7/rtc-signaling-contract-probe",
  o7RealtimeElevatorPreview: "/api/o7/realtime-elevator-preview",
  o7RouteReplayPreview: "/api/o7/route-replay-preview",
  o7LabelingPreview: "/api/o7/labeling-preview",
  o7VoicePreview: "/api/o7/voice-preview",
  o7SafeCommandPreview: "/api/o7/safe-command-preview",
  o7CloudArchiveTasks: "/api/o7/cloud-archive/tasks",
  robotControlSummary: "/api/robot-control/summary",
  robotControlBaseManual: "/api/robot-control/base/manual",
  robotControlBaseFirstJog: "/api/robot-control/base/first-jog",
  robotControlBaseStop: "/api/robot-control/base/stop",
  robotControlBaseFeedbackSamples: "/api/robot-control/base/feedback-samples",
  robotControlRadarStatus: "/api/robot-control/radar/status",
  robotControlRadarScanProofRefresh: "/api/robot-control/radar/scan-proof/refresh",
  robotControlRadarStart: "/api/robot-control/radar/start",
  robotControlRadarStop: "/api/robot-control/radar/stop",
  robotControlMapProofRefresh: "/api/robot-control/map/proof/refresh",
  robotControlMapPreview: "/api/robot-control/map/preview",
  robotControlNav2Start: "/api/robot-control/nav2/start",
  robotControlNav2Stop: "/api/robot-control/nav2/stop",
  robotControlNav2ProofRefresh: "/api/robot-control/nav2/proof/refresh",
  robotControlNav2GoalPreflight: "/api/robot-control/nav2/goal/preflight",
  robotControlNav2GoalExecute: "/api/robot-control/nav2/goal/execute",
  robotControlNav2GoalExecutionLatest: "/api/robot-control/nav2/goal/execution/latest",
  robotControlDeliveryLatest: "/api/robot-control/delivery/latest",
  robotControlDeliveryCheck: "/api/robot-control/delivery/check",
  robotControlDeliveryComplete: "/api/robot-control/delivery/complete",
  robotControlLocalizeReset: "/api/robot-control/localize/reset",
  robotControlMapList: "/api/robot-control/map/list",
  robotControlMapStart: "/api/robot-control/map/start",
  robotControlMapSave: "/api/robot-control/map/save",
  robotControlMapReset: "/api/robot-control/map/reset",
  robotControlFreeRoamAutonomyStart: "/api/robot-control/free-roam/autonomy/start",
  robotControlFreeRoamAutonomyStop: "/api/robot-control/free-roam/autonomy/stop",
  robotControlFreeRoamAutonomyLatest: "/api/robot-control/free-roam/autonomy/latest",
  robotControlCameraOffer: "/api/robot-control/camera/offer",
  robotControlCameraFirstFrameProbe: "/api/robot-control/camera/first-frame/probe",
  robotControlCameraMjpeg: "/api/robot-control/camera/mjpeg",
  robotControlCameraMjpegStatus: "/api/robot-control/camera/mjpeg/status",
  robotControlCameraPeersPrefix: "/api/robot-control/camera/peers/",
  robotControlOperatorReport: "/api/robot-control/operator/report",
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

async function postJson<T>(url: string, body: unknown): Promise<T> {
  // POST 只用于 workstation 固定代理；失败时仍由调用方保持 fail-closed UI。
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => null);
  if (payload === null) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return payload as T;
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

function robotControlSummaryUrl(baseUrl: string): string {
  // Robot API base URL 只进入本机 Node proxy，浏览器永远不直接跨域访问上位机。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  const query = params.toString();
  return query ? `${API_ENDPOINTS.robotControlSummary}?${query}` : API_ENDPOINTS.robotControlSummary;
}

function robotControlProofRefreshUrl(endpoint: string, baseUrl: string): string {
  // refresh 只允许固定 POST endpoint，浏览器只提供 baseUrl，不能拼接任意路径。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  const query = params.toString();
  return query ? `${endpoint}?${query}` : endpoint;
}

function robotControlCameraOfferUrl(baseUrl: string): string {
  // camera offer 只允许把上位机 base URL 交给本机 Node 代理，浏览器不直连机器人。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  return `${API_ENDPOINTS.robotControlCameraOffer}?${params.toString()}`;
}

function robotControlCameraFirstFrameProbeUrl(baseUrl: string, includeBackendSmoke = false): string {
  // first-frame probe 只把 baseUrl 和诊断级别交给 Node 代理，底层参数仍由后端白名单生成。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  if (includeBackendSmoke) {
    params.set("backendSmoke", "1");
  }
  return `${API_ENDPOINTS.robotControlCameraFirstFrameProbe}?${params.toString()}`;
}

export function robotControlCameraMjpegUrl(baseUrl: string): string {
  // MJPEG fallback 仍走本机 Node 代理，浏览器不直连上位机或 8088 camera service。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  return `${API_ENDPOINTS.robotControlCameraMjpeg}?${params.toString()}`;
}

function robotControlCameraMjpegStatusUrl(baseUrl: string): string {
  // status 只读本机共享 relay 表，不会创建 MJPEG client 或打开上位机相机。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  return `${API_ENDPOINTS.robotControlCameraMjpegStatus}?${params.toString()}`;
}

function robotControlBaseProxyUrl(endpoint: string, baseUrl: string): string {
  // 点动/停止都只接受 baseUrl，远端路径固定在 Node 代理侧，浏览器不能拼接任意 POST。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  const query = params.toString();
  return query ? `${endpoint}?${query}` : endpoint;
}

function robotControlMapLifecycleUrl(endpoint: string, baseUrl: string): string {
  // map lifecycle 也只把 baseUrl 交给 Node 代理；地图 action 路径由 client 常量固定。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  const query = params.toString();
  return query ? `${endpoint}?${query}` : endpoint;
}

function robotControlRadarLifecycleUrl(endpoint: string, baseUrl: string): string {
  // radar lifecycle 只传 baseUrl；start/stop 远端路径固定在 Node 后端。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  const query = params.toString();
  return query ? `${endpoint}?${query}` : endpoint;
}

function robotControlOperatorReportUrl(baseUrl: string): string {
  // operator report 提交只允许固定本机 Node 代理；上位机路径由 server 白名单写死。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  const query = params.toString();
  return query ? `${API_ENDPOINTS.robotControlOperatorReport}?${query}` : API_ENDPOINTS.robotControlOperatorReport;
}

function robotControlCameraCloseUrl(baseUrl: string, peerId: string): string {
  // peer cleanup 路径固定白名单；peer_id 由 encodeURIComponent 防止路径注入。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  return `${API_ENDPOINTS.robotControlCameraPeersPrefix}${encodeURIComponent(peerId)}/close?${params.toString()}`;
}

function consumerTaskListUrl(baseUrl: string): string {
  // consumer read 列表固定走 view=summary；这里只允许 operator 提供 loopback base URL。
  const params = new URLSearchParams();
  const trimmed = baseUrl.trim();
  if (trimmed) {
    params.set("baseUrl", trimmed);
  }
  return `${API_ENDPOINTS.o7ConsumerTaskList}?${params.toString()}`;
}

function consumerTaskDetailUrl(baseUrl: string, taskId: string, fieldEvidenceManifestJson = ""): string {
  // 本地 manifest 路径只交给 Node 后端读取；浏览器不直接访问文件，也不覆盖远端有效证据。
  const params = new URLSearchParams();
  const trimmedBaseUrl = baseUrl.trim();
  if (trimmedBaseUrl) {
    params.set("baseUrl", trimmedBaseUrl);
  }
  const trimmedManifestJson = fieldEvidenceManifestJson.trim();
  if (trimmedManifestJson) {
    params.set("fieldEvidenceManifestJson", trimmedManifestJson);
  }
  const trimmedTaskId = taskId.trim();
  return `${API_ENDPOINTS.o7ConsumerTaskDetailPrefix}${encodeURIComponent(trimmedTaskId)}?${params.toString()}`;
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

export async function getRobotControlSummary(baseUrl: string): Promise<RobotControlSummaryResponse> {
  // Robot Control V1 只读取 Node 代理后的 fail-closed 摘要，不接收前端任意 endpoint。
  return loadJson<RobotControlSummaryResponse>(robotControlSummaryUrl(baseUrl));
}

export async function postRobotControlBaseManual(
  baseUrl: string,
  body: RobotControlBaseCommandRequest,
): Promise<RobotControlBaseCommandProxyResponse> {
  // 非 stop 点动也只能走固定 Node 代理，避免页面直接拿到任意 Robot API POST 权限。
  return postJson<RobotControlBaseCommandProxyResponse>(robotControlBaseProxyUrl(API_ENDPOINTS.robotControlBaseManual, baseUrl), body);
}

export async function postRobotControlBaseFirstJog(
  baseUrl: string,
  body: RobotControlBaseCommandRequest,
): Promise<RobotControlBaseCommandProxyResponse> {
  // 首次试动只走 first-jog 固定代理；后端仍负责现场材料 gate 和固定 /api/base/manual 转发。
  return postJson<RobotControlBaseCommandProxyResponse>(robotControlBaseProxyUrl(API_ENDPOINTS.robotControlBaseFirstJog, baseUrl), body);
}

export async function postRobotControlBaseStop(baseUrl: string): Promise<RobotControlBaseCommandProxyResponse> {
  // stop 单独走固定 endpoint；即使成功也不能把 safe_to_control 变成 true。
  return postJson<RobotControlBaseCommandProxyResponse>(robotControlBaseProxyUrl(API_ENDPOINTS.robotControlBaseStop, baseUrl), {});
}

export async function postRobotControlBaseFeedbackSamples(
  baseUrl: string,
): Promise<RobotControlBaseFeedbackSamplesProxyResponse> {
  // 底盘反馈样本只走固定 T=130 只读采集代理，前端不能传方向、速度或串口参数。
  return postJson<RobotControlBaseFeedbackSamplesProxyResponse>(
    robotControlBaseProxyUrl(API_ENDPOINTS.robotControlBaseFeedbackSamples, baseUrl),
    {},
  );
}

export async function postRobotControlRadarScanProofRefresh(
  baseUrl: string,
): Promise<RobotControlProofRefreshProxyResponse> {
  // Radar refresh 只透过本机 Node 代理发给上位机，固定 body 由后端掌控。
  return postJson<RobotControlProofRefreshProxyResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlRadarScanProofRefresh, baseUrl),
    {},
  );
}

export async function getRobotControlRadarStatus(baseUrl: string): Promise<RobotControlRadarStatusResponse> {
  // 雷达状态是固定只读 GET，供地图 marker 和现场 smoke 复用，不触发雷达 start/stop。
  return loadJson<RobotControlRadarStatusResponse>(
    robotControlRadarLifecycleUrl(API_ENDPOINTS.robotControlRadarStatus, baseUrl),
  );
}

export async function postRobotControlRadarStart(baseUrl: string): Promise<RobotControlRadarLifecycleResponse> {
  // Radar start 是高级诊断固定入口；浏览器 body 为空，不能传上位机任意参数。
  return postJson<RobotControlRadarLifecycleResponse>(
    robotControlRadarLifecycleUrl(API_ENDPOINTS.robotControlRadarStart, baseUrl),
    {},
  );
}

export async function postRobotControlRadarStop(baseUrl: string): Promise<RobotControlRadarLifecycleResponse> {
  // Radar stop 是高级诊断固定入口；即使远端 dry-run，也不改变顶层控制安全字段。
  return postJson<RobotControlRadarLifecycleResponse>(
    robotControlRadarLifecycleUrl(API_ENDPOINTS.robotControlRadarStop, baseUrl),
    {},
  );
}

export async function postRobotControlOperatorReport(
  baseUrl: string,
  body: RobotControlOperatorReportRequest,
): Promise<RobotControlOperatorReportProxyResponse> {
  // 现场材料提交只能走固定 /api/operator/report；组件不能传 endpoint、method 或控制参数。
  return postJson<RobotControlOperatorReportProxyResponse>(robotControlOperatorReportUrl(baseUrl), body);
}

export async function postRobotControlMapProofRefresh(baseUrl: string): Promise<RobotControlProofRefreshProxyResponse> {
  // Map refresh 只透过本机 Node 代理发给上位机，固定 body 由后端掌控。
  return postJson<RobotControlProofRefreshProxyResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlMapProofRefresh, baseUrl),
    {},
  );
}

export async function postRobotControlNav2ProofRefresh(baseUrl: string): Promise<RobotControlProofRefreshProxyResponse> {
  // Nav2 refresh 只请求 no-motion 路径规划证明，前端不能传 goal、start/stop 或任意 body。
  return postJson<RobotControlProofRefreshProxyResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlNav2ProofRefresh, baseUrl),
    {},
  );
}

export async function postRobotControlNav2Start(baseUrl: string): Promise<RobotControlNav2LifecycleResponse> {
  // Nav2 start 只恢复上位机服务栈；真正路线执行必须另走 goal/execute 固定代理。
  return postJson<RobotControlNav2LifecycleResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlNav2Start, baseUrl),
    {},
  );
}

export async function postRobotControlNav2Stop(baseUrl: string): Promise<RobotControlNav2LifecycleResponse> {
  // Nav2 stop 只停止服务栈；它不是行程急停，急停仍走 base stop 兜底。
  return postJson<RobotControlNav2LifecycleResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlNav2Stop, baseUrl),
    {},
  );
}

export async function postRobotControlNav2GoalPreflight(
  baseUrl: string,
  body: RobotControlNavGoalPreflightRequest,
): Promise<RobotControlNavGoalPreflightResponse> {
  // 目标预检只传短白名单字段；真正的只读材料 gate 和禁止执行保证在 Node 后端完成。
  return postJson<RobotControlNavGoalPreflightResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlNav2GoalPreflight, baseUrl),
    body,
  );
}

export async function postRobotControlNav2GoalExecute(
  baseUrl: string,
  body: RobotControlNavGoalExecutionRequest,
): Promise<RobotControlNavGoalExecutionResponse> {
  // 目标执行只走固定 Node 代理；组件只能传短白名单目标和显式确认。
  return postJson<RobotControlNavGoalExecutionResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlNav2GoalExecute, baseUrl),
    body,
  );
}

export async function getRobotControlNav2GoalExecutionLatest(baseUrl: string): Promise<RobotControlNavGoalExecutionLatestResponse> {
  // latest 只读取最近 NavigateToPose artifact；不会再次执行 goal。
  return loadJson<RobotControlNavGoalExecutionLatestResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlNav2GoalExecutionLatest, baseUrl),
  );
}

export async function getRobotControlDeliveryLatest(baseUrl: string): Promise<RobotControlDeliveryLatestResponse> {
  // delivery latest 只读取 gate 最近结论和缺项；不会提交送达或 operator report。
  return loadJson<RobotControlDeliveryLatestResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlDeliveryLatest, baseUrl),
  );
}

export async function postRobotControlDeliveryGapCheck(baseUrl: string): Promise<RobotControlDeliveryGapCheckResponse> {
  // 缺口复算固定 confirm=false，只刷新当前 Nav2/operator report 缺项，不可能确认送达。
  return postJson<RobotControlDeliveryGapCheckResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlDeliveryCheck, baseUrl),
    {},
  );
}

export async function postRobotControlDeliveryComplete(
  baseUrl: string,
  body: RobotControlDeliveryCompleteRequest,
): Promise<RobotControlDeliveryCompleteResponse> {
  // 交付完成只走固定 gate；后端只合成 Nav2 latest 与 operator report latest，不发送运动命令。
  return postJson<RobotControlDeliveryCompleteResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlDeliveryComplete, baseUrl),
    body,
  );
}

export async function postRobotControlLocalizeReset(baseUrl: string): Promise<RobotControlProofRefreshProxyResponse> {
  // 定位重置只走固定 Node 代理；initialpose 和 timeout body 由后端写死，浏览器不能覆盖。
  return postJson<RobotControlProofRefreshProxyResponse>(
    robotControlProofRefreshUrl(API_ENDPOINTS.robotControlLocalizeReset, baseUrl),
    {},
  );
}

export async function getRobotControlMapList(baseUrl: string): Promise<RobotControlMapLifecycleResponse> {
  // Map list 是固定 GET 代理，不允许组件拼接 /api/map/list 或直接跨域访问上位机。
  return loadJson<RobotControlMapLifecycleResponse>(robotControlMapLifecycleUrl(API_ENDPOINTS.robotControlMapList, baseUrl));
}

export async function getRobotControlMapPreview(baseUrl: string): Promise<RobotControlMapPreviewResponse> {
  // Map preview 是固定只读代理，只拿上位机 YAML/PGM 转出的 PNG data URL，不启动建图或导航。
  return loadJson<RobotControlMapPreviewResponse>(robotControlMapLifecycleUrl(API_ENDPOINTS.robotControlMapPreview, baseUrl));
}

export async function postRobotControlMapStart(
  baseUrl: string,
  body: RobotControlMapLifecycleRequest = {},
): Promise<RobotControlMapLifecycleResponse> {
  // Start endpoint 存在但 UI 默认不开放；body 仍只允许 map_name/artifact_path。
  return postJson<RobotControlMapLifecycleResponse>(robotControlMapLifecycleUrl(API_ENDPOINTS.robotControlMapStart, baseUrl), body);
}

export async function postRobotControlMapSave(
  baseUrl: string,
  body: RobotControlMapLifecycleRequest = {},
): Promise<RobotControlMapLifecycleResponse> {
  // Save 通过固定代理触发上位机软件 guard 或配置命令，不透传任意字段。
  return postJson<RobotControlMapLifecycleResponse>(robotControlMapLifecycleUrl(API_ENDPOINTS.robotControlMapSave, baseUrl), body);
}

export async function postRobotControlMapReset(
  baseUrl: string,
  body: RobotControlMapLifecycleRequest = {},
): Promise<RobotControlMapLifecycleResponse> {
  // Reset 只保留高级诊断入口，默认不会在普通用户首屏变成可误点动作。
  return postJson<RobotControlMapLifecycleResponse>(robotControlMapLifecycleUrl(API_ENDPOINTS.robotControlMapReset, baseUrl), body);
}

export async function postRobotControlFreeRoamAutonomyStart(
  baseUrl: string,
  body: RobotControlFreeRoamAutonomyRequest,
): Promise<RobotControlFreeRoamAutonomyResponse> {
  // 自动扫图 start 只走固定 PC 代理；body 只允许安全确认布尔值。
  return postJson<RobotControlFreeRoamAutonomyResponse>(
    robotControlMapLifecycleUrl(API_ENDPOINTS.robotControlFreeRoamAutonomyStart, baseUrl),
    body,
  );
}

export async function getRobotControlFreeRoamAutonomyLatest(baseUrl: string): Promise<RobotControlFreeRoamAutonomyLatestResponse> {
  // 自动扫图 latest 只读取上车端 runtime artifact，不启动或停止自动扫图。
  return loadJson<RobotControlFreeRoamAutonomyLatestResponse>(
    robotControlMapLifecycleUrl(API_ENDPOINTS.robotControlFreeRoamAutonomyLatest, baseUrl),
  );
}

export async function postRobotControlFreeRoamAutonomyStop(baseUrl: string): Promise<RobotControlFreeRoamAutonomyResponse> {
  // stop 固定转发上车状态机停止请求，不发布浏览器侧速度命令。
  return postJson<RobotControlFreeRoamAutonomyResponse>(
    robotControlMapLifecycleUrl(API_ENDPOINTS.robotControlFreeRoamAutonomyStop, baseUrl),
    {},
  );
}

export async function postRobotControlCameraOffer(
  baseUrl: string,
  offer: { type: "offer"; sdp: string },
): Promise<RobotControlCameraOfferProxyResponse> {
  // WebRTC offer 只透过本机 Node 代理发给上位机，避免浏览器跨域绕过 URL 围栏。
  return postJson<RobotControlCameraOfferProxyResponse>(robotControlCameraOfferUrl(baseUrl), offer);
}

export async function postRobotControlCameraPeerClose(
  baseUrl: string,
  peerId: string,
): Promise<RobotControlCameraCloseProxyResponse> {
  // cleanup 只允许关闭已知 peer_id，不允许把前端变成任意 Robot API POST 代理。
  return postJson<RobotControlCameraCloseProxyResponse>(robotControlCameraCloseUrl(baseUrl, peerId), {});
}

export async function postRobotControlCameraFirstFrameProbe(
  baseUrl: string,
  includeBackendSmoke = false,
): Promise<RobotControlCameraFirstFrameProbeProxyResponse> {
  // 相机首帧探针是高级诊断固定入口；前端 body 为空，不能传任意设备或 shell 参数。
  return postJson<RobotControlCameraFirstFrameProbeProxyResponse>(robotControlCameraFirstFrameProbeUrl(baseUrl, includeBackendSmoke), {});
}

export async function getRobotControlCameraMjpegStatus(baseUrl: string): Promise<RobotControlCameraMjpegStatusResponse> {
  // 共享预览状态只说明 PC relay 是否复用同一上游流，不代表画面内容已经可见。
  return loadJson<RobotControlCameraMjpegStatusResponse>(robotControlCameraMjpegStatusUrl(baseUrl));
}

export async function getO7ConsumerTaskList(baseUrl: string): Promise<O7ConsumerTaskListResponse> {
  // O7 任务列表主路径统一走 workstation 后端 adapter，浏览器不直连 relay。
  return loadJson<O7ConsumerTaskListResponse>(consumerTaskListUrl(baseUrl));
}

export async function getO7ConsumerTaskDetail(
  baseUrl: string,
  taskId: string,
  fieldEvidenceManifestJson = "",
): Promise<O7ConsumerTaskDetailResponse> {
  // 可选本地 manifest 只补齐缺失 field_evidence，不改变 detail 的轨迹/事件/标注等远端来源。
  return loadJson<O7ConsumerTaskDetailResponse>(consumerTaskDetailUrl(baseUrl, taskId, fieldEvidenceManifestJson));
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
