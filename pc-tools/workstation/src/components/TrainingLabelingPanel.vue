<script setup lang="ts">
import type { TrainingLabelingResponse } from "../shared/contracts";

defineProps<{
  trainingLabeling: TrainingLabelingResponse | null;
}>();

// 训练/标注入口只展示后端占位契约，不声明真实流水线已接通。
</script>

<template>
  <section class="workspace">
    <div class="section-head">
      <h2>Training/Labeling</h2>
      <span class="pill">placeholder_not_connected</span>
    </div>
    <div class="two-col">
      <!-- real_pipeline_connected=false 直接来自 API，避免 UI 文案升级能力。 -->
      <article v-for="entry in trainingLabeling?.entries" :key="entry.path">
        <h3>{{ entry.name }}</h3>
        <p>{{ entry.path }}</p>
        <p>real_pipeline_connected=false</p>
      </article>
    </div>
  </section>
</template>
