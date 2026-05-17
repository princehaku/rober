# Sprint 2026.05.17_20-21 Wave Rover Feedback Replay Gate - Tech Done

sprint_type: epic

## 1. 实际改动

本轮按 `tech-plan.md` 完成三条 Engineer 交付链，并由 Product 做 closeout。证据边界固定为 `software_proof_docker_wave_rover_feedback_replay_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Task A - hardware-engineer：

- 新增 dependency-free PC gate：`pc-tools/evidence/wave_rover_feedback_replay_gate.py`。
- 新增测试与 fixtures：`pc-tools/evidence/test_wave_rover_feedback_replay_gate.py`、`pc-tools/evidence/fixtures/wave_rover_feedback_replay/`。
- 新增硬件文档：`docs/hardware/wave_rover_feedback_replay_gate.md`。
- 已复读并采用本地 vendor 来源：`docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、`docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`、`docs/hardware/wave_rover_json_bridge.md`。

Task B - robot-software-engineer：

- 在 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py` 新增 `wave_rover_feedback_replay` / `_summary` diagnostics metadata-only consumer。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 覆盖 fail-closed 与只读 summary 消费。
- 更新 `docs/interfaces/ros_contracts.md`，同步 Robot diagnostics 合同。

Task C - full-stack-software-engineer：

- 在 `mobile/web/app.js` 新增 WAVE ROVER feedback replay 只读 panel。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json` 和 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`，说明手机端只展示 replay verdict、interval summary、topic alignment、next required evidence 和边界 flags。

Task D - product-okr-owner：

- 创建本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。Objective 1 仅按 HIL-prep replay gate software proof 保守上调；Objective 5 保持约 68%。

## 2. 验证结果

Engineer 已报告并由 Product closeout 记录的任务级验证：

- Task A：`python3 -m py_compile ...` pass；`python3 -m unittest pc-tools/evidence/test_wave_rover_feedback_replay_gate.py` 输出 `Ran 7 tests OK`；CLI `--help` pass；required `rg` pass；scoped `git diff --check` pass；happy fixture 输出 `overall_status=ready_for_hil_review_not_proven`；failure fixture 对 evidence_ref mismatch 以 exit 2 blocked。
- Task B：`python3 -m py_compile ...` pass；diagnostics unittest 输出 `Ran 158 tests OK`；required `rg` pass；scoped `git diff --check` pass。
- Task C：mobile unittest 输出 `Ran 54 tests OK`；`node --check mobile/web/app.js` pass；required `rg` pass；scoped `git diff --check` pass。

Product closeout 还必须运行 sprint 要求的整体验收命令；最终结果记录在 `final.md`。

## 3. 偏差和边界

- 本轮没有真实 WAVE ROVER、真实 UART、真实串口日志、真实 `feedback_T1001.log`、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 HIL 或 `hil_pass`。
- 本轮没有真实 2D LiDAR / ToF SKU、source、receipt、采购、安装、接线、电源、标定或 HIL-entry 材料。
- 本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。
- PC gate 的 fixture pass 只证明 replay / interval / topic-alignment 软件围栏可执行，不证明真实底盘反馈稳定。

## 4. 剩余风险

- 未来真实 HIL packet 必须包含同一 `evidence_ref` 的 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`，否则 gate 应继续 blocked / `not_proven`。
- Robot diagnostics 和 mobile/web 已有 metadata-only 消费面，但真实 ROS topic timing、feedback interval、IMU、电池、电机轮速仍需上车实测。
- Objective 5 仍受外部材料阻塞；按 stop rule，不应继续用本地 metadata depth 伪装 production proof。
