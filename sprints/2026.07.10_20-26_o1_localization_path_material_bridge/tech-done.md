# O1 Localization Path Material Bridge Tech Done

## sprint_type

sprint_type: epic

## 已读资料和 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

采用的 vendor 事实没有新增硬件假设：WAVE ROVER 上下位机链路仍按 UTF-8 JSON line、`T=1` 左右轮速度命令、`T=130` 反馈请求、`T=1001` 底盘反馈处理。本轮只扩展 historical artifact safe summary，不改串口、波特率、launch 默认值、速度映射、固件或控制命令。

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
  - 扩展 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，新增 `localization_path_material_bridge` 摘要。
  - 从 `38_pc_summary_after_map_fix.json` allowlist 消费 `status`、`map_proof_latest`、`localize_proof_latest`、`nav2_status`、`nav2_proof_latest`。
  - 输出 `same_run_map_once_observed=true`、`same_run_amcl_pose_observed=true`、TF `map_to_odom=true` / `map_to_base_link=true`，并固定 `same_run_path_generation_succeeded=false`、`same_run_path_generated=false`、`same_run_path_point_count=0`、`same_run_path_proven=false`。
  - 固定安全字段：`hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`。
  - 安全消费 June 11 clean-baseline path artifacts 作为 `cross_run_clean_baseline_*` comparator，`path_point_count=31` 只作为 cross-run 对照，不覆盖 same-run 字段。
  - 增加 fail-closed：`38` 缺失、schema mismatch、required readback 缺失、TF JSON parse 失败、TF 不完整、same-run path 被篡改为成功、dangerous true、allowlist 消费字段出现 URL/path/token/traceback/base64/baudrate 等都会 blocked。
  - 主会话验收后补强 endpoint `key_values` 的 optional dangerous false 检查：`robot_control_executed`、`hil_pass`、`nav2_route_execution_success`、`same_run_path_proven`、`wheel_feedback_lr_nonzero_proven`、`real_route_map_proven` 缺失不误杀正例，但出现且不是 `false` 会 blocked。
  - 补强 comparator：`latest_result.primary_actions_enabled` 缺失不误杀正例，出现且不是 `false` 会禁用 `cross_run_clean_baseline_*` comparator。
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
  - 新增/更新 positive、missing endpoint、TF JSON parse failure、TF incomplete、same-run path success tamper、unsafe consumed value、dangerous true、cross-run comparator 断言。
  - 主会话验收后新增 endpoint `key_values.robot_control_executed/nav2_route_execution_success=true` blocked 回归，以及 comparator `latest_result.primary_actions_enabled=true` blocked 回归。
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
  - 同步 localization/path bridge 合同、fail-closed 规则、cross-run comparator 边界和 next evidence。
- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/tech-done.md`
  - 记录本轮实现、验证、边界和风险。

## 验证结果

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py
```

结果：通过，无输出。

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
```

结果：

```text
Ran 24 tests in 0.104s
OK
```

```bash
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
```

结果：exit `0`，输出 `status=motion_map_hil_material_bundle_ready_not_hil_pass`、`proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`、`localization_path_material_bridge_present=true`、`same_run_path_generation_requested=true`、`same_run_path_generation_succeeded=false`、`same_run_path_generated=false`、`same_run_path_point_count=0`、`same_run_path_proven=false`、`cross_run_clean_baseline_path_summary.path_point_count=31`、`hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`，且 `blocked_reasons=[]`。

```bash
rg -n "localization_path_material_bridge|same_run_path_proven|path_point_count|software_proof_o1_motion_map_hil_material_bundle_only" onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_20-26_o1_localization_path_material_bridge
```

结果：通过，命中实现、测试、hardware 文档和 sprint 文档中的新合同字段。

```bash
git diff --check -- onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_20-26_o1_localization_path_material_bridge
```

结果：通过，无输出。

## 失败定位

主会话验收发现 `_endpoint_key_values()` 只检查 endpoint `key_values` 内的 `safe_to_control`、`delivery_success`、`primary_actions_enabled`，没有覆盖 `robot_control_executed`、`hil_pass`、`nav2_route_execution_success`、`same_run_path_proven` 等 optional dangerous 字段。修复后这些字段缺失不影响正例，出现且不是 `false` 会进入 `blocked_reasons`。

Comparator 侧同步补了 `latest_result.primary_actions_enabled` 的 optional false 检查。该字段为 `true` 时只禁用 `cross_run_clean_baseline_*` comparator，不覆盖 same-run localization/path bridge。

修复后的指定验证命令均通过。没有遗留失败。

## 证据边界

本轮 proof boundary 是 historical same-run software proof only：

- 证明 2026-06-22 historical same-run `38_pc_summary_after_map_fix.json` 的 localization/path readback 已被当前软件安全 intake。
- 证明 same-run localization readiness material 存在：map once、AMCL pose、TF map-to-odom / map-to-base-link。
- 证明 same-run path 仍未成功：`path_generation_succeeded=false`、`path_generated=false`、`path_point_count=0`、`same_run_path_proven=false`。
- June 11 `path_point_count=31` 只是 cross-run comparator。

不证明 current live HIL、safe-to-control、delivery success、Nav2 route execution success、current live path generation success、轮向确认、IMU/battery 标定、production cloud 或真实上车送达。

## 剩余风险和下一步

- 仍缺 current live same-run `feedback_T1001.log`、motion command record、operator/external observation、HIL acceptance record。
- 仍缺 current live same-run Nav2 path generation success 和 Nav2 route execution success。
- 后续若要给 O6/O7/PC UI 消费该 bridge，需要另起跨 owner sprint 接 archive/readback/UI，不应在本 O1 hardware bundle 内扩散。
