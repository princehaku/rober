<script setup lang="ts">
import { onMounted, ref } from "vue";
import EvidenceToolsPanel from "./components/EvidenceToolsPanel.vue";
import O7FixturePreviewPanel from "./components/O7FixturePreviewPanel.vue";
import O7OperatorConsolePanel from "./components/O7OperatorConsolePanel.vue";
import ProofBoundaryPanel from "./components/ProofBoundaryPanel.vue";
import RobotControlConsolePanel from "./components/RobotControlConsolePanel.vue";
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
  O7OperatorConsoleResponse,
  ProofBoundaryResponse,
  RouteDebugSummaryResponse,
  TrainingLabelingResponse,
} from "./shared/contracts";

// App 只组合全局状态和布局，不再承载各页面的展示细节。
// activePanel 现在只用于默认关闭的高级工具，避免工程 tab 污染普通用户首屏。
const activePanel = ref<WorkstationPanel>("route");
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
const o7OperatorConsole = ref<O7OperatorConsoleResponse | null>(null);
const proofBoundary = ref<ProofBoundaryResponse | null>(null);
const routeInputs = ref<RouteDebugInputs>({
  // 输入框保存用户本机路径；这些值只拼到 query，不作为 safe summary 展示。
  statusJson: "",
  taskRecord: "",
  taskRecordDir: "",
  elevatorRouteReconciliation: "",
});

function isDirectMapViewRequested(): boolean {
  // 直达地图大屏只改变 PC 页面壳，不启动 RViz2、ROS2 runtime 或任何运动接口。
  const params = new URLSearchParams(window.location.search);
  const view = params.get("view") ?? params.get("mode");
  return view === "map" || view === "map-only" || window.location.hash === "#map";
}

const directMapViewRequested = isDirectMapViewRequested();

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
  <main
    class="shell"
    :data-direct-map-view-requested="String(directMapViewRequested)"
    data-direct-map-view-url="?view=map"
    data-direct-map-view-behavior="page_shell_map_only"
  >
    <header v-if="!directMapViewRequested" class="topbar">
      <div>
        <h1>Rober 小车控制台</h1>
        <p class="topbar-subtitle">连接小车、查看画面和地图，必要时一键停止。</p>
      </div>
      <button class="secondary" type="button" @click="refresh">刷新页面</button>
    </header>

    <div v-if="error" class="notice" role="alert">
      页面暂时没有读到本机服务：{{ error }}。
    </div>

    <div v-if="loading" class="notice" role="status">
      正在读取本机状态...
    </div>

    <RobotControlConsolePanel />

    <details v-if="!directMapViewRequested" class="advanced-tools-details">
      <summary>高级工具</summary>
      <div class="advanced-tools-body">
        <WorkstationTabs v-model="activePanel" />

        <RouteDebugPanel
          v-if="activePanel === 'route'"
          v-model:route-inputs="routeInputs"
          :route-summary="routeSummary"
          @refresh="refresh"
        />
        <O7OperatorConsolePanel v-if="activePanel === 'o7'" :operator-console="o7OperatorConsole" />
        <O7FixturePreviewPanel v-if="activePanel === 'o7Previews'" />
        <EvidenceToolsPanel v-if="activePanel === 'evidence'" :evidence-tools="evidenceTools" />
        <WaveRoverMaterialCoveragePanel v-if="activePanel === 'hardware'" :hardware-materials="hardwareMaterials" />
        <TrainingLabelingPanel v-if="activePanel === 'training'" :training-labeling="trainingLabeling" />
        <ProofBoundaryPanel v-if="activePanel === 'boundary'" :health="health" :proof-boundary="proofBoundary" />
      </div>
    </details>
  </main>
</template>
