<script setup lang="ts">
export type WorkstationPanel =
  | "route"
  | "robotControl"
  | "o7"
  | "o7Previews"
  | "evidence"
  | "hardware"
  | "training"
  | "boundary";

const activePanel = defineModel<WorkstationPanel>({ required: true });

const panels: Array<{ id: WorkstationPanel; label: string }> = [
  // 标签改成普通用户更容易理解的短中文，但入口能力保持不变。
  { id: "robotControl", label: "机器人" },
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
