<script setup lang="ts">
import { computed } from "vue";
import type { EvidenceToolsResponse } from "../shared/contracts";

const props = defineProps<{
  evidenceTools: EvidenceToolsResponse | null;
}>();

const categoryRows = computed(() =>
  // Evidence 分类来自 API 只读索引，前端只负责稳定排序和展示。
  Object.entries(props.evidenceTools?.categories ?? {}).sort(([left], [right]) => left.localeCompare(right)),
);
</script>

<template>
  <section class="workspace">
    <div class="section-head">
      <h2>Evidence Tools</h2>
      <span class="pill">{{ evidenceTools?.total_json_fixtures ?? 0 }} fixtures</span>
    </div>
    <div class="metrics">
      <!-- 分类计数是 fixture 索引规模，不代表现场验证通过数量。 -->
      <div v-for="[category, count] in categoryRows" :key="category">
        <strong>{{ count }}</strong>
        <span>{{ category }}</span>
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th>Group</th>
          <th>Category</th>
          <th>Fixtures</th>
          <th>Summary</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="asset in evidenceTools?.assets" :key="asset.group">
          <td>{{ asset.group }}</td>
          <td>{{ asset.category }}</td>
          <td>{{ asset.fixture_count }}</td>
          <td>{{ asset.summary }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
