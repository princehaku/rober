<script setup lang="ts">
import { onMounted, ref } from "vue";
import EvidenceToolsPanel from "./components/EvidenceToolsPanel.vue";
import ProofBoundaryPanel from "./components/ProofBoundaryPanel.vue";
import ProofFlagStrip from "./components/ProofFlagStrip.vue";
import RouteDebugPanel from "./components/RouteDebugPanel.vue";
import TrainingLabelingPanel from "./components/TrainingLabelingPanel.vue";
import WorkstationTabs from "./components/WorkstationTabs.vue";
import type { WorkstationPanel } from "./components/WorkstationTabs.vue";
import { loadWorkstationSnapshot } from "./client/workstationApi";
import type { RouteDebugInputs } from "./client/workstationApi";
import type {
  EvidenceToolsResponse,
  HealthResponse,
  ProofBoundaryResponse,
  RouteDebugSummaryResponse,
  TrainingLabelingResponse,
} from "./shared/contracts";

// App 只组合全局状态和布局，不再承载各页面的展示细节。
// activePanel 是本地导航状态，不参与证明链路。
const activePanel = ref<WorkstationPanel>("route");
// loading 只说明 API 请求中，不说明任何旧 gate 正在执行。
const loading = ref(true);
// error 展示 API 不可用原因，并继续保持主动作关闭。
const error = ref("");

// UI 状态只承载 API 返回值；默认值保持空，不在前端伪造机器人事实。
const health = ref<HealthResponse | null>(null);
const routeSummary = ref<RouteDebugSummaryResponse | null>(null);
const evidenceTools = ref<EvidenceToolsResponse | null>(null);
const trainingLabeling = ref<TrainingLabelingResponse | null>(null);
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
    trainingLabeling.value = snapshot.trainingLabeling;
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
    <EvidenceToolsPanel v-else-if="activePanel === 'evidence'" :evidence-tools="evidenceTools" />
    <TrainingLabelingPanel v-else-if="activePanel === 'training'" :training-labeling="trainingLabeling" />
    <ProofBoundaryPanel v-else :proof-boundary="proofBoundary" />
  </main>
</template>
