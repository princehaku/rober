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
        <span>complete file/material coverage</span>
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
        <strong>{{ hardwareMaterials?.safe_to_control ?? false }}</strong>
        <span>safe_to_control</span>
      </div>
      <div>
        <strong>{{ hardwareMaterials?.delivery_success ?? false }}</strong>
        <span>delivery_success</span>
      </div>
    </div>

    <p class="notice">
      {{ hardwareMaterials?.boundary_copy ?? "coverage is not HIL pass; material coverage is not_proven." }}
    </p>

    <div class="two-col compact-section">
      <article>
        <h3>Coverage gaps</h3>
        <ul class="dense">
          <!-- gaps 来自 Node scanner，作为补材料清单，不作为通过或失败按钮。 -->
          <li v-for="gap in hardwareMaterials?.gaps" :key="`${gap.fixture_relative_path}:${gap.missing_material}`">
            {{ gap.group }} - missing {{ gap.missing_material }} - {{ gap.recovery_hint }}
          </li>
          <li v-if="hardwareMaterials && hardwareMaterials.gaps.length === 0">
            no local file gaps; not_proven boundaries still apply
          </li>
        </ul>
      </article>
      <article>
        <h3>not_proven boundaries</h3>
        <ul class="dense">
          <li v-for="boundary in hardwareMaterials?.not_proven_boundaries" :key="boundary">{{ boundary }}</li>
        </ul>
      </article>
    </div>

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
        <tr v-for="group in hardwareMaterials?.fixture_groups" :key="group.fixture_relative_path">
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
        <h3>Vendor sources</h3>
        <ul class="dense">
          <!-- 来源列表来自 API，UI 只显示本地 vendor 文件和 fact ids，不补充硬件推断。 -->
          <li v-for="source in hardwareMaterials?.vendor_sources" :key="source.path">
            {{ source.path }} - {{ source.fact_ids.join(", ") }}
          </li>
        </ul>
      </article>
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
        <h3>Serial reference</h3>
        <dl class="kv">
          <dt>vendor_rpi_default_device</dt>
          <dd>{{ hardwareMaterials?.serial_reference.vendor_rpi_default_device }}</dd>
          <dt>vendor_rpi_alternate_device</dt>
          <dd>{{ hardwareMaterials?.serial_reference.vendor_rpi_alternate_device }}</dd>
          <dt>baudrate</dt>
          <dd>{{ hardwareMaterials?.serial_reference.baudrate }}</dd>
          <dt>orange_pi_device_status</dt>
          <dd>{{ hardwareMaterials?.serial_reference.orange_pi_device_status }}</dd>
        </dl>
      </article>
      <article>
        <h3>Command facts</h3>
        <ul class="dense">
          <li v-for="fact in hardwareMaterials?.command_facts" :key="fact.t">
            T={{ fact.t }} {{ fact.name }} source={{ fact.source_path }} hardware_verified={{ fact.hardware_verified }}
          </li>
        </ul>
      </article>
      <article>
        <h3>Feedback schema</h3>
        <dl class="kv">
          <dt>T1001 base_fields</dt>
          <dd>{{ hardwareMaterials?.feedback_schema.T1001.base_fields.join("/") }}</dd>
          <dt>module_conditional_fields</dt>
          <dd>{{ hardwareMaterials?.feedback_schema.T1001.module_conditional_fields.join("; ") }}</dd>
          <dt>source_path</dt>
          <dd>{{ hardwareMaterials?.feedback_schema.T1001.source_path }}</dd>
        </dl>
      </article>
      <article>
        <h3>API flags</h3>
        <dl class="kv">
          <dt>hardware_claim_level</dt>
          <dd>{{ hardwareMaterials?.hardware_claim_level ?? "software_material_coverage" }}</dd>
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
