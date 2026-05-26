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

    <div class="two-col snapshot-grid">
      <article class="snapshot-panel">
        <div class="section-head compact-head">
          <!-- 地图 snapshot 是 cloud 契约占位，不读取 /tf，也不证明刷新延迟。 -->
          <h3>Realtime map snapshot</h3>
          <span class="pill danger">{{ operatorConsole?.realtime_map_snapshot.snapshot_status ?? "blocked_not_proven" }}</span>
        </div>
        <dl class="kv compact-kv">
          <dt>schema</dt>
          <dd>{{ operatorConsole?.realtime_map_snapshot.schema ?? "trashbot.o7.realtime_map_snapshot.v1" }}</dd>
          <dt>map_ref</dt>
          <dd>{{ operatorConsole?.realtime_map_snapshot.map_ref.value ?? "not_connected" }}</dd>
          <dt>map frame</dt>
          <dd>
            {{ operatorConsole?.realtime_map_snapshot.map_frame.value ?? "map" }}
            · {{ operatorConsole?.realtime_map_snapshot.map_frame.status ?? "contract_placeholder_not_tf" }}
          </dd>
          <dt>pose</dt>
          <dd>
            x={{ operatorConsole?.realtime_map_snapshot.robot_pose.x_m ?? "null" }},
            y={{ operatorConsole?.realtime_map_snapshot.robot_pose.y_m ?? "null" }},
            yaw={{ operatorConsole?.realtime_map_snapshot.robot_pose.yaw_rad ?? "null" }}
          </dd>
          <dt>pose freshness</dt>
          <dd>
            age_ms={{ operatorConsole?.realtime_map_snapshot.pose_freshness.age_ms ?? "null" }}
            · latency_lt_2s_proven={{
              operatorConsole?.realtime_map_snapshot.pose_freshness.latency_lt_2s_proven ?? false
            }}
          </dd>
          <dt>route membership</dt>
          <dd>
            route={{ operatorConsole?.realtime_map_snapshot.route_membership.route_id ?? "not_connected" }}
            · on_route={{ operatorConsole?.realtime_map_snapshot.route_membership.on_route ?? false }}
            · in_elevator_zone={{
              operatorConsole?.realtime_map_snapshot.route_membership.in_elevator_zone ?? false
            }}
          </dd>
          <dt>safe_to_control</dt>
          <dd>{{ operatorConsole?.realtime_map_snapshot.safe_to_control ?? false }}</dd>
        </dl>
        <h3>Blocked by</h3>
        <ul class="dense">
          <!-- blocked reasons 明确缺 cloud stream、map artifact 和 /tf forwarding。 -->
          <li v-for="reason in operatorConsole?.realtime_map_snapshot.blocked_reasons" :key="reason">
            {{ reason }}
          </li>
        </ul>
      </article>

      <article class="snapshot-panel">
        <div class="section-head compact-head">
          <!-- 电梯 snapshot 只展示状态链槽位，不能解释为真实电梯在线。 -->
          <h3>Elevator state snapshot</h3>
          <span class="pill danger">{{
            operatorConsole?.elevator_state_snapshot.snapshot_status ?? "blocked_not_proven"
          }}</span>
        </div>
        <dl class="kv compact-kv">
          <dt>schema</dt>
          <dd>{{ operatorConsole?.elevator_state_snapshot.schema ?? "trashbot.o7.elevator_state_snapshot.v1" }}</dd>
          <dt>current state</dt>
          <dd>{{ operatorConsole?.elevator_state_snapshot.current_state ?? "not_connected" }}</dd>
          <dt>state chain</dt>
          <dd>
            {{
              operatorConsole?.elevator_state_snapshot.state_chain
                .map((state) => `${state.state}:${state.status}`)
                .join(" -> ") ?? "not_connected:not_proven"
            }}
          </dd>
          <dt>floor evidence</dt>
          <dd>
            {{ operatorConsole?.elevator_state_snapshot.current_floor_evidence.floor_label ?? "not_connected" }}
            · confidence={{
              operatorConsole?.elevator_state_snapshot.current_floor_evidence.confidence ?? "null"
            }}
          </dd>
          <dt>target floor</dt>
          <dd>
            {{ operatorConsole?.elevator_state_snapshot.target_floor.floor_label ?? "not_connected" }}
            · {{ operatorConsole?.elevator_state_snapshot.target_floor.confirmation_status ?? "not_proven" }}
          </dd>
          <dt>human takeover</dt>
          <dd>
            required={{ operatorConsole?.elevator_state_snapshot.human_takeover.required ?? true }}
            · reason={{
              operatorConsole?.elevator_state_snapshot.human_takeover.reason ??
                "real_elevator_state_chain_not_proven"
            }}
          </dd>
          <dt>primary actions</dt>
          <dd>{{ operatorConsole?.elevator_state_snapshot.primary_actions_enabled ?? false }}</dd>
        </dl>
        <h3>Blocked by</h3>
        <ul class="dense">
          <!-- blocked reasons 保留楼层识别和人工接管原因缺口。 -->
          <li v-for="reason in operatorConsole?.elevator_state_snapshot.blocked_reasons" :key="reason">
            {{ reason }}
          </li>
        </ul>
      </article>
    </div>

    <article class="snapshot-panel">
      <div class="section-head compact-head">
        <!-- 路线回放 snapshot 只展示 O6 归档对接字段，不能把 playback_available=false 渲染成播放器。 -->
        <h3>Route replay snapshot</h3>
        <span class="pill danger">{{
          operatorConsole?.route_replay_snapshot.snapshot_status ?? "blocked_not_proven"
        }}</span>
      </div>
      <div class="two-col">
        <dl class="kv compact-kv">
          <!-- task selector 固定无真实任务列表，避免 operator 误以为可选择历史任务。 -->
          <dt>schema</dt>
          <dd>{{ operatorConsole?.route_replay_snapshot.schema ?? "trashbot.o7.route_replay_snapshot.v1" }}</dd>
          <dt>task selector</dt>
          <dd>
            {{ operatorConsole?.route_replay_snapshot.task_selector.status ?? "blocked_no_cloud_task_archive" }}
            · count={{ operatorConsole?.route_replay_snapshot.task_selector.available_task_count ?? 0 }}
          </dd>
          <dt>selected task</dt>
          <dd>
            {{ operatorConsole?.route_replay_snapshot.selected_task.task_id ?? "not_connected" }}
            · evidence={{
              operatorConsole?.route_replay_snapshot.selected_task.evidence_ref ?? "missing_selected_task_record"
            }}
          </dd>
          <dt>trajectory</dt>
          <dd>
            frame_count={{ operatorConsole?.route_replay_snapshot.trajectory.frame_count ?? 0 }}
            · sample_frames={{
              operatorConsole?.route_replay_snapshot.trajectory.sample_frames.length ?? 0
            }}
            · {{ operatorConsole?.route_replay_snapshot.trajectory.status ?? "blocked_no_trajectory_api" }}
          </dd>
          <dt>playback cursor</dt>
          <dd>
            frame={{ operatorConsole?.route_replay_snapshot.playback_cursor.frame_index ?? "null" }}
            · ts={{ operatorConsole?.route_replay_snapshot.playback_cursor.timestamp_ms ?? "null" }}
            · {{ operatorConsole?.route_replay_snapshot.playback_cursor.status ?? "blocked_not_available" }}
          </dd>
          <dt>playback available</dt>
          <dd>{{ operatorConsole?.route_replay_snapshot.playback_available ?? false }}</dd>
          <dt>real archive</dt>
          <dd>{{ operatorConsole?.route_replay_snapshot.real_archive_connected ?? false }}</dd>
        </dl>
        <dl class="kv compact-kv">
          <!-- keyframe/evidence refs 当前都是 missing token，只给未来真实 archive 留槽。 -->
          <dt>keyframes</dt>
          <dd>
            count={{ operatorConsole?.route_replay_snapshot.keyframes.count ?? 0 }}
            · refs={{ operatorConsole?.route_replay_snapshot.keyframes.sample_refs.length ?? 0 }}
            · {{ operatorConsole?.route_replay_snapshot.keyframes.status ?? "blocked_no_keyframe_archive" }}
          </dd>
          <dt>task archive ref</dt>
          <dd>{{ operatorConsole?.route_replay_snapshot.evidence_refs.task_archive ?? "missing_o6_cloud_task_archive" }}</dd>
          <dt>trajectory ref</dt>
          <dd>{{ operatorConsole?.route_replay_snapshot.evidence_refs.trajectory_api ?? "missing_trajectory_api" }}</dd>
          <dt>keyframe ref</dt>
          <dd>{{ operatorConsole?.route_replay_snapshot.evidence_refs.keyframe_archive ?? "missing_keyframe_archive" }}</dd>
          <dt>transition ref</dt>
          <dd>
            {{
              operatorConsole?.route_replay_snapshot.evidence_refs.state_transition_archive ??
                "missing_state_transition_archive"
            }}
          </dd>
          <dt>state transitions</dt>
          <dd>
            count={{ operatorConsole?.route_replay_snapshot.state_transitions.count ?? 0 }}
            · sample={{ operatorConsole?.route_replay_snapshot.state_transitions.sample.length ?? 0 }}
            · {{
              operatorConsole?.route_replay_snapshot.state_transitions.status ??
                "blocked_no_state_transition_archive"
            }}
          </dd>
        </dl>
      </div>
      <div class="two-col">
        <div>
          <h3>State transition gaps</h3>
          <ul class="dense">
            <!-- gaps 是后续归档字段缺口，不代表 PC 已经查询过真实任务。 -->
            <li v-for="gap in operatorConsole?.route_replay_snapshot.state_transitions.gaps" :key="gap">
              {{ gap }}
            </li>
          </ul>
        </div>
        <div>
          <h3>Next evidence</h3>
          <ul class="dense">
            <!-- next evidence 指向 O6 cloud archive/trajectory API，对当前页面仍是只读缺口。 -->
            <li v-for="item in operatorConsole?.route_replay_snapshot.next_required_evidence" :key="item">
              {{ item }}
            </li>
          </ul>
        </div>
      </div>
    </article>

    <article class="snapshot-panel">
      <div class="section-head compact-head">
        <!-- 标注队列 snapshot 只展示 O6 annotation API 的缺口，不提供提交或回滚按钮。 -->
        <h3>Labeling queue snapshot</h3>
        <span class="pill danger">{{
          operatorConsole?.labeling_queue_snapshot.snapshot_status ?? "blocked_not_proven"
        }}</span>
      </div>
      <div class="two-col">
        <dl class="kv compact-kv">
          <!-- queue 和 selected item 固定未连接，避免把占位 media_ref 当作真实截图。 -->
          <dt>schema</dt>
          <dd>{{ operatorConsole?.labeling_queue_snapshot.schema ?? "trashbot.o7.labeling_queue_snapshot.v1" }}</dd>
          <dt>review queue</dt>
          <dd>
            {{ operatorConsole?.labeling_queue_snapshot.review_queue.status ?? "blocked_no_annotation_api" }}
            · count={{ operatorConsole?.labeling_queue_snapshot.review_queue.available_item_count ?? 0 }}
          </dd>
          <dt>selected item</dt>
          <dd>
            {{ operatorConsole?.labeling_queue_snapshot.selected_item.item_id ?? "not_connected" }}
            · media={{ operatorConsole?.labeling_queue_snapshot.selected_item.media_ref ?? "missing_review_item_media_ref" }}
          </dd>
          <dt>label schema</dt>
          <dd>
            {{ operatorConsole?.labeling_queue_snapshot.label_schema.schema_ref ?? "missing_label_schema" }}
            · {{ operatorConsole?.labeling_queue_snapshot.label_schema.status ?? "blocked_no_label_schema_api" }}
          </dd>
          <dt>draft labels</dt>
          <dd>
            count={{ operatorConsole?.labeling_queue_snapshot.draft_labels.count ?? 0 }}
            · {{ operatorConsole?.labeling_queue_snapshot.draft_labels.status ?? "blocked_no_selected_item" }}
          </dd>
          <dt>submit enabled</dt>
          <dd>{{ operatorConsole?.labeling_queue_snapshot.submit_enabled ?? false }}</dd>
          <dt>rollback enabled</dt>
          <dd>{{ operatorConsole?.labeling_queue_snapshot.rollback_enabled ?? false }}</dd>
        </dl>
        <dl class="kv compact-kv">
          <!-- 提交、回滚和导出字段只展示 future disabled endpoint 与 audit 缺口。 -->
          <dt>annotation API</dt>
          <dd>{{ operatorConsole?.labeling_queue_snapshot.real_annotation_api_connected ?? false }}</dd>
          <dt>submit audit</dt>
          <dd>
            {{ operatorConsole?.labeling_queue_snapshot.submit_audit.status ?? "blocked_not_available" }}
            · {{ operatorConsole?.labeling_queue_snapshot.submit_audit.audit_ref ?? "missing_submit_audit_log" }}
          </dd>
          <dt>rollback audit</dt>
          <dd>
            {{ operatorConsole?.labeling_queue_snapshot.rollback_audit.status ?? "blocked_not_available" }}
            · {{ operatorConsole?.labeling_queue_snapshot.rollback_audit.audit_ref ?? "missing_rollback_audit_log" }}
          </dd>
          <dt>dataset export</dt>
          <dd>
            available={{ operatorConsole?.labeling_queue_snapshot.dataset_export_available ?? false }}
            · {{ operatorConsole?.labeling_queue_snapshot.dataset_export.status ?? "blocked_not_available" }}
          </dd>
          <dt>export ref</dt>
          <dd>
            {{
              operatorConsole?.labeling_queue_snapshot.dataset_export.export_ref ??
                "missing_training_dataset_export"
            }}
          </dd>
        </dl>
      </div>
      <div class="three-col">
        <div>
          <h3>Allowed label types</h3>
          <ul class="dense">
            <!-- allowed types 是契约占位，status 保持 not_api，不能当作云端 schema 返回。 -->
            <li v-for="labelType in operatorConsole?.labeling_queue_snapshot.allowed_label_types" :key="labelType.type">
              {{ labelType.type }} · {{ labelType.status }} · values={{ labelType.values.length }}
            </li>
          </ul>
        </div>
        <div>
          <h3>Dataset export gaps</h3>
          <ul class="dense">
            <!-- gaps 明确训练集导出尚未接通，不渲染任何导出入口。 -->
            <li v-for="gap in operatorConsole?.labeling_queue_snapshot.dataset_export.gaps" :key="gap">
              {{ gap }}
            </li>
          </ul>
        </div>
        <div>
          <h3>Next evidence</h3>
          <ul class="dense">
            <!-- next evidence 指向 O6 annotation API 和 dataset export 后续证据。 -->
            <li v-for="item in operatorConsole?.labeling_queue_snapshot.next_required_evidence" :key="item">
              {{ item }}
            </li>
          </ul>
        </div>
      </div>
    </article>

    <article class="preflight-panel">
      <div class="section-head compact-head">
        <!-- 板端媒体摘要来自 API；缺省值也保持 blocked，避免页面加载失败时显示可用。 -->
        <h3>Board media preflight</h3>
        <span class="pill danger">{{ operatorConsole?.board_media_preflight_state ?? "blocked" }}</span>
      </div>
      <dl class="kv compact-kv">
        <!-- schema 和 required 字段让 operator 明确这是 O7 KR5 的前置证据缺口。 -->
        <dt>schema</dt>
        <dd>{{ operatorConsole?.board_media_preflight_schema ?? "trashbot.o7_board_media_preflight.v1" }}</dd>
        <dt>required</dt>
        <dd>{{ operatorConsole?.board_media_preflight_required ?? true }}</dd>
        <dt>safe_to_control</dt>
        <dd>{{ operatorConsole?.board_media_preflight_summary.safe_to_control ?? false }}</dd>
        <dt>primary_actions_enabled</dt>
        <dd>{{ operatorConsole?.board_media_preflight_summary.primary_actions_enabled ?? false }}</dd>
        <dt>device_probe_attempted</dt>
        <dd>{{ operatorConsole?.board_media_preflight_summary.device_probe_attempted ?? false }}</dd>
      </dl>
      <div class="two-col">
        <div>
          <h3>Blocked reasons</h3>
          <ul class="dense">
            <!-- blocked reasons 指向板端媒体缺口，不代表 PC 已经探测硬件。 -->
            <li v-for="reason in operatorConsole?.board_media_preflight_summary.blocked_reasons" :key="reason">
              {{ reason }}
            </li>
          </ul>
        </div>
        <div>
          <h3>Not proven</h3>
          <ul class="dense">
            <!-- not_proven 覆盖 RTC、摄像头、音频、ASR/TTS 和上车 smoke。 -->
            <li v-for="item in operatorConsole?.board_media_preflight_summary.not_proven" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
      <h3>Next evidence</h3>
      <ul class="dense">
        <!-- next evidence 是后续上车验收清单，不触发 PC 本地设备访问。 -->
        <li v-for="item in operatorConsole?.board_media_preflight_summary.next_required_evidence" :key="item">
          {{ item }}
        </li>
      </ul>
    </article>

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
