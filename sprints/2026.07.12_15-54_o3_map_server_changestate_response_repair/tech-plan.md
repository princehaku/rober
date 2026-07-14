# Tech Plan - O3 Map Server ChangeState Response Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target: repair `/map_server` lifecycle clean/active or narrow `map_server_changestate_response_failure_after_image_load_before_map_read_completed` under strict no-motion

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1/当前最高优先级显示最低 Objective 是 O5，约 `85%`；O1/O6/O7 约 `93%`。
2. 本 sprint 不直接针对 O5。
3. 原因：O5 当前缺真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence；继续 support-only packet、review、handoff、readiness wrapper 或 surface 不允许计主 OKR 增量。
4. 本 sprint 选择 O3/O1 strict no-motion，因为 14:54 accepted artifact 已把 true-board blocker 收敛到 `/map_server` image load 后、map read 完成前的 ChangeState failure；这是 current same-run path generation、Nav2 route execution 和后续 delivery evidence 的前置条件。
5. 本轮 OKR 百分比默认不调整；只有出现 same-run path generation、route execution、current live HIL、delivery/operator acceptance 或 production external evidence 才考虑调整。

## 上轮证据输入

最新 accepted sprint：`sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/`。

Primary live artifact：`sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/artifacts/live_o10_map_server_on_configure_io_order_repair.raw.json`。

已知事实：

- `status=blocked_with_root_cause`
- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `proof.managed_runtime_started=true`
- `proof.map_server_active=false`
- `proof.amcl_active=false`
- `proof.root_causes[0].layer=Nav2 map_server transition callback`
- `proof.root_causes[0].reason=map_server_changestate_response_failure_after_image_load_before_map_read_completed`
- `proof.root_causes[0].detail=lifecycle_manager_changestate_response_failure_after_image_load_before_map_read_completed`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_changestate_response_failure_after_image_load_before_map_read_completed`
- `transition_sequence.configure.lifecycle_manager_configure_requested=true`
- `transition_sequence.configure.map_server_configure_callback_log_observed=true`
- `transition_sequence.configure.yaml_load_started=true`
- `transition_sequence.configure.image_load_started=true`
- `transition_sequence.configure.state_change_failed=true`
- `transition_sequence.configure.state_change_failed_after_image_load_before_map_read_completed=true`
- `transition_sequence.configure.map_read_completed=true`
- `transition_sequence.event_timestamps_s.image_load_started=1783840650.5605125`
- `transition_sequence.event_timestamps_s.state_change_failed=1783840650.660171`
- `transition_sequence.event_timestamps_s.map_read_completed=1783840651.0017402`
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

- 13:54：`map_server_configure_return_failure_before_deferred_map_read_completed`。
- 14:54：`map_server_changestate_response_failure_after_image_load_before_map_read_completed`。
- 本轮允许继续，因为 root cause 已从 generic configure/map-read ordering 下钻到 image load 后、map read 完成前的 ChangeState response failure。
- 本轮必须继续推进到 `/map_server` lifecycle clean/active，或比 `map_server_changestate_response_failure_after_image_load_before_map_read_completed` 更窄。
- 若本轮仍完全重复同一句 root cause 且没有更窄 evidence，验收标记 `needs retry`；若 retry 后仍无法推进，下一步必须 `升级 CEO` 或切换 Objective，不接受继续包装同一 blocker。

## 技术方案

Robot Software 单 owner 闭环。

实施建议路径：

1. 确认 local helper 与 true-board 脚本版本一致，避免旧脚本影响 conclusion。
2. 检查 runtime log window、service summary、process summary 是否来自同一 managed runtime 启动窗口，继续排除 cleanup tail。
3. 增加或修复 map_server configure 证据：
   - `on_configure` callback exception 或 return false 迹象
   - map yaml/image load、map decode/map read、publisher 初始化、callback return 的 ordering
   - process alive/exit code、stderr exception、lifecycle state before/after configure
   - lifecycle manager ChangeState request/response timing、success flag、service timeout/error
   - executor starvation 或 service future 未完成迹象
4. 如发现 map read actually completed 后转入 AMCL configure failure，应把 primary 改为 AMCL takeover 分类，不再归因于 map_server image-load window。
5. 若能修复 launch/parameter/timing bug，优先修复并 true-board strict no-motion 重跑。
6. 若不能修复，artifact 必须输出更窄 canonical classification，例如：
   - `map_server_on_configure_exception`
   - `map_server_on_configure_return_false_after_image_load`
   - `map_server_on_configure_return_false_after_map_read`
   - `map_server_map_io_completion_after_changestate_failure`
   - `map_server_map_io_blocked_before_configure_return`
   - `lifecycle_manager_changestate_response_false_without_exception`
   - `map_server_change_state_rpc_timeout_or_error`
   - `map_server_executor_starvation_before_configure_response`
   - `map_server_process_exited_during_on_configure`
   - `map_server_parameter_invalid_during_configure`
   - `amcl_configure_failure_after_map_server_configure_completed`
7. 如果 `/map_server` lifecycle clean/active，才允许读取 `/map` sample、AMCL lifecycle readback 和 dynamic `map->odom` readiness；仍不得进入 NavigateToPose、route execution、`/cmd_vel`、`/api/base/manual` 或 WAVE ROVER UART。

## Robot Software 文件范围

允许 `robot-software-engineer` 改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/src/ros2_trashbot_bringup/launch/`
- `onboard/src/ros2_trashbot_bringup/CMakeLists.txt`，仅当 launch/install 入口事实需要修复
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `onboard/src/ros2_trashbot_bringup/test/`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/tech-done.md`
- `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/artifacts/`

不得改动：

- WAVE ROVER、ESP32、UART、串口、波特率、接线或硬件配置。
- `OKR.md`
- `docs/process/okr_progress_log.md`
- O5/O6/O7 API/UI/archive 代码。
- 历史 sprint 目录。

## 接口影响

允许影响：

- `o10_amcl_nav2_runtime_proof.py` 增加 additive proof fields，记录 map_server `on_configure`、map IO ordering、ChangeState response、executor timing、process/exception、参数/AMCL takeover 证据。
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
  --output-json sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/artifacts/local_o10_map_server_changestate_response_repair.raw.json
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
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_changestate_response_repair.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_changestate_response_repair.raw.json \
  sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/artifacts/live_o10_map_server_changestate_response_repair.raw.json
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
  sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair
```

Planning 阶段验收命令：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|map_server_changestate_response_failure_after_image_load_before_map_read_completed|strict no-motion" \
  sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/pre_start.md \
  sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/prd.md \
  sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/tech-plan.md
```

```bash
git diff --check -- \
  sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair
```

## 风险边界

- 本轮仍可能停留在 `/map_server` lifecycle not active；只有更窄 root cause 或 clean/active readback 才算推进。
- true-board 访问、ROS graph、daemon、LiDAR serial 噪声可能影响采样；primary 判断必须来自同一 managed runtime 窗口。
- 如果硬件串口、LiDAR 接线、波特率或 WAVE ROVER 成为 primary root cause，必须停止本 owner 继续推断，转 Hardware 并读取 `docs/vendor/VENDOR_INDEX.md`。
