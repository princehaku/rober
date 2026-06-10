<script setup lang="ts">
import ProofFlagStrip from "./ProofFlagStrip.vue";
import type { HealthResponse, ProofBoundaryResponse } from "../shared/contracts";

defineProps<{
  health: HealthResponse | null;
  proofBoundary: ProofBoundaryResponse | null;
}>();

// Proof Boundary 是跨页面安全说明，所有字段必须来自 API 响应。
</script>

<template>
  <section class="workspace">
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
      <!-- 控制策略由后端 proof boundary 给出，页面只做只读展示。 -->
      <dt>workstation_executes_control</dt>
      <dd>false</dd>
      <dt>route_loader_mode</dt>
      <dd>{{ proofBoundary?.control_policy.route_loader_mode }}</dd>
      <dt>recovery_path</dt>
      <dd>{{ proofBoundary?.control_policy.recovery_path }}</dd>
    </dl>
    <details class="advanced-details">
      <summary>高级安全信息</summary>
      <ProofFlagStrip :health="health" />
    </details>
  </section>
</template>
