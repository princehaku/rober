<script setup lang="ts">
import { computed } from "vue";
import type { RealMaterialAcceptanceResponse } from "../shared/contracts";

const props = defineProps<{
  realMaterialAcceptance: RealMaterialAcceptanceResponse | null;
}>();

const statusCopy = computed(() => {
  // summary 由后端统一计算；前端只压缩成 operator 能扫一眼的队列概览。
  const summary = props.realMaterialAcceptance?.summary;
  if (!summary) {
    return "accepted=0 · needs_long_run=0 · not_observed=0 · blocked=0";
  }
  return [
    `accepted=${summary.accepted}`,
    `needs_long_run=${summary.needs_long_run}`,
    `not_observed=${summary.not_observed}`,
    `blocked=${summary.blocked}`,
  ].join(" · ");
});

const queueItems = computed(() => {
  // 未加载时给出空数组，让模板保持 fail-closed 文案而不是伪造材料项。
  return props.realMaterialAcceptance?.items ?? [];
});
</script>

<template>
  <section class="real-material-queue-panel" aria-label="Real material acceptance queue">
    <div class="section-head compact-head">
      <div>
        <!-- 队列只展示已有证据缺口，不提供执行 probe 或控制机器人按钮。 -->
        <p class="eyebrow">O5/O6/O7 real-material acceptance</p>
        <h2>真实材料验收队列</h2>
      </div>
      <span class="pill danger">{{ realMaterialAcceptance?.queue_status ?? "not_loaded" }}</span>
    </div>

    <dl class="kv compact-kv">
      <dt>schema</dt>
      <dd>{{ realMaterialAcceptance?.schema ?? "trashbot.pc_tools_workstation.real_material_acceptance.v1" }}</dd>
      <dt>summary</dt>
      <dd>{{ statusCopy }}</dd>
      <dt>fail-closed</dt>
      <dd>
        safe_to_control={{ realMaterialAcceptance?.fail_closed_flags.safe_to_control ?? false }}
        · sends_commands={{ realMaterialAcceptance?.fail_closed_flags.sends_commands ?? false }}
        · robot_control_executed={{ realMaterialAcceptance?.fail_closed_flags.robot_control_executed ?? false }}
      </dd>
      <dt>execution</dt>
      <dd>
        artifacts_only={{ realMaterialAcceptance?.execution_policy.reads_existing_artifacts_only ?? true }}
        · network_probe={{ realMaterialAcceptance?.execution_policy.network_probe_executed ?? false }}
        · post={{ realMaterialAcceptance?.execution_policy.post_executed ?? false }}
        · robots_path={{ realMaterialAcceptance?.execution_policy.robots_path_accessed ?? false }}
      </dd>
    </dl>

    <div class="probe-endpoint-grid">
      <article v-for="item in queueItems" :key="item.id" class="probe-endpoint-card">
        <!-- item.status 来自后端 queue，不在 UI 里二次推断。 -->
        <strong>{{ item.objective }} · {{ item.status }}</strong>
        <span>{{ item.title }}</span>
        <span>source={{ item.source_endpoint }} · artifact={{ item.source_artifact_status }}</span>
        <span>
          freshness={{ item.artifact_freshness.status }} · age={{ item.artifact_freshness.age_seconds ?? "n/a" }}s ·
          ref={{ item.artifact_freshness.artifact_ref }}
        </span>
        <span>reason={{ item.blocking_reason }}</span>
        <span>next={{ item.next_action }}</span>
        <span>runbook={{ item.collection_runbook.goal }}</span>
        <span>cmd={{ item.collection_runbook.suggested_commands[0] }}</span>
        <span>success={{ item.collection_runbook.success_criteria.join(" | ") }}</span>
        <span>boundary={{ item.proof_boundary }}</span>
      </article>
    </div>

    <ul class="dense">
      <!-- next_actions 是 operator 的下一步工作队列；为空代表当前摘要已被后端判定 accepted。 -->
      <li v-for="action in realMaterialAcceptance?.next_actions ?? ['real_material_acceptance_queue_not_loaded']" :key="action">
        {{ action }}
      </li>
    </ul>
  </section>
</template>
