<script setup lang="ts">
import type { RouteDebugInputs } from "../client/workstationApi";
import type { RouteDebugSummaryResponse } from "../shared/contracts";

const props = defineProps<{
  routeSummary: RouteDebugSummaryResponse | null;
  routeInputs: RouteDebugInputs;
}>();

const emit = defineEmits<{
  refresh: [];
  "update:routeInputs": [value: RouteDebugInputs];
}>();

const routeInputFields: Array<{ key: keyof RouteDebugInputs; label: string }> = [
  // 字段名保持与后端 query 参数一致，避免 UI 和 API 入口漂移。
  { key: "statusJson", label: "statusJson" },
  { key: "taskRecord", label: "taskRecord" },
  { key: "taskRecordDir", label: "taskRecordDir" },
  { key: "elevatorRouteReconciliation", label: "elevatorRouteReconciliation" },
];

function updateInput(key: keyof RouteDebugInputs, event: Event): void {
  // 组件只更新本地表单值；实际 query 拼接统一交给 workstationApi。
  const target = event.target as HTMLInputElement;
  emit("update:routeInputs", {
    ...props.routeInputs,
    [key]: target.value,
  });
}

function formatSummaryValue(value: unknown): string {
  // UI 只格式化后端 safe summary，不在前端补机器人状态或成功结论。
  if (value === null || value === undefined) {
    return "null";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}
</script>

<template>
  <section class="workspace">
    <div class="section-head">
      <h2>Route Debug</h2>
      <span class="pill">read-only</span>
    </div>
    <form class="route-inputs" @submit.prevent="emit('refresh')">
      <!-- 输入框保存用户本机路径；路径只送 API，不直接作为 safe summary 展示。 -->
      <label v-for="field in routeInputFields" :key="field.key">
        <span>{{ field.label }}</span>
        <input
          :value="routeInputs[field.key]"
          type="text"
          autocomplete="off"
          spellcheck="false"
          @input="updateInput(field.key, $event)"
        >
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
      <li>
        route_elevator_reconciliation={{
          routeSummary?.route_console_summary.route_elevator_reconciliation.lookup_status
        }}
      </li>
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
</template>
