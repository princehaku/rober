<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type {
  EvidenceToolsResponse,
  HealthResponse,
  ProofBoundaryResponse,
  RouteDebugSummaryResponse,
  TrainingLabelingResponse,
} from "./shared/contracts";
import { PROOF_FLAGS } from "./shared/contracts";

type Panel = "route" | "evidence" | "training" | "boundary";

// 组件层只处理交互状态，不拥有机器人事实。
// activePanel 是本地导航状态，不参与证明链路。
const activePanel = ref<Panel>("route");
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
const routeInputs = ref({
  // 输入框保存用户本机路径；这些值只拼到 query，不作为 safe summary 展示。
  statusJson: "",
  taskRecord: "",
  taskRecordDir: "",
  elevatorRouteReconciliation: "",
});

const panels: Array<{ id: Panel; label: string }> = [
  // 四个入口对应本轮 PRD，第一阶段不增加控制台式主动作。
  // Route Debug 只显示旧 gate 映射，不读取现场 route JSON。
  // Evidence Tools 只显示索引，不执行 evidence Python。
  // Training/Labeling 只显示占位，不接真实流水线。
  // Proof Boundary 解释不可证明项，不生成新状态。
  { id: "route", label: "Route Debug" },
  { id: "evidence", label: "Evidence Tools" },
  { id: "training", label: "Training/Labeling" },
  { id: "boundary", label: "Proof Boundary" },
];

async function loadJson<T>(url: string): Promise<T> {
  // 所有数据都走 API，UI 不在前端拼接机器人状态或成功结论。
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return (await response.json()) as T;
}

function routeDebugUrl(): string {
  // 空字段不进入 query，让后端明确返回 not_provided，而不是读取空路径。
  const params = new URLSearchParams();
  Object.entries(routeInputs.value).forEach(([key, value]) => {
    const trimmed = value.trim();
    if (trimmed) {
      params.set(key, trimmed);
    }
  });
  const query = params.toString();
  return query ? `/api/route/debug-summary?${query}` : "/api/route/debug-summary";
}

async function refresh(): Promise<void> {
  // 刷新同时拉取全部只读 API，避免分页面状态互相漂移。
  loading.value = true;
  error.value = "";
  try {
    [health.value, routeSummary.value, evidenceTools.value, trainingLabeling.value, proofBoundary.value] =
      await Promise.all([
        loadJson<HealthResponse>("/api/health"),
        loadJson<RouteDebugSummaryResponse>(routeDebugUrl()),
        loadJson<EvidenceToolsResponse>("/api/tools/evidence"),
        loadJson<TrainingLabelingResponse>("/api/tools/training-labeling"),
        loadJson<ProofBoundaryResponse>("/api/proof-boundary"),
      ]);
  } catch (err) {
    // API 不可用时保持 fail-closed；不显示任何成功或可控制状态。
    error.value = err instanceof Error ? err.message : "api_unavailable_not_proven";
  } finally {
    loading.value = false;
  }
}

const categoryRows = computed(() =>
  // Evidence 分类来自 API 只读索引，前端只负责稳定排序和展示。
  Object.entries(evidenceTools.value?.categories ?? {}).sort(([left], [right]) => left.localeCompare(right)),
);

function formatSummaryValue(value: unknown): string {
  // UI 只格式化后端 safe summary；不在前端补机器人状态或成功结论。
  if (value === null || value === undefined) {
    return "null";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
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

    <section class="status-strip" aria-label="proof flags">
      <span>source={{ health?.source ?? PROOF_FLAGS.source }}</span>
      <span>proof_status={{ health?.proof_status ?? PROOF_FLAGS.proof_status }}</span>
      <span>safe_to_control=false</span>
      <span>delivery_success=false</span>
      <span>pc_only=true</span>
    </section>

    <div v-if="error" class="notice" role="alert">
      API unavailable: {{ error }}. primary_actions_enabled=false.
    </div>

    <nav class="tabs" aria-label="workstation sections">
      <button
        v-for="panel in panels"
        :key="panel.id"
        :class="{ active: activePanel === panel.id }"
        type="button"
        @click="activePanel = panel.id"
      >
        {{ panel.label }}
      </button>
    </nav>

    <section v-if="loading" class="workspace">
      <h2>Loading local software proof index</h2>
      <p>primary_actions_enabled=false</p>
    </section>

    <section v-else-if="activePanel === 'route'" class="workspace">
      <div class="section-head">
        <h2>Route Debug</h2>
        <span class="pill">read-only</span>
      </div>
      <form class="route-inputs" @submit.prevent="refresh">
        <label>
          <span>statusJson</span>
          <input v-model="routeInputs.statusJson" type="text" autocomplete="off" spellcheck="false">
        </label>
        <label>
          <span>taskRecord</span>
          <input v-model="routeInputs.taskRecord" type="text" autocomplete="off" spellcheck="false">
        </label>
        <label>
          <span>taskRecordDir</span>
          <input v-model="routeInputs.taskRecordDir" type="text" autocomplete="off" spellcheck="false">
        </label>
        <label>
          <span>elevatorRouteReconciliation</span>
          <input v-model="routeInputs.elevatorRouteReconciliation" type="text" autocomplete="off" spellcheck="false">
        </label>
        <button class="secondary" type="submit">Refresh Route Summary</button>
      </form>
      <dl class="kv">
        <dt>route_root</dt>
        <dd>{{ routeSummary?.route_root }}</dd>
        <dt>legacy_schema</dt>
        <dd>{{ routeSummary?.route_console_summary.schema }}</dd>
        <dt>evidence_boundary</dt>
        <dd>{{ routeSummary?.route_console_summary.evidence_boundary }}</dd>
        <dt>console_controls</dt>
        <dd>{{ routeSummary?.route_console_summary.console_controls }}</dd>
        <dt>loader_name</dt>
        <dd>{{ routeSummary?.node_route_json_loader.name }}</dd>
        <dt>implementation</dt>
        <dd>{{ routeSummary?.node_route_json_loader.implementation }}</dd>
        <dt>accepts_local_json</dt>
        <dd>{{ routeSummary?.node_route_json_loader.accepts_local_json }}</dd>
        <dt>executes_control</dt>
        <dd>false</dd>
        <dt>statusJson</dt>
        <dd>{{ routeSummary?.input_status.statusJson }}</dd>
        <dt>taskRecord</dt>
        <dd>{{ routeSummary?.input_status.taskRecord }}</dd>
        <dt>taskRecordDir</dt>
        <dd>{{ routeSummary?.input_status.taskRecordDir }}</dd>
        <dt>elevatorRouteReconciliation</dt>
        <dd>{{ routeSummary?.input_status.elevatorRouteReconciliation }}</dd>
      </dl>
      <h3>Node loader safe summary</h3>
      <ul class="dense">
        <li>route_progress={{ formatSummaryValue(routeSummary?.route_console_summary.route_progress) }}</li>
        <li>keyframe_preflight={{ formatSummaryValue(routeSummary?.route_console_summary.keyframe_preflight) }}</li>
        <li>match_status={{ routeSummary?.route_console_summary.match_status }}</li>
        <li>failure={{ routeSummary?.route_console_summary.failure.status }}</li>
        <li>recent_task={{ formatSummaryValue(routeSummary?.route_console_summary.recent_task) }}</li>
        <li>route_elevator_reconciliation={{ routeSummary?.route_console_summary.route_elevator_reconciliation.lookup_status }}</li>
      </ul>
      <h3>Missing or blocked reason</h3>
      <ul class="dense">
        <li v-for="item in routeSummary?.blocked_reasons" :key="item">{{ item }}</li>
        <li v-if="!routeSummary?.blocked_reasons.length">none</li>
      </ul>
      <h3>Fail-closed conditions</h3>
      <ul class="dense">
        <li v-for="item in routeSummary?.route_console_summary.failure.fail_closed_conditions" :key="item">{{ item }}</li>
      </ul>
      <h3>Missing or external fields</h3>
      <ul class="dense">
        <li v-for="item in routeSummary?.missing_fields" :key="item">{{ item }}</li>
      </ul>
    </section>

    <section v-else-if="activePanel === 'evidence'" class="workspace">
      <div class="section-head">
        <h2>Evidence Tools</h2>
        <span class="pill">{{ evidenceTools?.total_json_fixtures ?? 0 }} fixtures</span>
      </div>
      <div class="metrics">
        <div v-for="[category, count] in categoryRows" :key="category">
          <strong>{{ count }}</strong>
          <span>{{ category }}</span>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Group</th>
            <th>Category</th>
            <th>Fixtures</th>
            <th>Summary</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="asset in evidenceTools?.assets" :key="asset.group">
            <td>{{ asset.group }}</td>
            <td>{{ asset.category }}</td>
            <td>{{ asset.fixture_count }}</td>
            <td>{{ asset.summary }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section v-else-if="activePanel === 'training'" class="workspace">
      <div class="section-head">
        <h2>Training/Labeling</h2>
        <span class="pill">placeholder_not_connected</span>
      </div>
      <div class="two-col">
        <article v-for="entry in trainingLabeling?.entries" :key="entry.path">
          <h3>{{ entry.name }}</h3>
          <p>{{ entry.path }}</p>
          <p>real_pipeline_connected=false</p>
        </article>
      </div>
    </section>

    <section v-else class="workspace">
      <div class="section-head">
        <h2>Proof Boundary</h2>
        <span class="pill danger">not_proven</span>
      </div>
      <div class="two-col">
        <article>
          <h3>Can prove</h3>
          <ul class="dense">
            <li v-for="item in proofBoundary?.can_prove" :key="item">{{ item }}</li>
          </ul>
        </article>
        <article>
          <h3>Not proven</h3>
          <ul class="dense">
            <li v-for="item in proofBoundary?.not_proven" :key="item">{{ item }}</li>
          </ul>
        </article>
      </div>
      <dl class="kv">
        <dt>workstation_executes_control</dt>
        <dd>false</dd>
        <dt>route_loader_mode</dt>
        <dd>{{ proofBoundary?.control_policy.route_loader_mode }}</dd>
        <dt>recovery_path</dt>
        <dd>{{ proofBoundary?.control_policy.recovery_path }}</dd>
      </dl>
    </section>
  </main>
</template>
