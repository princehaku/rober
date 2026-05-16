# Sprint 2026.05.16_14-15 Hardware Sensor Procurement Execution Pack - Tech Done

sprint_type: epic

## 1. 用户价值和产品北极星

本轮把上一轮 `hardware_sensor_procurement_review_decision` 继续推进为 `hardware_sensor_procurement_execution_pack`。用户价值是让硬件 owner、现场同学和手机端支持人员能看到下一步真实 2D LiDAR / ToF 采购、安装、接线、标定和 HIL entry 需要补齐哪些材料，而不是继续从 review decision 手工翻译执行清单。

产品北极星仍是普通手机用户可理解、低成本、可验证的垃圾投递机器人；本轮只补齐量产传感器材料执行包，不打开任何真实运动或远程控制能力。

## 2. OKR 映射和 KR 拆解

- Objective 4：主推进。量产传感器材料链从 review decision 推进到可执行采购包、Robot diagnostics metadata-only consumer 和 mobile/web 首屏只读 panel。
- Objective 1：只为后续真实硬件/HIL entry 准备材料模板；没有真实 WAVE ROVER、UART、`T=1001` feedback、Orange Pi 串口或 HIL，因此不提升。
- Objective 2 / Objective 3：只为后续 route/elevator field pass 所需 2D LiDAR / ToF 材料准备前置清单；没有真实 route/elevator、Nav2/fixed-route、dropoff/cancel completion 或 delivery result，因此不提升。
- Objective 5：不推进。仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 和 production worker/migration；本轮不是 Objective 5 external proof。

KR 拆解结果：

- KR4.3 / KR4.8 / KR4.9：形成 2D LiDAR / ToF 材料执行包的 phone-safe 表达。
- KR1.x：保留真实硬件/HIL entry 缺口。
- KR2/KR3：保留真实路线和电梯现场材料缺口。
- KR5.x：保持等待真实外部云/4G/OSS/CDN/DB/queue 证据。

## 3. 本轮核心抓手和责任 Engineer

- Hardware Infra Engineer：新增 `hardware_sensor_procurement_execution_pack` PC gate，读取 vendor index 与 Waveshare sources 后确认本地 vendor 资料不证明真实 2D LiDAR / ToF；输出 `software_proof_docker_hardware_sensor_procurement_execution_pack_gate`、材料模板、owner handoff、rerun command 和 `not_proven`。
- Robot Platform Engineer：新增 diagnostics metadata-only 消费；缺失、unsupported、unsafe 均 fail closed，不触发 collect/dropoff/cancel、ACK、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery result。
- User Touchpoint Full-Stack Engineer：新增 mobile/web 首屏只读“传感器采购执行包”panel；Start / Confirm Dropoff / Cancel gating 未改变。
- Product Manager / OKR Owner：本文件、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` closeout。

## 4. 实际改动

本轮 worker 已完成的工程改动：

- Hardware：新增 `pc-tools/evidence/hardware_sensor_procurement_execution_pack_gate.py` 和对应 unittest；同步 `docs/product/production_hardware_boundary.md`。
- Robot：更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、diagnostics unittest 和 `docs/interfaces/ros_contracts.md`。
- Full-stack：更新 `mobile/web/app.js`、`mobile/web/styles.css`、`mobile/web/test_mobile_web_entrypoint.py`、`mobile/web/fixtures/status.json` 和 `docs/product/mobile_user_flow.md`。

Product closeout 改动：

- 新增本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 当前进度快照和最高优先级。
- 更新 `docs/process/okr_progress_log.md` 详细历史。

## 5. 验证结果

Worker 已回报验证：

- Hardware：`test_hardware_sensor_procurement_execution_pack_gate.py` `Ran 9 tests ... OK`；`py_compile`、CLI `--help`、required `rg`、scoped `git diff --check` 通过。
- Robot：diagnostics unittest `Ran 100 tests ... OK`；`py_compile`、required `rg`、scoped `git diff --check` 通过。
- Full-stack：mobile unittest `Ran 2 tests ... OK`；`node --check mobile/web/app.js`、required `rg`、scoped `git diff --check` 通过。

Product closeout 验证：

```bash
rg -n "hardware_sensor_procurement_execution_pack|software_proof_docker_hardware_sensor_procurement_execution_pack_gate|Objective 5|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.16_14-15_hardware-sensor-procurement-execution-pack OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_14-15_hardware-sensor-procurement-execution-pack OKR.md docs/process/okr_progress_log.md
```

结果：`rg` 命中本 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md` 中的 execution pack / Docker / Objective 5 / `not_proven` / `delivery_success=false` / `primary_actions_enabled=false` 边界；`git diff --check` 无输出，通过。

## 6. 偏差、失败定位和剩余风险

- 无 worker 回报的未修复验证失败。
- 本轮结论必须保持 `software_proof_docker_hardware_sensor_procurement_execution_pack_gate`；不能写成真实采购、真实安装、真实接线、真实标定、真实 HIL entry、真实 WAVE ROVER/UART/HIL、真实手机、真实 route/elevator、真实 dropoff/cancel completion、delivery success 或 Objective 5 external proof。
- 当前 vendor 资料只支持避免硬件猜测；不证明真实项目 2D LiDAR / ToF SKU/source/procurement。
- 剩余风险是下一轮如果没有真实 SKU、采购凭证、安装/接线照片或脱敏 HIL entry 材料，本链路仍只能继续保持 `hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
