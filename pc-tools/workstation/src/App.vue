<script setup lang="ts">
import { onMounted, ref } from "vue";
import O7LiveOperatorPanel from "./components/O7LiveOperatorPanel.vue";
import { getO7LiveOperatorPanel } from "./client/workstationApi";
import type { O7LiveOperatorPanelResponse } from "./shared/contracts";

// 首屏只拉 O7 live operator 合同，避免用户控制台默认加载 O5/O6/cloud/验收材料。
const loading = ref(true);
// API 错误只影响状态展示，不打开任何控制动作。
const error = ref("");
// 机器人事实仍来自后端合同；前端不硬编码 ready 或可控状态。
const o7LiveOperatorPanel = ref<O7LiveOperatorPanelResponse | null>(null);

async function refresh(): Promise<void> {
  // 刷新只读状态，不触发 camera /offer，也不触发任何机器人控制 API。
  loading.value = true;
  error.value = "";
  try {
    o7LiveOperatorPanel.value = await getO7LiveOperatorPanel();
  } catch (err) {
    // 后端不可用时保持 fail-closed 文案，避免用户误以为控制可用。
    error.value = err instanceof Error ? err.message : "workstation_api_unavailable";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  // 页面进入后读取一次只读合同，让四个状态灯能及时显示未知/锁定。
  void refresh();
});
</script>

<template>
  <main class="user-console-shell">
    <header class="console-topbar">
      <div>
        <p class="console-kicker">PC 本地控制入口</p>
        <h1>Rober 控制台</h1>
      </div>
      <button class="console-refresh" type="button" @click="refresh">刷新状态</button>
    </header>

    <div v-if="error" class="user-notice" role="alert">
      无法读取本机状态：{{ error }}。控制保持锁定。
    </div>

    <section v-if="loading" class="console-loading" aria-live="polite">
      正在读取 Rober 状态...
    </section>

    <O7LiveOperatorPanel v-else :live-operator-panel="o7LiveOperatorPanel" />
  </main>
</template>
