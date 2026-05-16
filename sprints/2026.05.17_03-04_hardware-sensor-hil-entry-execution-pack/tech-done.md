# Sprint 2026.05.17_03-04 Hardware Sensor HIL-entry Execution Pack - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `hardware_sensor_hil_entry_execution_pack` 的 PC / Robot / mobile 三端软件 proof 闭环。证据边界固定为 `software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate`，不是 HIL、真实采购、真实安装或真实手机/browser 验收。

### Hardware Infra Engineer

实际落地：

- 新增 `pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py`。
- 新增 `pc-tools/evidence/test_hardware_sensor_hil_entry_execution_pack_gate.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/product/production_hardware_boundary.md`。

产出：PC gate 将上一轮 HIL-entry readiness review 转成 fail-closed execution pack artifact/summary，包含 controlled HIL-entry manifest、material templates、first-run / rerun command summary、owner handoff 和 next required evidence。Hardware worker 已读取 `docs/vendor/VENDOR_INDEX.md`、`ugv_rpi/base_ctrl.py`、`ugv_rpi/config.yaml`、`WAVE_ROVER_V0.9/json_cmd.h`、`WAVE_ROVER_V0.9/uart_ctrl.h`，但这些只作为 WAVE ROVER / Orange Pi / UART JSON source boundary，不作为真实采购、安装、接线、标定或 HIL proof。

验证结果：

```text
python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py
PASS

python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_execution_pack_gate.py
Ran 7 tests ... OK

python3 pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py --help
PASS

required rg
PASS

git diff --check -- pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py pc-tools/evidence/test_hardware_sensor_hil_entry_execution_pack_gate.py pc-tools/README.md docs/product/production_hardware_boundary.md
PASS
```

### Robot Platform Engineer

实际落地：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。

产出：Robot diagnostics 新增 `hardware_sensor_hil_entry_execution_pack` / `_summary` metadata-only consumer，支持 explicit ref、env、latest status 和 nested diagnostics summary；unsupported schema、weak boundary、success claim、unsafe raw fields 均 fail closed。首轮 latest_status strip 和 HIL wording over-classification 已修复。本改动不触发 collect、dropoff、cancel、ACK、cursor、Nav2、HIL、route/elevator pass 或 delivery success。

验证结果：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PASS

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 126 tests ... OK

required rg
PASS

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
PASS
```

### User Touchpoint Full-Stack Engineer

实际落地：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/web/fixtures/status.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。

产出：mobile/web 新增只读“传感器 HIL 执行包” panel，消费 status、phone_readiness、diagnostics、nested summary 中的 execution pack 摘要，只展示 phone-safe 字段。Start Delivery / Confirm Dropoff / Cancel gating 不变，不展示 raw vendor docs、raw JSON、serial/UART、绝对路径、凭证、DB/queue URL、OSS AK/SK、checksums、complete artifacts 或 raw robot responses。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
28 tests OK

node --check mobile/web/app.js
PASS

required rg
PASS

git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
PASS
```

## 2. 偏差和修复

- Robot 首轮发现 latest_status strip 与 HIL wording over-classification，已由 Robot worker 修复并复验 `Ran 126 tests ... OK`。
- 本轮没有工程 worker 返回未修复的验证失败。
- Product closeout 未修改工程实现、测试或 planning docs，只更新 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 3. OKR 判断

- Objective 1：从约 76% 保守上调到约 77%。理由是 HIL-entry readiness review 已推进为执行包模板、owner handoff 与 rerun command summary，真实上车前的材料准备更可执行；但仍不是真实 WAVE ROVER、UART、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或 `hil_pass`。
- Objective 4：从约 96% 保守上调到约 97%。理由是 mobile/web 能把 HIL-entry execution pack phone-safe 可读化，现场支持可看到缺失材料、owner handoff 和下一步证据，且主操作 gating 未改变；但仍不是真实手机/browser 或 production app proof。
- Objective 2 / Objective 3：保持约 86%。本轮没有真实任务、导航、电梯、route completion signal、task record、dropoff/cancel completion 或 delivery success。
- Objective 5：保持约 66%。Objective 5 仍是数值最低，但 Docker-only 主机缺公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 等真实外部材料；本轮不是 Objective 5 external proof。

## 4. 剩余风险

- 真实 2D LiDAR / ToF SKU、vendor/source、receipt、procurement、installation、wiring、power、calibration、HIL-entry 仍缺。
- 真实 WAVE ROVER / Orange Pi 串口、UART JSON feedback、`T=1001`、`/odom`、`/imu/data`、`/battery`、`hil_pass` 仍缺。
- 真实 Nav2/fixed-route、route/elevator field pass、真实手机/browser、production app、dropoff/cancel completion、delivery success 仍缺。
- Objective 5 external proof 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- 本轮所有结果必须继续保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
