<script setup lang="ts">
export type WorkstationPanel =
  | "route"
  | "o7"
  | "o7Previews"
  | "evidence"
  | "hardware"
  | "training"
  | "boundary";

const activePanel = defineModel<WorkstationPanel>({ required: true });

const panels: Array<{ id: WorkstationPanel; label: string }> = [
  // 高级工具默认收起；这里保留工程入口，但不再把它们放到普通用户第一屏。
  { id: "route", label: "路线" },
  { id: "o7", label: "控制台" },
  { id: "o7Previews", label: "预览" },
  { id: "evidence", label: "证据" },
  { id: "hardware", label: "硬件" },
  { id: "training", label: "数据" },
  { id: "boundary", label: "安全边界" },
];
</script>

<template>
  <nav class="tabs" aria-label="workstation sections">
    <!-- tab 状态只是本地导航，不参与证明链路。 -->
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
</template>
