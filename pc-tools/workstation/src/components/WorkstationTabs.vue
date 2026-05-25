<script setup lang="ts">
export type WorkstationPanel = "route" | "evidence" | "hardware" | "training" | "boundary";

const activePanel = defineModel<WorkstationPanel>({ required: true });

const panels: Array<{ id: WorkstationPanel; label: string }> = [
  // 四个入口对应工作站只读能力，不增加任何控制台式主动作。
  { id: "route", label: "Route Debug" },
  { id: "evidence", label: "Evidence Tools" },
  { id: "hardware", label: "Hardware Materials" },
  { id: "training", label: "Training/Labeling" },
  { id: "boundary", label: "Proof Boundary" },
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
