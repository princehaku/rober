# Tech Plan - O3 Map Server On-Configure IO Order Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/`
- Owner: `robot-software-engineer`
- Product owner: `product-okr-owner`
- Target: repair `/map_server` lifecycle clean/active or narrow `map_server_configure_return_failure_before_deferred_map_read_completed` under strict no-motion

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1/当前最高优先级显示最低 Objective 是 O5，约 `85%`；O1/O6/O7 约 `93%`。
2. 本 sprint 不直接针对 O5。
3. 原因：O5 当前缺真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence；继续 support-only packet、review、handoff、readiness wrapper 或 surface 不允许计主 OKR 增量。
4. 本 sprint 选择 O3/O1 strict no-motion，因为 13:54 accepted artifact 已把 true-board blocker 收敛到 `/map_server` configure ordering；这是 current same-run path generation、Nav2 route execution 和后续 delivery evidence 的前置条件。
5. 本轮 OKR 百分比默认不调整；只有出现 same-run path generation、route execution、current live HIL、delivery/operator acceptance 或 production external evidence 才考虑调整。

## 上轮证据输入

最新 accepted sprint：`sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/`。

Primary live artifact：`sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/live_o10_map_server_configure_failure_repair.raw.json`。

已知事实：

- `status=blocked_with_root_cause`
- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `proof.managed_runtime_started=true`
- `proof.map_server_active=false`
- `proof.amcl_active=false`
- `proof.root_causes[0].layer=Nav2 map_server transition callback`
- `proof.root_causes[0].reason=map_server_configure_return_failure_before_deferred_map_read_completed`
- `proof.root_causes[0].detail=lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_configure_return_failure_before_deferred_map_read_completed`
- `proof.map_server_transition_callback_probe.transition_sequence.observed_stage=configure`
- `transition_sequence.configure.lifecycle_manager_requested=true`
- `transition_sequence.configure.map_server_callback_entered=true`
- `transition_sequence.configure.yaml_load_started=true`
- `transition_sequence.configure.image_load_started=true`
- `transition_sequence.configure.map_read_completed=true`
- `transition_sequence.configure.state_change_failed=true`
- `transition_sequence.configure.state_change_failed_before_map_read_completed=true`
- `service_rpc_timing.inferred_change_state_response=failure`
- `bond_timing.bond_stage=not_created_before_configure_return_failure`
- `runtime_log_window.events.map_read_after_state_change_failure=true`
- `runtime_log_window.dds_transport_error_text=""`
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

## 同一 Blocker 红线判断

- 12:55：`map_server_configure_callback_return_failure` with ChangeState inferred failure before bond creation。
- 13:54：`map_server_configure_return_failure_before_deferred_map_read_completed` with map read completion ordering and empty DDS transport error text。
- 本轮允许继续，因为 root cause 从 generic callback failure 下钻到 configure/map IO ordering。
- 本轮必须继续推进到 `/map_server` lifecycle clean/active，或比 `map_server_configure_return_failure_before_deferred_map_read_completed` 更窄。
- 若本轮仍完全重复同一句 root cause 且没有更窄 evidence，验收标记 `needs retry`；若 retry 后仍无法推进，下一步必须 `升级 CEO` 或切换 Objective，不接受继续包装同一 blocker。

## 技术方案

Robot Software 单 owner 闭环。

实施建议路径：

1. 先确认 local worktree 与 true-board 脚本版本一致，避免旧 helper 或旧 launch 影响 conclusion。
2. 检查 `o10_amcl_nav2_runtime_proof.py` 对 runtime log window 的 ordering 解析，特别是 `state_change_failed_before_map_read_completed` 与 `map_read_after_state_change_failure` 是否来自同一启动窗口。
3. 在不触发运动的前提下，补充 map_server `on_configure` 证据：
   - callback enter/exit timing
   - callback return code / exception text
   - map yaml open、image open、map decode、map publication 初始化的 ordering
   - lifecycle state before/after configure
   - process alive/exit status
4. 检查 lifecycle manager ChangeState response handling：
   - `/map_server/change_state` request/response timing
   - response success flag 或 failure detail
   - service availability wait 与 timeout
   - lifecycle manager log line around configure failure
5. 检查 executor timing / starvation：
   - managed runtime startup order
   - map_server process still alive while response failed
   - whether cleanup or SIGINT lines are excluded from primary window
6. 检查 bond prerequisites：
   - bond should not be expected before configure success
   - if bond creation appears before active, classify exact timing
7. 若发现 launch/parameter/timing bug，优先修复并 true-board strict no-motion 重跑。
8. 若不能修复，artifact 必须输出更窄 canonical classification，例如：
   - `map_server_on_configure_exception`
   - `map_server_on_configure_return_false_after_yaml_load`
   - `map_server_on_configure_return_false_after_image_load`
   - `map_server_map_io_completion_after_changestate_failure`
   - `map_server_map_io_blocked_before_configure_return`
   - `lifecycle_manager_changestate_response_false_without_exception`
   - `map_server_change_state_rpc_timeout_or_error`
   - `map_server_executor_starvation_before_configure_response`
   - `map_server_process_exited_during_on_configure`
   - `map_server_parameter_invalid_during_configure`
   - `map_server_bond_prerequisite_not_reached_before_configure_success`
9. 如果 `/map_server` lifecycle clean/active，才允许读取 `/map` sample、AMCL lifecycle readback 和 dynamic `map->odom` readiness；仍不得进入 NavigateToPose、route execution、`/cmd_vel`、`/api/base/manual` 或 WAVE ROVER UART。

## Robot Software 文件范围

后续实施允许 `robot-software-engineer` 改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/src/ros2_trashbot_bringup/launch/`
- `onboard/src/ros2_trashbot_bringup/CMakeLists.txt`，仅当 launch/install 入口事实需要修复
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `onboard/src/ros2_trashbot_bringup/test/`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/tech-done.md`
- `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/artifacts/`

不得改动：

- WAVE ROVER、ESP32、UART、串口、波特率、接线或硬件配置。
- `OKR.md`
- `docs/process/okr_progress_log.md`
- O5/O6/O7 API/UI/archive 代码。
- 历史 sprint 目录。

## 接口影响

允许影响：

- `o10_amcl_nav2_runtime_proof.py` 增加 additive proof fields，记录 map_server `on_configure`、map IO ordering、ChangeState response、executor timing、bond prerequisites、参数/异常证据。
- no-motion helper 可修复 lifecycle/readback/log parsing、map_server launch 参数或 lifecycle manager timing。
- navigation docs 同步新的 proof boundary。

禁止影响：

- 不改变 `/cmd_vel`、`/api/base/manual`、WAVE ROVER UART 或底盘控制入口。
- 不执行 NavigateToPose 或 Nav2 route execution。
- 不把 lifecycle clean/active 自动转成 `safe_to_control=true`。
- 不改变 O5/O6/O7 合同。

## 验收命令

Robot Software 必须运行并记录以下命令。若 true-board 命令参数需要调整，必须把实际命令、返回码、stdout/stderr 摘要和 artifact 字段写入 `tech-done.md`。

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

如修改 lifecycle script，追加：

```bash
bash -n onboard/scripts/o11_nav2_lifecycle.sh
```

Local strict no-motion dry-run：

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/artifacts/local_o10_map_server_on_configure_io_order_repair.raw.json
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

如修改 `onboard/scripts/o11_nav2_lifecycle.sh`，同步：

```bash
scp -P 37878 onboard/scripts/o11_nav2_lifecycle.sh \
  root@192.168.1.11:/root/rober/onboard/scripts/o11_nav2_lifecycle.sh
```

如修改 bringup package，使用现有 board sync/build 入口或在 `tech-done.md` 写明 board 侧未同步原因和影响。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_on_configure_io_order_repair.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_on_configure_io_order_repair.raw.json \
  sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/artifacts/live_o10_map_server_on_configure_io_order_repair.raw.json
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
  sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair
```

Planning 阶段验收命令：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|map_server_configure_return_failure_before_deferred_map_read_completed|strict no-motion|robot-software-engineer|升级 CEO|lifecycle clean/active" \
  sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/pre_start.md \
  sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/prd.md \
  sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/tech-plan.md
```

```bash
git diff --check -- sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair
```

## 验收判定

Accept：

- true-board artifact 证明 `/map_server` lifecycle clean/active；或
- true-board artifact 输出比 `map_server_configure_return_failure_before_deferred_map_read_completed` 更窄且可执行的 root cause。
- no-motion 字段全部保持 false。
- `tech-done.md` 记录实际改动、验证结果、失败定位和剩余风险。
- docs 同步 proof boundary。

Needs retry：

- artifact 仍只输出完全相同 `map_server_configure_return_failure_before_deferred_map_read_completed`，没有更窄分类或新 evidence。
- primary blocker 是 cleanup/LiDAR/AMCL/TF/noise，而不是 map_server configure/root cause。
- 没有 true-board artifact。
- docs 或 sprint `tech-done.md` 未记录 proof boundary。

Reject：

- 发送 NavigateToPose。
- 发布 `/cmd_vel`。
- 调用 `/api/base/manual`。
- 打开 WAVE ROVER UART。
- 改硬件配置或未读 vendor 资料就假设硬件事实。

## 风险边界

- `/map_server` lifecycle clean/active 只证明 map server lifecycle 前置条件改善，不证明 `/map` sample、AMCL pose、dynamic `map->odom`、planner path、route execution、delivery、HIL、safe-to-control 或 production external evidence。
- 如果 true-board SSH 不可达，本轮只能记录 environment blocker，不能用 local artifact 替代 true-board proof。
- 如果本轮结束仍是同一句 root cause 且无更窄 evidence，必须触发同一 Blocker 红线：`needs retry`，然后 `升级 CEO` 或切换 Objective。

## 后续文档要求

Robot Software 实施完成后必须更新：

- `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/tech-done.md`
- `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/artifacts/`

Product 验收阶段再更新：

- `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/side2side_check.md`
- `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/final.md`
