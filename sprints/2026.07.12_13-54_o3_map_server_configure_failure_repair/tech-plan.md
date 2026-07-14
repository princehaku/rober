# Tech Plan - O3 Map Server Configure Failure Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/`
- Owner: `robot-software-engineer`
- Product owner: `product-okr-owner`
- Target: repair or further narrow true-board `/map_server` configure failure under strict no-motion

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1/当前最高优先级显示最低 Objective 是 O5，约 `85%`；O1/O6/O7 约 `93%`。
2. 本 sprint 不直接针对 O5。
3. 原因：O5 当前缺真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence；继续 support-only packet/readback/wrapper 不允许计主 OKR 增量。本轮选择 O3/O1 strict no-motion，是为了打通 current same-run path generation 与 Nav2 route execution 的 `/map_server` lifecycle 前置 blocker。
4. 本轮 OKR 百分比默认不调整；只有出现 same-run path generation、route execution、current live HIL、delivery/operator acceptance 或 production external evidence 才考虑调整。

## 上轮证据输入

最新 accepted sprint：`sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/`。

关键 artifact：`sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/artifacts/live_o10_map_server_transition_callback_probe.raw.json`。

已知事实：

- `status=blocked_with_root_cause`
- `proof.root_causes[0].layer=Nav2 map_server transition callback`
- `proof.root_causes[0].reason=map_server_configure_callback_return_failure`
- `proof.root_causes[0].detail=lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_configure_callback_return_failure`
- `transition_sequence.observed_stage=configure`
- `transition_sequence.configure.lifecycle_manager_requested=true`
- `transition_sequence.configure.map_server_callback_entered=true`
- `transition_sequence.configure.yaml_load_started=true`
- `transition_sequence.configure.image_load_started=true`
- `transition_sequence.configure.map_read_completed=true`
- `transition_sequence.configure.state_change_failed=true`
- `service_rpc_timing.inferred_change_state_response=failure`
- `bond_timing.bond_stage=not_created_before_configure_return_failure`
- `process_status.managed_runtime_started=true`
- `process_status.process_alive_before_cleanup=true`
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

- 11-54：`map_server_activate_callback_failed` after valid map readback。
- 12-55：`map_server_configure_callback_return_failure` with ChangeState inferred failure before bond creation。
- 本轮允许继续，因为 blocker 已下钻到 configure callback / lifecycle RPC 层。
- 若本轮仍完全停在同一句 `map_server_configure_callback_return_failure` 且没有更窄参数、异常、map IO、RPC、executor 或 bond evidence，下一轮必须升级 CEO 决策或切 Objective。

## 技术方案

Robot Software 单 owner 闭环。

实施建议路径：

1. 检查 `o10_amcl_nav2_runtime_proof.py` 对 map_server configure 日志、state transition、process status、lifecycle readback 和 cleanup 噪声的解析，确保当前 primary 不被 stale/noise 覆盖。
2. 检查 `o11_nav2_lifecycle.sh` 与 `ros2_trashbot_bringup` launch 中 map_server、map yaml、lifecycle manager、namespace、service timeout、bond timeout、use_sim_time、RMW env、executor 启动顺序与参数。
3. 若有明显配置或启动顺序问题，优先修复并在 true-board strict no-motion 重跑。
4. 若不能修复，扩展 artifact 字段，记录更窄分类：
   - `map_server_configure_parameter_invalid`
   - `map_server_configure_map_io_exception`
   - `map_server_configure_callback_exception`
   - `map_server_change_state_response_failure_detail`
   - `map_server_change_state_rpc_timeout_or_error`
   - `map_server_executor_starvation_before_configure_response`
   - `map_server_bond_prerequisite_not_reached`
   - `map_server_process_exited_during_configure`
   - `map_server_configure_return_failure_after_map_read_completed`
5. 如果 `/map_server` clean/active，才允许继续读取 `/map` sample、AMCL pose 和 dynamic `map->odom`；仍不得进入 NavigateToPose、`/cmd_vel`、`/api/base/manual` 或 WAVE ROVER UART。

## 允许文件范围

Robot Software 允许改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/src/ros2_trashbot_bringup/launch/`
- `onboard/src/ros2_trashbot_bringup/CMakeLists.txt`，仅当 launch/install 入口事实需要修复
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `onboard/src/ros2_trashbot_bringup/test/`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/tech-done.md`
- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/`

不得改动：

- WAVE ROVER、ESP32、UART、串口、波特率、接线、硬件配置。
- `OKR.md`
- `docs/process/okr_progress_log.md`
- O5/O6/O7 API/UI/archive 代码。
- 历史 sprint 目录。

## 接口影响

允许影响：

- `o10_amcl_nav2_runtime_proof.py` 增加 additive proof fields，记录 map_server configure repair/root-cause detail。
- no-motion helper 可修复 lifecycle/readback/log parsing、map_server launch 参数或 lifecycle manager timing。
- navigation docs 同步新的 proof boundary。

禁止影响：

- 不改变 `/cmd_vel`、`/api/base/manual`、WAVE ROVER UART 或底盘控制入口。
- 不执行 NavigateToPose 或 Nav2 route execution。
- 不把 lifecycle active 自动转成 `safe_to_control=true`。
- 不改变 O5/O6/O7 合同。

## 验收命令

Robot Software 必须运行并记录以下命令。若 true-board 命令参数需要调整，必须把实际命令、返回码、stdout/stderr 摘要和 artifact 字段写入 `tech-done.md`。

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

如修改 bringup launch 或 lifecycle script，追加对应检查：

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
  --output-json sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/local_o10_map_server_configure_failure_repair.raw.json
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
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_configure_failure_repair.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_configure_failure_repair.raw.json \
  sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/live_o10_map_server_configure_failure_repair.raw.json
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
  sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair
```

Planning 阶段验收命令：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|map_server_configure_callback_return_failure|strict no-motion|robot-software-engineer" sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/pre_start.md sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/prd.md sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/tech-plan.md
```

```bash
git diff --check -- sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair
```

## 验收判定

Accept：

- true-board artifact 证明 `/map_server` lifecycle clean/active；或
- true-board artifact 输出比 `map_server_configure_callback_return_failure` 更窄且可执行的 root cause。
- no-motion 字段全部 false。
- `tech-done.md` 记录实际改动、验证结果、失败定位和剩余风险。
- docs 同步 proof boundary。

Needs retry：

- artifact 仍只输出完全相同 `map_server_configure_callback_return_failure`，没有更窄分类或新 evidence。
- primary blocker 是 cleanup/LiDAR/AMCL/TF/noise，而不是 map_server configure/root cause。
- docs 或 sprint `tech-done.md` 未记录 proof boundary。

Reject：

- 发送 NavigateToPose。
- 发布 `/cmd_vel`。
- 调用 `/api/base/manual`。
- 打开 WAVE ROVER UART。
- 改硬件配置或未读 vendor 资料就假设硬件事实。

## 后续文档要求

Robot Software 实施完成后必须更新：

- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/tech-done.md`

Product 验收阶段再更新：

- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/side2side_check.md`
- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/final.md`
