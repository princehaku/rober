# Sprint 2026.05.17_02-03 Hardware Sensor HIL-entry Readiness Review - Tech Done

sprint_type: epic

## 1. 用户价值和产品北极星

本轮把 PR #5 暴露的硬件材料边界继续推进到“传感器 HIL 准入评审”：普通手机用户不需要理解 vendor 文档、UART、JSON、frame ID 或阈值，但现场支持必须能判断 2D LiDAR / ToF 材料和配置是否足够进入下一步 HIL-entry 人工评审。

产品北极星保持不变：低成本、可追溯、手机用户可用的 ROS2 自主垃圾投递机器人。硬件目标不能被写成已采购、已安装、已接线、已标定或已 HIL 的事实。

## 2. OKR 映射和 KR 拆解

- Objective 1：把 receipt intake 与 HIL-entry config precheck 合成为可审查的 readiness review，补齐进入真实 HIL 前的材料评审入口。
- Objective 4：让 mobile/web 用只读、phone-safe panel 解释 readiness status、missing materials、next required evidence 和安全边界。
- Objective 5：仍是数值最低 Objective，但本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 证据，保持约 66%。

KR 拆解：

- Hardware：新增 dependency-free PC gate，输出 `trashbot.hardware_sensor_hil_entry_readiness_review.v1` 与 summary。
- Robot：新增 diagnostics metadata-only consumer，只透传白名单摘要并 fail closed。
- Full-stack：新增 mobile/web 只读“传感器 HIL 准入评审” panel，保持主操作 gating 不变。
- Product：完成 sprint closeout、OKR 更新和进展日志更新，保守声明证据边界。

## 3. 实际改动

Task A Hardware worker 完成：

- 新增 `pc-tools/evidence/hardware_sensor_hil_entry_readiness_review_gate.py`。
- 新增 `pc-tools/evidence/test_hardware_sensor_hil_entry_readiness_review_gate.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/product/production_hardware_boundary.md`。
- 读取并采用的 vendor/source boundary：`AGENTS.md`、`docs/vendor/VENDOR_INDEX.md`、`base_ctrl.py`、`config.yaml`、`json_cmd.h`、`uart_ctrl.h`。

Task B Robot worker 完成：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 新增 `hardware_sensor_hil_entry_readiness_review` / `_summary` diagnostics metadata-only consumer，支持 explicit ref、latest_status.diagnostics 和环境变量输入。

Task C Full-stack worker 完成：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/web/fixtures/status.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增只读“传感器 HIL 准入评审” panel，兼容 status、phone_readiness、diagnostics 与 nested summary。

Product closeout 本轮更新：

- `sprints/2026.05.17_02-03_hardware-sensor-hil-entry-readiness-review/tech-done.md`
- `sprints/2026.05.17_02-03_hardware-sensor-hil-entry-readiness-review/side2side_check.md`
- `sprints/2026.05.17_02-03_hardware-sensor-hil-entry-readiness-review/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 4. 验证结果

Task A Hardware worker 报告：

```text
python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_readiness_review_gate.py
PASS

python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_readiness_review_gate.py
Ran 8 tests OK

python3 pc-tools/evidence/hardware_sensor_hil_entry_readiness_review_gate.py --help
PASS

required rg
PASS

scoped git diff --check
PASS
```

Task B Robot worker 报告：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
exit 0

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 124 tests in 0.166s OK

required rg
PASS

scoped git diff --check
PASS
```

Task C Full-stack worker 报告：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
26 tests OK

node --check mobile/web/app.js
PASS

required rg
PASS

scoped git diff --check
PASS
```

首轮敏感词围栏失败已由 Full-stack worker 修复并复验通过。

Product closeout 验收命令在 closeout 后执行，结果记录在 `final.md`。

## 5. 偏差和失败定位

- 无未修复验证失败。
- Full-stack 首轮敏感词围栏失败的根因是 mobile/web 展示面泄露了不该进入 phone-safe copy 的敏感或过宽字段；worker 已收敛为白名单摘要，过滤 raw vendor docs、raw JSON、serial/UART、绝对路径、凭证和 complete artifacts。
- 本轮没有运行真实硬件、真实串口、真实 HIL、真实手机设备、真实 Nav2/fixed-route 或 Objective 5 外部云验证；这是预期边界，不是工程验证失败。

## 6. 证据边界和剩余风险

本轮证据边界是 `software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate`。它证明当前 repo 能把 receipt intake 与 HIL-entry config precheck 汇总为 fail-closed readiness review，并由 Robot diagnostics 与 mobile/web 只读消费。

本轮不证明：

- 真实 2D LiDAR / ToF 已采购、已收货、已安装、已接线、已供电、已标定或已进入 HIL。
- 真实 WAVE ROVER、Orange Pi 串口、UART JSON feedback、`T=1001`、`/odom`、`/imu/data`、`/battery` 或 `hil_pass`。
- 真实 Nav2/fixed-route、route/elevator field pass、dropoff/cancel completion 或 delivery success。
- 真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- Objective 5 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。

必须继续保持：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
