<script setup lang="ts">
import type { O7OperatorConsoleResponse } from "../shared/contracts";

defineProps<{
  operatorConsole: O7OperatorConsoleResponse | null;
}>();
</script>

<template>
  <section class="workspace">
    <div class="section-head">
      <!-- 顶部状态直接来自 API，提醒 operator 当前只是契约视图。 -->
      <h2>O7 Operator Console</h2>
      <span class="pill danger">{{ operatorConsole?.cloud_api_status ?? "draft_blocked_not_proven" }}</span>
    </div>

    <dl class="kv">
      <!-- contract source 是 cloud-relay helper，PC 不在前端发明状态。 -->
      <dt>contract source</dt>
      <dd>{{ operatorConsole?.contract_source ?? "cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py" }}</dd>
      <!-- observe_only 是当前手控和寻路入口的安全边界。 -->
      <dt>operator mode</dt>
      <dd>{{ operatorConsole?.operator_mode ?? "observe_only" }}</dd>
      <dt>robot connection</dt>
      <dd>{{ operatorConsole?.robot_connection ?? "not_connected_by_pc" }}</dd>
      <dt>command dispatch</dt>
      <dd>{{ operatorConsole?.manual_control_policy.command_dispatch_enabled ?? false }}</dd>
      <dt>success claim allowed</dt>
      <dd>{{ operatorConsole?.manual_control_policy.success_claim_allowed ?? false }}</dd>
    </dl>

    <div class="kr-grid">
      <!-- 六个 KR 逐项展示，所有字段都来自后端契约。 -->
      <article v-for="kr in operatorConsole?.kr_views" :key="kr.id">
        <div class="section-head compact-head">
          <!-- status 只能是 draft/blocked/not_proven，不能渲染成功态。 -->
          <h3>{{ kr.id }} · {{ kr.title }}</h3>
          <span class="pill danger">{{ kr.status }}</span>
        </div>
        <dl class="kv compact-kv">
          <!-- cloud contract 是后续 O6/O7 对齐点，不代表端点已上线。 -->
          <dt>cloud contract</dt>
          <dd>{{ kr.cloud_contract }}</dd>
          <dt>PC surface</dt>
          <dd>{{ kr.pc_surface }}</dd>
          <dt>next contract</dt>
          <dd>{{ kr.next_required_contract }}</dd>
        </dl>
        <h3>Current view</h3>
        <ul class="dense">
          <!-- current_view 用 token 表示最小状态，避免写成真实实时数据。 -->
          <li v-for="item in kr.current_view" :key="item">{{ item }}</li>
        </ul>
        <h3>Blocked by</h3>
        <ul class="dense">
          <!-- blocked_by 让 operator 看到缺口，不提供绕过云端的替代入口。 -->
          <li v-for="item in kr.blocked_by" :key="item">{{ item }}</li>
        </ul>
      </article>
    </div>

    <h3>Command previews</h3>
    <table>
      <thead>
        <tr>
          <th>Envelope</th>
          <th>Status</th>
          <th>Cloud endpoint</th>
          <th>Recovery path</th>
        </tr>
      </thead>
      <tbody>
        <!-- 这些行不是按钮；sends_to_robot=false 固定关闭真实控制。 -->
        <tr v-for="command in operatorConsole?.command_previews" :key="command.id">
          <td>{{ command.label }} · sends_to_robot={{ command.sends_to_robot }}</td>
          <td>{{ command.status }} · confirmation={{ command.requires_confirmation }}</td>
          <td>{{ command.cloud_endpoint }}</td>
          <td>{{ command.recovery_path }}</td>
        </tr>
      </tbody>
    </table>

    <div class="two-col">
      <article>
        <h3>Blocked reasons</h3>
        <ul class="dense">
          <!-- blocked reasons 是当前不可用原因，不是运行失败日志。 -->
          <li v-for="reason in operatorConsole?.blocked_reasons" :key="reason">{{ reason }}</li>
        </ul>
      </article>
      <article>
        <h3>Recovery paths</h3>
        <ul class="dense">
          <!-- recovery paths 指向后续 owner 协作，不触发任何本地命令。 -->
          <li v-for="path in operatorConsole?.recovery_paths" :key="path">{{ path }}</li>
        </ul>
      </article>
    </div>
  </section>
</template>
