<script setup lang="ts">
import type { HardwareMaterialsResponse } from "../shared/contracts";

defineProps<{
  hardwareMaterials: HardwareMaterialsResponse | null;
}>();
</script>

<template>
  <section class="workspace">
    <div class="section-head">
      <div>
        <h2>WAVE ROVER Material Coverage</h2>
        <p class="eyebrow">coverage is not HIL pass; software_proof/not_proven only</p>
      </div>
      <span class="pill danger">{{ hardwareMaterials?.proof_status ?? "not_proven" }}</span>
    </div>

    <div class="metrics">
      <!-- 覆盖计数只描述材料文件是否存在，不代表真机连通、标定或运动通过。 -->
      <div>
        <strong>{{ hardwareMaterials?.coverage_summary.groups_total ?? 0 }}</strong>
        <span>groups</span>
      </div>
      <div>
        <strong>{{ hardwareMaterials?.coverage_summary.groups_complete ?? 0 }}</strong>
        <span>complete coverage</span>
      </div>
      <div>
        <strong>{{ hardwareMaterials?.coverage_summary.groups_partial ?? 0 }}</strong>
        <span>partial coverage</span>
      </div>
      <div>
        <strong>{{ hardwareMaterials?.coverage_summary.groups_missing ?? 0 }}</strong>
        <span>missing coverage</span>
      </div>
      <div>
        <strong>false</strong>
        <span>safe_to_control</span>
      </div>
      <div>
        <strong>false</strong>
        <span>delivery_success</span>
      </div>
    </div>

    <p class="notice">
      {{ hardwareMaterials?.boundary_copy ?? "coverage is not HIL pass; material coverage is not_proven." }}
    </p>

    <table>
      <thead>
        <tr>
          <th>Group</th>
          <th>Fixture relative path</th>
          <th>Coverage</th>
          <th>Present materials</th>
          <th>Missing materials</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <!-- 每行来自 API scanner；UI 不自行推断 pass/fail。 -->
        <tr v-for="group in hardwareMaterials?.groups" :key="group.fixture_relative_path">
          <td>{{ group.group }}</td>
          <td>{{ group.fixture_relative_path }}</td>
          <td>{{ group.coverage_counts.present }}/{{ group.coverage_counts.required }}</td>
          <td>{{ group.present_materials.join(", ") || "none" }}</td>
          <td>{{ group.missing_materials.join(", ") || "none" }}</td>
          <td>{{ group.status }}</td>
        </tr>
      </tbody>
    </table>

    <div class="two-col">
      <article>
        <h3>Required materials</h3>
        <ul class="dense">
          <li v-for="material in hardwareMaterials?.required_materials" :key="material.id">
            {{ material.required_path }} - {{ material.description }}
          </li>
        </ul>
      </article>
      <article>
        <h3>Fail-closed tokens</h3>
        <ul class="dense">
          <li v-for="token in hardwareMaterials?.fail_closed_tokens" :key="token">{{ token }}</li>
        </ul>
      </article>
      <article>
        <h3>Bounded vendor facts</h3>
        <ul class="dense">
          <li v-for="fact in hardwareMaterials?.vendor_facts_bounded" :key="fact">{{ fact }}</li>
        </ul>
      </article>
      <article>
        <h3>API flags</h3>
        <dl class="kv">
          <dt>source</dt>
          <dd>{{ hardwareMaterials?.source ?? "software_proof" }}</dd>
          <dt>proof_status</dt>
          <dd>{{ hardwareMaterials?.proof_status ?? "not_proven" }}</dd>
          <dt>primary_actions_enabled</dt>
          <dd>{{ hardwareMaterials?.primary_actions_enabled ?? false }}</dd>
          <dt>pc_only</dt>
          <dd>{{ hardwareMaterials?.pc_only ?? true }}</dd>
        </dl>
      </article>
    </div>
  </section>
</template>
