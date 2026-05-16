# Sprint 2026.05.16_18-19 Hardware Sensor HIL-entry Config Precheck - Tech Done

sprint_type: epic

## 1. 实际改动

本轮按 4 owner epic sprint 完成 A/B/C/D 分工，核心 contract 为 `trashbot.hardware_sensor_hil_entry_config_precheck.v1` / `trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1`，证据边界固定为 `software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate`。

Task A Hardware 已完成：

- 新增 `pc-tools/evidence/hardware_sensor_hil_entry_config_precheck_gate.py`。
- 新增 `pc-tools/evidence/test_hardware_sensor_hil_entry_config_precheck_gate.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/product/production_hardware_boundary.md`。
- 已读取 vendor source：`docs/vendor/VENDOR_INDEX.md`、WAVE ROVER `config.yaml`、`base_ctrl.py`、`json_cmd.h`。
- Gate 检查 future HIL-entry sensor config 的 sensor count、thresholds、frame IDs、safety policy、evidence refs 与 vendor/source boundary，并对缺失、unsupported、unsafe、success claim、弱 boundary fail closed。

Task B Robot 已完成：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 新增 `hardware_sensor_hil_entry_config_precheck` metadata-only diagnostics consumer，支持 explicit ref、env、latest_status、diagnostics nested summary。
- 对缺失 summary、unsupported schema、unsafe 字段、success claim、弱 evidence boundary fail closed，不改变 collect/dropoff/cancel 授权。

Task C Full-stack 已完成：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/web/fixtures/status.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增只读“传感器 HIL 入口配置预检” panel，copy/export whitelist-only，Start / Confirm Dropoff / Cancel gating 不变。

Task D Product closeout 已完成：

- 创建本文件。
- 创建 `side2side_check.md`。
- 创建 `final.md`。
- 更新 `OKR.md` 4.1 快照。
- 更新 `docs/process/okr_progress_log.md`。

## 2. 验证结果

Task A Hardware 验证：

```text
python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_config_precheck_gate.py
pass

python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_config_precheck_gate.py
Ran 9 tests OK

python3 pc-tools/evidence/hardware_sensor_hil_entry_config_precheck_gate.py --help
pass

required rg
pass

scoped git diff --check
pass
```

Task B Robot 验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass

python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 108 tests in 0.114s OK

required rg
pass

scoped git diff --check
pass
```

Task C Full-stack 验证：

```text
python3 -m unittest mobile.web.test_mobile_web_entrypoint
Ran 10 tests in 0.019s OK

node --check mobile/web/app.js
pass

required rg
pass

scoped git diff --check
pass
```

Task D Product closeout 验证：

```text
rg -n "hardware_sensor_hil_entry_config_precheck|software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate|Objective 5|Docker|not_proven|delivery_success=false|primary_actions_enabled=false|PR #5" OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck
pass; matched OKR.md, docs/process/okr_progress_log.md, pre_start.md, prd.md, tech-plan.md, tech-done.md, side2side_check.md, and final.md

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/tech-done.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/side2side_check.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/final.md
pass; no output
```

## 3. 失败定位

A/B/C worker 返回的最终验证均通过。Product closeout 首轮验收通过；未发现需要修复的失败。

## 4. 剩余风险

- 本轮是 `software_proof` only，状态必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不证明真实 WAVE ROVER/UART/HIL，不证明真实 2D LiDAR / ToF 采购、安装、接线、供电、标定或 HIL-entry。
- 不证明真实手机/browser、production app、真实 PWA prompt/user choice。
- 不证明 Objective 5 external proof；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- 后续若要提升硬件或 O5 实证完成度，必须补真实外部材料，不能复用本轮 software proof 文档当作现场通过证据。
