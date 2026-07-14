# Tech Plan - O3 Map Server Lifecycle Activation Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/`
- Owner: `robot-software-engineer`
- Product owner: `product-okr-owner`
- Target: strict no-motion `/map_server` lifecycle activation repair/proof

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1/当前最高优先级显示最低 Objective 是 O5，约 `85%`。O1/O6/O7 约 `93%`。
2. 本 sprint 不直接针对 O5。
3. 原因：O5 当前只能靠真实 production external evidence 计分；readiness packet、surface、review、handoff、intake 或其他 support-only work 不得继续提升 OKR。本轮选择 O3/O1 strict no-motion 现场链路，因为它能在真实上位机上推进 current-run `/map_server` lifecycle clean，并可能解锁后续 `/map`、AMCL pose、dynamic `map->odom` 和 planner-only path gate。
4. 方向判断：O5 `暂停 support-only`；O3/O1 `继续`；O6/O7 `暂停等待新材料`。本轮不调整百分比，不归档 KR。

## 上轮证据输入

来自 `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/`：

- `canonical_classification=map_server_node_absent`
- `failure_detail=lifecycle_retry_node_not_found`
- `/map_server` retry `stderr="Node not found\n"`
- no-motion fields false

来自 `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/`：

- `managed_runtime_requested=true`
- `managed_runtime_started=true`
- `managed_runtime_cleanup_ok=true`
- `proof.map_server_presence_recovery.canonical_classification=map_server_lifecycle_not_active_after_recovery`
- `failure_detail=lifecycle_manager_failed_to_change_state_for_map_server`
- runtime log 证明 lifecycle manager starts、map_server enters `Configuring`、`trashbot_map.yaml` 和 `trashbot_map.pgm` load，随后 `Failed to change state for node: map_server`
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

本轮必须把边界从 generic lifecycle manager failure 推进到 lifecycle clean，或更窄 configure/activate classification。

## 同一 Blocker 红线判断

- 09-54 是 `map_server_node_absent`。
- 10-54 是 `lifecycle_manager_failed_to_change_state_for_map_server`。
- 本轮允许继续一次，因为 root cause 已从 map_server node absent 前进到 map_server configure/activate 期间 state change failed。
- 若本轮仍停在完全相同 `lifecycle_manager_failed_to_change_state_for_map_server` 且没有更窄错误、stderr/stdout、process exit、map yaml/pgm 可读性或参数/lifecycle 管辖 classification，下一轮必须 CEO 升级或切 Objective。

## 技术方案

Robot Software 单 owner 闭环。

实施建议路径：

1. 扩展或修复 `o10_amcl_nav2_runtime_proof.py` 的 `/map_server` lifecycle activation proof，保留 10-54 的 presence recovery 字段作为前置事实。
2. 采集并结构化记录：
   - map_server stderr/stdout、recent log lines、exception text
   - lifecycle_manager log and state-change result
   - map yaml/pgm exists/readable/hash basename
   - yaml fields: image path、resolution、origin、occupied_thresh、free_thresh、mode
   - frame_id 或 map server frame 参数
   - launch 参数、node name/namespace、lifecycle manager managed node list
   - process exit status、service timeout、returncode
3. 如原因明确，优先修复 launch/parameter/map path/lifecycle manager 管辖问题，让 `/map_server` lifecycle transition clean。
4. 如果无法修复，artifact 必须输出更窄 canonical classification，例如：
   - `map_server_yaml_image_unreadable`
   - `map_server_yaml_invalid_fields`
   - `map_server_frame_id_missing_or_invalid`
   - `map_server_process_exited_during_configure`
   - `map_server_configure_exception`
   - `lifecycle_manager_map_server_name_mismatch`
   - `lifecycle_manager_map_server_namespace_mismatch`
   - `map_server_activate_callback_failed`
   - `map_server_lifecycle_service_timeout_with_process_alive`
5. 不进入 NavigateToPose、不发布 `/cmd_vel`、不调用 `/api/base/manual`、不打开 WAVE ROVER UART。

## 允许文件范围

Robot Software 实施允许改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/src/ros2_trashbot_bringup/launch/`
- `onboard/src/ros2_trashbot_bringup/CMakeLists.txt`，仅当 map server launch/install 入口需要修复
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `onboard/src/ros2_trashbot_bringup/test/`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/tech-done.md`
- `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/artifacts/`

不得改动：

- WAVE ROVER、ESP32、UART、串口、波特率、接线、硬件配置。
- `OKR.md`
- `docs/process/okr_progress_log.md`
- O5/O6/O7 API/UI/archive 代码。
- 历史 sprint 目录。

如发现必须依赖硬件串口、接线、波特率、JSON 指令、速度映射或 feedback 协议事实，停止相关实现假设，派 `rober-hardware-engineer` 读取 `docs/vendor/VENDOR_INDEX.md` 及其指向资料后再继续；本轮默认不触碰硬件配置。

## 接口影响

允许影响：

- `o10_amcl_nav2_runtime_proof.py` artifact schema 增加 additive fields，描述 `/map_server` lifecycle activation proof。
- no-motion helper 可新增 map_server configure/activate log parsing、yaml/pgm readback、parameter/lifecycle manager checks。
- bringup launch 可修复 map server/lifecycle manager 管辖关系，但必须保持 motion/control 默认关闭。
- navigation docs 同步 proof boundary。

禁止影响：

- 不改变 `/cmd_vel`、`/api/base/manual`、WAVE ROVER UART 或真实底盘控制入口。
- 不执行 NavigateToPose 或 Nav2 route execution。
- 不把 map_server active 自动转成 `safe_to_control=true`。
- 不改变 O5/O6/O7 合同。

## 验收命令

Robot Software 必须运行并记录以下命令。若实施中需要替换 true-board 命令参数，必须把实际命令、返回码、stdout/stderr 摘要和 artifact 字段写入 `tech-done.md`。

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

Local strict no-motion dry-run：

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/artifacts/local_o10_map_server_lifecycle_activation_repair.raw.json
```

True-board strict no-motion run/pull artifact：

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_lifecycle_activation_repair.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_lifecycle_activation_repair.raw.json \
  sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/artifacts/live_o10_map_server_lifecycle_activation_repair.raw.json
```

Scoped git diff --check：

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/scripts/o11_nav2_lifecycle.sh \
  onboard/src/ros2_trashbot_bringup \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair
```

Planning阶段验收命令：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|85%|map_server_lifecycle_not_active_after_recovery|lifecycle_manager_failed_to_change_state_for_map_server|同一 Blocker|robot-software-engineer|strict no-motion|NavigateToPose|cmd_vel|base/manual|WAVE ROVER|git diff --check" sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair
```

```bash
git diff --check -- sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair
```

## 验收判定

Accept：

- true-board artifact 越过 lifecycle manager `Failed to change state for node: map_server`，或更窄地证明 configure/activate blocker。
- no-motion 字段全部 false。
- map_server stderr/stdout、lifecycle_manager log、map yaml/pgm readback、frame_id/parameter/lifecycle 管辖、process exit 被明确记录。
- local dry-run fail-closed。
- tests 和 scoped `git diff --check` 通过。

Needs retry：

- artifact 仍只输出完全相同 `lifecycle_manager_failed_to_change_state_for_map_server`，没有更窄分类和日志字段。
- primary blocker 是 generic timeout，没有 map_server configure/activate 证据。
- `/scan`、AMCL、TF、planner timeout 被当作 primary result。
- docs 或 sprint `tech-done.md` 未记录 proof boundary。

Reject：

- 发送 NavigateToPose。
- 发布 `/cmd_vel`。
- 调用 `/api/base/manual`。
- 打开 WAVE ROVER UART。
- 改硬件配置或未读 vendor 资料就假设硬件事实。

## 风险边界

- `/map_server` lifecycle clean 仅证明 map server node/lifecycle 可见性改善，不证明 `/map` sample、TF、localization ready、path generation、route execution、delivery success、safe-to-control 或 HIL。
- 如果 true-board SSH 不可达，本轮只能记录 blocked，不能用 local artifact 替代 true-board proof。
- 如果本轮结束仍是完全相同 `lifecycle_manager_failed_to_change_state_for_map_server` 且没有更窄错误，必须触发同一 Blocker 红线：升级 CEO 决策或切换 Objective，不能继续包装诊断。

## 后续文档要求

Robot Software 实施完成后必须更新：

- `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/tech-done.md`

Product 验收阶段再更新：

- `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/side2side_check.md`
- `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/final.md`
