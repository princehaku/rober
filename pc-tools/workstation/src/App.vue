<script setup lang="ts">
import { onMounted, ref } from "vue";
import EvidenceToolsPanel from "./components/EvidenceToolsPanel.vue";
import O7FixturePreviewPanel from "./components/O7FixturePreviewPanel.vue";
import O7LiveOperatorPanel from "./components/O7LiveOperatorPanel.vue";
import O7OperatorConsolePanel from "./components/O7OperatorConsolePanel.vue";
import ProofBoundaryPanel from "./components/ProofBoundaryPanel.vue";
import ProofFlagStrip from "./components/ProofFlagStrip.vue";
import RealMaterialAcceptancePanel from "./components/RealMaterialAcceptancePanel.vue";
import RouteDebugPanel from "./components/RouteDebugPanel.vue";
import TrainingLabelingPanel from "./components/TrainingLabelingPanel.vue";
import WaveRoverMaterialCoveragePanel from "./components/WaveRoverMaterialCoveragePanel.vue";
import WorkstationTabs from "./components/WorkstationTabs.vue";
import type { WorkstationPanel } from "./components/WorkstationTabs.vue";
import { loadWorkstationSnapshot } from "./client/workstationApi";
import type { RouteDebugInputs } from "./client/workstationApi";
import type {
  EvidenceToolsResponse,
  HardwareMaterialsResponse,
  HealthResponse,
  O5O6ExternalProbeArtifactResponse,
  O7LiveOperatorPanelResponse,
  O7OperatorConsoleResponse,
  ProofBoundaryResponse,
  RealMaterialAcceptanceResponse,
  RouteDebugSummaryResponse,
  TrainingLabelingResponse,
} from "./shared/contracts";

// App 只组合全局状态和布局，不再承载各页面的展示细节。
// O7 是当前最低优先级目标，本轮默认首屏直接进入运营调试 console。
const activePanel = ref<WorkstationPanel>("o7");
// loading 只说明 API 请求中，不说明任何旧 gate 正在执行。
const loading = ref(true);
// error 展示 API 不可用原因，并继续保持主动作关闭。
const error = ref("");

// UI 状态只承载 API 返回值；默认值保持空，不在前端伪造机器人事实。
const health = ref<HealthResponse | null>(null);
const routeSummary = ref<RouteDebugSummaryResponse | null>(null);
const evidenceTools = ref<EvidenceToolsResponse | null>(null);
const hardwareMaterials = ref<HardwareMaterialsResponse | null>(null);
const trainingLabeling = ref<TrainingLabelingResponse | null>(null);
const o5O6ExternalProbeArtifact = ref<O5O6ExternalProbeArtifactResponse | null>(null);
const realMaterialAcceptance = ref<RealMaterialAcceptanceResponse | null>(null);
const o7LiveOperatorPanel = ref<O7LiveOperatorPanelResponse | null>(null);
const o7OperatorConsole = ref<O7OperatorConsoleResponse | null>(null);
const proofBoundary = ref<ProofBoundaryResponse | null>(null);
const routeInputs = ref<RouteDebugInputs>({
  // 输入框保存用户本机路径；这些值只拼到 query，不作为 safe summary 展示。
  statusJson: "",
  taskRecord: "",
  taskRecordDir: "",
  elevatorRouteReconciliation: "",
});

async function refresh(): Promise<void> {
  // 数据加载统一走 client，App 不直接拼 fetch URL。
  loading.value = true;
  error.value = "";
  try {
    const snapshot = await loadWorkstationSnapshot(routeInputs.value);
    health.value = snapshot.health;
    routeSummary.value = snapshot.routeSummary;
    evidenceTools.value = snapshot.evidenceTools;
    hardwareMaterials.value = snapshot.hardwareMaterials;
    trainingLabeling.value = snapshot.trainingLabeling;
    o5O6ExternalProbeArtifact.value = snapshot.o5O6ExternalProbeArtifact;
    realMaterialAcceptance.value = snapshot.realMaterialAcceptance;
    o7LiveOperatorPanel.value = snapshot.o7LiveOperatorPanel;
    o7OperatorConsole.value = snapshot.o7OperatorConsole;
    proofBoundary.value = snapshot.proofBoundary;
  } catch (err) {
    // API 不可用时保持 fail-closed；不显示任何成功或可控制状态。
    error.value = err instanceof Error ? err.message : "api_unavailable_not_proven";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  // 页面加载即拉取 API，让错误状态也能落到 fail-closed 提示。
  void refresh();
});
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">pc-tools/workstation</p>
        <h1>Rober PC Tools Workstation</h1>
      </div>
      <button class="secondary" type="button" @click="refresh">Refresh</button>
    </header>

    <ProofFlagStrip :health="health" />

    <div v-if="error" class="notice" role="alert">
      API unavailable: {{ error }}. primary_actions_enabled=false.
    </div>

    <WorkstationTabs v-model="activePanel" />

    <section v-if="loading" class="workspace">
      <h2>Loading local software proof index</h2>
      <p>primary_actions_enabled=false</p>
    </section>

    <RouteDebugPanel
      v-else-if="activePanel === 'route'"
      v-model:route-inputs="routeInputs"
      :route-summary="routeSummary"
      @refresh="refresh"
    />
    <template v-else-if="activePanel === 'o7'">
      <O7LiveOperatorPanel :live-operator-panel="o7LiveOperatorPanel" />
      <RealMaterialAcceptancePanel :real-material-acceptance="realMaterialAcceptance" />
      <section class="probe-artifact-panel" aria-label="O5 O6 external probe artifact">
        <div class="section-head compact-head">
          <div>
            <!-- 该卡片只显示后端脱敏摘要，不展示 artifact path、raw URL 或 token。 -->
            <p class="eyebrow">O5/O6 external live probe · latest artifact</p>
            <h2>External Probe Artifact</h2>
          </div>
          <span class="pill danger">{{ o5O6ExternalProbeArtifact?.probe_status ?? "not_loaded" }}</span>
        </div>
        <dl class="kv compact-kv">
          <!-- updated_at 来自 artifact executed_at 或文件 mtime 脱敏值，便于运维判断是否 stale。 -->
          <dt>artifact</dt>
          <dd>
            {{ o5O6ExternalProbeArtifact?.artifact_status ?? "missing" }}
            · source={{ o5O6ExternalProbeArtifact?.artifact_source ?? "workstation_runtime" }}
            · updated={{ o5O6ExternalProbeArtifact?.updated_at ?? "null" }}
          </dd>
          <dt>runner</dt>
          <dd>{{ o5O6ExternalProbeArtifact?.runner ?? "not_loaded" }} · {{ o5O6ExternalProbeArtifact?.viewpoint ?? "not_loaded" }}</dd>
          <dt>reachability</dt>
          <dd>
            reachable={{ o5O6ExternalProbeArtifact?.summary.reachable_count ?? 0 }}/{{
              o5O6ExternalProbeArtifact?.summary.endpoint_count ?? 0
            }}
            · schema={{ o5O6ExternalProbeArtifact?.summary.schema_matched_count ?? 0 }}
            · fail_closed={{ o5O6ExternalProbeArtifact?.summary.fail_closed_count ?? 0 }}
          </dd>
          <dt>safety</dt>
          <dd>
            no_post={{ o5O6ExternalProbeArtifact?.safety_policy.no_post ?? true }}
            · no_robot_control={{ o5O6ExternalProbeArtifact?.safety_policy.no_robot_control ?? true }}
            · no_hardware_read={{ o5O6ExternalProbeArtifact?.safety_policy.no_hardware_read ?? true }}
          </dd>
          <dt>redaction</dt>
          <dd>
            credentials_redacted={{ o5O6ExternalProbeArtifact?.credentials_redacted ?? true }}
            · token_exposed={{ o5O6ExternalProbeArtifact?.token_exposed ?? false }}
            · raw_url_exposed={{ o5O6ExternalProbeArtifact?.raw_url_exposed ?? false }}
            · artifact_path_exposed={{ o5O6ExternalProbeArtifact?.artifact_path_exposed ?? false }}
          </dd>
        </dl>

        <div class="probe-endpoint-grid">
          <article
            v-for="endpoint in o5O6ExternalProbeArtifact?.endpoints ?? []"
            :key="endpoint.name"
            class="probe-endpoint-card"
          >
            <!-- endpoint 名和固定路径来自 probe allowlist；不会显示 raw base URL。 -->
            <strong>{{ endpoint.name }}</strong>
            <span>{{ endpoint.endpoint }}</span>
            <span>reachable={{ endpoint.reachable }} · http={{ endpoint.http_status ?? "null" }}</span>
            <span>{{ endpoint.contract_status }} · {{ endpoint.failure_category }}</span>
            <span v-if="endpoint.blocked_reasons.length">
              blocked={{ endpoint.blocked_reasons.join(", ") }}
            </span>
          </article>
        </div>

        <ul class="dense">
          <!-- blocked reasons 是 probe 的产品化恢复提示，已由后端截断和脱敏。 -->
          <li v-for="reason in o5O6ExternalProbeArtifact?.blocked_reasons ?? []" :key="reason">
            {{ reason }}
          </li>
        </ul>
      </section>
      <O7OperatorConsolePanel :operator-console="o7OperatorConsole" />
    </template>
    <O7FixturePreviewPanel v-else-if="activePanel === 'o7Previews'" />
    <EvidenceToolsPanel v-else-if="activePanel === 'evidence'" :evidence-tools="evidenceTools" />
    <WaveRoverMaterialCoveragePanel
      v-else-if="activePanel === 'hardware'"
      :hardware-materials="hardwareMaterials"
    />
    <TrainingLabelingPanel v-else-if="activePanel === 'training'" :training-labeling="trainingLabeling" />
    <ProofBoundaryPanel v-else :proof-boundary="proofBoundary" />
  </main>
</template>
