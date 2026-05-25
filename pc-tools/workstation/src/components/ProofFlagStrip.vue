<script setup lang="ts">
import type { HealthResponse } from "../shared/contracts";
import { PROOF_FLAGS } from "../shared/contracts";

defineProps<{
  health: HealthResponse | null;
}>();

// 证明旗标只来自 health 或共享默认值，页面不自行创造成功状态。
</script>

<template>
  <section class="status-strip" aria-label="proof flags">
    <!-- 这些字段是工作站的 fail-closed 锚点，必须持续可见。 -->
    <span>source={{ health?.source ?? PROOF_FLAGS.source }}</span>
    <span>proof_status={{ health?.proof_status ?? PROOF_FLAGS.proof_status }}</span>
    <span>safe_to_control=false</span>
    <span>delivery_success=false</span>
    <span>pc_only=true</span>
  </section>
</template>
