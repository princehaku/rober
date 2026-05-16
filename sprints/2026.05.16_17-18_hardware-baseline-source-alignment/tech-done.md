# Sprint 2026.05.16_17-18 Hardware Baseline Source Alignment - Tech Done

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：让普通用户、现场支持和工程同学看到同一份硬件基线事实：默认硬件集是什么、目标传感器基线是什么、哪些只来自 vendor/source coverage、哪些仍缺真实采购/安装/接线/标定/HIL 材料。

产品北极星：把 `rober` 做成普通手机用户可理解、可诊断、可低成本量产的 ROS2 送垃圾机器人。本轮不追求真实硬件通过，而是先消除硬件基线口径漂移，避免后续采购、bringup、Robot diagnostics 和 mobile/web 对同一硬件缺口给出不同解释。

## 2. OKR 映射与 KR 更新

- Objective 1：硬件协议可信底盘。PR #5 review 指出的默认硬件集与 mandatory sensor baseline 矛盾、传感器假设缺少 `docs/vendor/` source attribution，已经被转成 `hardware_baseline_source_alignment` software proof、Robot diagnostics metadata-only consumer 和 mobile/web 只读展示；Objective 1 从约 73% 保守上调到约 74%。
- Objective 4：手机用户体验与低成本量产边界。手机端现在能用 phone-safe copy 展示默认硬件集、目标传感器基线、vendor/source boundary、缺失材料和 fail-closed 控制边界；Objective 4 从约 86% 保守上调到约 87%。
- Objective 5：云中转 + OSS/CDN 数据通路产品化。当前仍缺真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 worker/migration；本轮没有新增外部 O5 材料，保持约 66%。

KR 拆解：

- O1 KR source discipline：硬件假设必须可追溯到 `docs/vendor/VENDOR_INDEX.md` 或明确写为 product target pending validation。
- O1 KR HIL-entry readiness：2D LiDAR / ToF 不再被误写成已采购、已安装、已接线、已标定或 HIL-ready。
- O4 KR phone-safe diagnostics：mobile/web 只读展示硬件基线来源对齐摘要，Start / Confirm Dropoff / Cancel gating 不变。

## 3. 本轮核心抓手与责任 Engineer

- Task A Hardware Infra Engineer：新增 `pc-tools/evidence/hardware_baseline_source_alignment_gate.py` 和单元测试，更新 `pc-tools/README.md`、`docs/product/production_hardware_boundary.md`，输出 `trashbot.hardware_baseline_source_alignment.v1` / summary v1，边界为 `software_proof_docker_hardware_baseline_source_alignment_gate`。
- Task B Robot Platform Engineer：更新 `operator_gateway_diagnostics.py`、diagnostics 单测和 `docs/interfaces/ros_contracts.md`，新增 metadata-only consumer，透传 `default_hardware_set_summary`、`target_sensor_baseline_summary`、`vendor_source_boundary`、`missing_alignment_items`。
- Task C User Touchpoint Full-Stack Engineer：更新 `mobile/web/app.js`、`styles.css`、`fixtures/status.json`、`test_mobile_web_entrypoint.py`、`docs/product/mobile_user_flow.md`，新增“硬件基线来源对齐”只读 panel，copy/export whitelist-only。
- Task D Product Manager / OKR Owner：收口 sprint 留档、`OKR.md` 4.1 和 `docs/process/okr_progress_log.md`。

## 4. 实际改动与验证结果

Task A 验证：

- `py_compile` passed。
- `python3 -m unittest pc-tools/evidence/test_hardware_baseline_source_alignment_gate.py`：`Ran 5 tests in 0.005s OK`。
- CLI `--help` passed。
- required `rg` passed。
- scoped `git diff --check` passed。
- 额外 `--once-json` live docs 输出 `overall_status=hardware_baseline_source_aligned_not_proven`、`missing_alignment_items=[]`、`delivery_success=false`、`primary_actions_enabled=false`。
- 已读来源：`AGENTS.md`、`docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`、`docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`。

Task B 验证：

- `py_compile` passed。
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 106 tests in 0.117s OK`。
- required `rg` passed。
- scoped `git diff --check` passed。
- 失败定位：中间一次 unittest 因旧断言全局禁止 WAVE ROVER，已改成只在 unsafe blocked summary 限制 raw hardware detail。

Task C 验证：

- `python3 -m unittest mobile.web.test_mobile_web_entrypoint`：`Ran 8 tests ... OK`。
- `node --check mobile/web/app.js` passed。
- required `rg` passed。
- scoped `git diff --check` passed。

Task D 本文件收口后验证见 `final.md`。

## 5. 验收口径

本轮验收通过的范围是：PC gate、Robot diagnostics 和 mobile/web 均能围绕 `hardware_baseline_source_alignment` 给出一致的 phone-safe/source-safe 摘要，并保持 `software_proof_docker_hardware_baseline_source_alignment_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

本轮明确不证明：真实 HIL、真实 WAVE ROVER/UART/Orange Pi 串口、`T=1001` feedback、真实 2D LiDAR / ToF 采购/安装/接线/供电/标定、真实 Nav2/fixed-route、真实 route/elevator field pass、真实 dropoff/cancel completion、delivery success、真实手机设备/browser、production app 或 Objective 5 external proof。

## 6. 风险、阻塞和证据链

- O5 仍是数值最低 Objective，但下一步有效进展需要真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration，Docker-only 本地链路不能继续堆 O5 completion。
- O1 上调只来自硬件基线 source-alignment 软件证明，不来自实机硬件运行。
- O4 上调只来自 phone-safe 只读展示，不来自真实手机设备或生产 app 验收。
- 后续真实补证仍需要同一 `evidence_ref` 下的采购/source/receipt、安装/接线/供电、标定、HIL entry、route/elevator field materials 和实机日志。
