<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getO7ConsumerTaskDetail, getRobotControlSummary } from "../client/workstationApi";
import type { O7ConsumerTaskDetailResponse, RobotControlSummaryResponse } from "../shared/contracts";

// 本组件是 PC 控制台入口，但 V1 只读状态和证据，不发送任何机器人命令。
const robotApiBaseUrl = ref("");
const o6ConsumerBaseUrl = ref("http://127.0.0.1:8088");
const taskId = ref("");
const fieldEvidenceManifestJson = ref("");
const loading = ref(false);
const error = ref("");
const robotSummary = ref<RobotControlSummaryResponse | null>(null);
const taskDetail = ref<O7ConsumerTaskDetailResponse | null>(null);

const proofRows = computed(() => {
  // O3 proof 字段固定列出，缺字段也要显示 unknown，不能把缺失当作通过。
  const proof = robotSummary.value?.o3_proof_summary;
  return [
    ["managed_runtime_started", proof?.managed_runtime_started],
    ["scan_once_observed", proof?.scan_once_observed],
    ["map_once_observed", proof?.map_once_observed],
    ["amcl_pose_observed", proof?.amcl_pose_observed],
    ["localization_tf_observed", proof?.localization_tf_observed],
    ["planner_server_active", proof?.planner_server_active],
    ["path_generation_requested", proof?.path_generation_requested],
    ["path_generation_succeeded", proof?.path_generation_succeeded],
    ["path_generated", proof?.path_generated],
    ["path_point_count", proof?.path_point_count],
  ];
});

const selectedTaskSummary = computed(() => {
  // task_id 是回放和 evidence 的主键；没有 task_id 时保持 blocked 空状态。
  if (!taskId.value.trim()) {
    return "task_id not selected; route replay/mock fallback summary blocked";
  }
  if (!taskDetail.value) {
    return "task detail not loaded; use Refresh control console";
  }
  return `${taskDetail.value.requested_task_id} / ${taskDetail.value.detail_status}`;
});

const routeReplaySource = computed(() => {
  // 本地 manifest 只能补 field_evidence，不覆盖 O6 trajectory/events 主路径。
  if (!taskDetail.value) {
    return "blocked_not_loaded";
  }
  const fieldSource = taskDetail.value.field_evidence.source_contract;
  return fieldSource === "not_loaded" ? "o6_consumer_detail_missing_or_blocked" : `${fieldSource} + O6 consumer detail`;
});

function display(value: unknown): string {
  // 展示层统一把 null/undefined 压成 unknown，避免模板里散落 fallback 逻辑。
  if (value === null || value === undefined) {
    return "unknown";
  }
  return String(value);
}

function listText(items: string[] | undefined, fallback = "none"): string {
  // blocked/not_proven 只展示少量摘要，完整定位应回到后端日志或 artifact。
  return items && items.length ? items.slice(0, 6).join("; ") : fallback;
}

function sampleText(items: Record<string, unknown>[] | undefined): string {
  // 只读样本压缩成短 JSON，页面不承担完整数据浏览器职责。
  if (!items || items.length === 0) {
    return "none";
  }
  return items
    .slice(0, 2)
    .map((item) => JSON.stringify(item).slice(0, 160))
    .join(" | ");
}

async function refreshConsole(): Promise<void> {
  // 刷新永远先读 Node proxy；只有 task_id 存在才读 O6 detail。
  loading.value = true;
  error.value = "";
  try {
    const [summary, detail] = await Promise.all([
      getRobotControlSummary(robotApiBaseUrl.value),
      taskId.value.trim()
        ? getO7ConsumerTaskDetail(o6ConsumerBaseUrl.value, taskId.value, fieldEvidenceManifestJson.value)
        : Promise.resolve(null),
    ]);
    robotSummary.value = summary;
    taskDetail.value = detail;
  } catch (err) {
    // 前端异常仍保持所有主动作关闭，具体 Robot API 失败应优先看 summary.blocked_reasons。
    error.value = err instanceof Error ? err.message : "robot_control_console_refresh_failed";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  // 初次加载只拿到 baseUrl_not_provided 的 blocked 摘要，不会探测真实机器人。
  void refreshConsole();
});
</script>

<template>
  <section class="workspace robot-console">
    <div class="section-head">
      <div>
        <p class="eyebrow">O7 Robot Control Console V1</p>
        <h2>Robot Control</h2>
      </div>
      <span class="pill danger">primary_actions_enabled=false</span>
    </div>

    <form class="robot-control-form" @submit.prevent="refreshConsole">
      <label>
        <span>task_id selector</span>
        <input v-model="taskId" name="task_id" placeholder="task_id">
      </label>
      <label>
        <span>Robot API base URL</span>
        <input v-model="robotApiBaseUrl" name="robotApiBaseUrl" placeholder="http://192.168.x.x:8787">
      </label>
      <label>
        <span>O6 consumer base URL</span>
        <input v-model="o6ConsumerBaseUrl" name="o6ConsumerBaseUrl" placeholder="http://127.0.0.1:8088">
      </label>
      <label>
        <span>Mock/field manifest JSON</span>
        <input v-model="fieldEvidenceManifestJson" name="fieldEvidenceManifestJson" placeholder="optional local JSON">
      </label>
      <button class="secondary" type="submit" :disabled="loading">Refresh control console</button>
    </form>

    <div v-if="error" class="notice" role="alert">
      {{ error }}; safe_to_control=false; delivery_success=false; primary_actions_enabled=false.
    </div>

    <div class="robot-console-grid">
      <article class="snapshot-panel">
        <h3>task_id selector</h3>
        <dl class="kv compact-kv">
          <dt>selected</dt>
          <dd>{{ selectedTaskSummary }}</dd>
          <dt>source</dt>
          <dd>{{ routeReplaySource }}</dd>
          <dt>task status</dt>
          <dd>{{ taskDetail?.task_summary?.task_status_summary ?? "blocked_not_loaded" }}</dd>
          <dt>safe_to_control</dt>
          <dd>false</dd>
          <dt>delivery_success</dt>
          <dd>false</dd>
        </dl>
      </article>

      <article class="snapshot-panel">
        <h3>Robot API connection</h3>
        <dl class="kv compact-kv">
          <dt>proxy</dt>
          <dd>Node server only; Vue direct access=false</dd>
          <dt>base URL</dt>
          <dd>{{ robotSummary?.normalized_base_url ?? "not_loaded" }}</dd>
          <dt>状态</dt>
          <dd>{{ robotSummary?.robot_api_connection.status ?? "not_loaded" }}</dd>
          <dt>read count</dt>
          <dd>
            loaded={{ robotSummary?.robot_api_connection.loaded_count ?? 0 }},
            failed={{ robotSummary?.robot_api_connection.failed_count ?? 0 }},
            blocked={{ robotSummary?.robot_api_connection.blocked_count ?? 0 }}
          </dd>
          <dt>blocked reason</dt>
          <dd>{{ listText(robotSummary?.robot_api_connection.blocked_reasons, "none") }}</dd>
        </dl>
      </article>

      <article class="snapshot-panel">
        <h3>O3 proof summary</h3>
        <table>
          <tbody>
            <tr v-for="[key, value] in proofRows" :key="key">
              <th>{{ key }}</th>
              <td>{{ display(value) }}</td>
            </tr>
          </tbody>
        </table>
        <p class="muted">root_causes: {{ listText(robotSummary?.o3_proof_summary.root_causes) }}</p>
        <p class="muted">not_proven: {{ listText(robotSummary?.o3_proof_summary.not_proven) }}</p>
      </article>

      <article class="snapshot-panel">
        <h3>route replay / Mock fallback</h3>
        <dl class="kv compact-kv">
          <dt>source</dt>
          <dd>{{ routeReplaySource }}</dd>
          <dt>trajectory</dt>
          <dd>{{ taskDetail?.trajectory.status ?? "blocked_not_loaded" }} / frames={{ taskDetail?.trajectory.frame_count ?? 0 }}</dd>
          <dt>events</dt>
          <dd>{{ taskDetail?.events.status ?? "blocked_not_loaded" }} / count={{ taskDetail?.events.count ?? 0 }}</dd>
          <dt>tunnel</dt>
          <dd>{{ taskDetail?.tunnel_status.latest_known_status ?? "blocked_not_loaded" }}</dd>
          <dt>Mock</dt>
          <dd>{{ fieldEvidenceManifestJson ? "local_mock_or_field_manifest_visible" : "Mock fallback not selected" }}</dd>
        </dl>
      </article>

      <article class="snapshot-panel">
        <h3>evidence / keyframe / labeling readiness</h3>
        <dl class="kv compact-kv">
          <dt>field evidence</dt>
          <dd>{{ taskDetail?.field_evidence.artifact_status ?? "blocked_not_loaded" }}</dd>
          <dt>manifest gate</dt>
          <dd>{{ taskDetail?.field_evidence.manifest_gate.status ?? "blocked_not_loaded" }}</dd>
          <dt>evidence</dt>
          <dd>{{ taskDetail?.evidence.status ?? "blocked_not_loaded" }} / count={{ taskDetail?.evidence.count ?? 0 }}</dd>
          <dt>labeling</dt>
          <dd>{{ taskDetail?.labeling.status ?? "blocked_not_loaded" }} / labels={{ taskDetail?.labeling.label_count ?? 0 }}</dd>
          <dt>keyframe/sample</dt>
          <dd>{{ sampleText(taskDetail?.evidence.sample_evidence) }}</dd>
        </dl>
      </article>

      <article class="snapshot-panel">
        <h3>manual / nav safe command boundary</h3>
        <p class="muted">{{ robotSummary?.safe_command_boundary.locked_reason ?? "locked by V1 boundary" }}</p>
        <div class="locked-actions" aria-label="locked robot actions">
          <button disabled type="button">/api/base/manual locked</button>
          <button disabled type="button">cmd_vel locked</button>
          <button disabled type="button">Nav2 goal locked</button>
          <button disabled type="button">map start locked</button>
          <button disabled type="button">radar start locked</button>
          <button disabled type="button">keyboard control locked</button>
          <button disabled type="button">map click goal locked</button>
        </div>
        <p class="muted">
          command_dispatch_enabled=false; manual_control_enabled=false; navigate_goal_enabled=false;
          keyboard_control_enabled=false; robot_control_executed=false.
        </p>
      </article>

      <article class="snapshot-panel">
        <h3>Camera / LiDAR / Base readback</h3>
        <dl class="kv compact-kv">
          <dt>Camera</dt>
          <dd>
            /api/camera/health={{ robotSummary?.readback_summary.camera.status ?? "not_loaded" }},
            /api/camera/devices={{ robotSummary?.readback_summary.camera.devices_status ?? "not_loaded" }}
          </dd>
          <dt>LiDAR</dt>
          <dd>
            /api/radar/status={{ robotSummary?.readback_summary.lidar.status ?? "not_loaded" }},
            scan={{ robotSummary?.readback_summary.lidar.latest_scan_proof_status ?? "not_loaded" }},
            raw={{ robotSummary?.readback_summary.lidar.latest_raw_packet_proof_status ?? "not_loaded" }}
          </dd>
          <dt>Base</dt>
          <dd>
            /api/base/status={{ robotSummary?.readback_summary.base.status ?? "not_loaded" }},
            readback={{ robotSummary?.readback_summary.base.latest_feedback_status ?? "not_loaded" }}
          </dd>
          <dt>unsafe starts</dt>
          <dd>radar start=false; map start=false; base manual=false</dd>
        </dl>
      </article>
    </div>

    <section class="preflight-panel">
      <h3>Robot API readback endpoints</h3>
      <table>
        <thead>
          <tr>
            <th>endpoint</th>
            <th>HTTP</th>
            <th>状态</th>
            <th>schema</th>
            <th>key readback</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="endpoint in robotSummary?.read_endpoints ?? []" :key="endpoint.id">
            <td>{{ endpoint.endpoint }}</td>
            <td>{{ endpoint.http_status ?? "n/a" }}</td>
            <td>{{ endpoint.request_status }} / {{ endpoint.status }}</td>
            <td>{{ endpoint.schema }}</td>
            <td>{{ JSON.stringify(endpoint.key_values).slice(0, 220) }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>
