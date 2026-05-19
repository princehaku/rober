# Sprint 2026.05.20_03-04 PR5 Vendor Source Review Packet - Tech Done

## 1. Sprint 类型和证据边界

- sprint_type: epic
- Sprint 主题：`pr5_vendor_source_review_packet`
- 证据边界：`software_proof_docker_pr5_vendor_source_review_packet_gate`
- 固定边界：`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`
- 本轮只证明 repo-local / Docker-only vendor/source review packet、Robot safe alias 和 mobile/web 只读展示；不证明真实 2D LiDAR / ToF 采购、source、receipt、安装、接线、电源、标定、HIL-entry、真实手机/browser、O5 external proof、route/elevator field pass 或 delivery success。

## 2. 实际改动

### Hardware Infra Engineer

- `pc-tools/evidence/pr5_vendor_source_review_packet.py`：新增 PR #5 vendor/source review packet gate，读取本地 `docs/vendor/` source boundary 和 product hardware boundary，输出 artifact 与 summary。
- `tests/test_pr5_vendor_source_review_packet.py`：覆盖 vendor index required、packet status、missing materials、unsafe success/control claim blocking 和 fail-closed copy。
- `docs/interfaces/pr5_vendor_source_review_packet.md`：记录 `trashbot.pr5_vendor_source_review_packet.v1` 与 summary schema、source boundary、missing materials 和不证明事项。
- `docs/product/production_hardware_boundary.md`：同步 PR #5 vendor/source review packet 边界，明确 local vendor tree 不证明 2D LiDAR / ToF 真实材料。
- `sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/evidence/pr5_vendor_source_review_packet.json` 与 `pr5_vendor_source_review_packet_summary.json`：生成 review-ready artifact，status 为 `ready_for_pr5_vendor_source_review_packet_not_proven`。

Vendor sources read:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`

Source conclusion：local vendor tree proves source boundary for Orange Pi, WAVE ROVER, UART JSON, firmware/vendor app references；does not prove project 2D LiDAR / ToF SKU/procurement/install/wiring/power/calibration/HIL/field pass/delivery success。

### Robot Platform Engineer

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：新增 `robot_diagnostics_pr5_vendor_source_review_packet_summary`，schema 为 `trashbot.robot_diagnostics_pr5_vendor_source_review_packet_summary.v1`，只消费 sanitized Hardware summary。
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：新增 safe alias 测试，覆盖缺失、unsupported、raw body、serial/UART/ROS/control/ACK/cursor/success/HIL/field-pass claim 的 fail-closed 处理。
- `docs/interfaces/operator_gateway_diagnostics.md` 与 `docs/interfaces/ros_contracts.md`：同步 Robot diagnostics contract，保留 read-only / metadata-only 边界。

Robot fail-closed defaults：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

### User Touchpoint Full-Stack Engineer

- `mobile/web/app.js`：在手机端只读展示 `robot_diagnostics_pr5_vendor_source_review_packet_summary`、`PRRT_kwDOSWB9286CJ3tX`、`software_proof/not_proven` 和中文安全文案。
- `mobile/web/styles.css`：补齐 review packet panel 的只读状态样式。
- `mobile/web/test_mobile_web_entrypoint.py`：新增 fixture、DOM copy、fail-closed gating、unsafe wording 和 no control side-effect 断言。
- `mobile/web/fixtures/robot_diagnostics_pr5_vendor_source_review_packet_summary.json`：新增 Robot safe summary fixture。
- `docs/product/mobile_user_flow.md`：同步手机端 PR #5 vendor/source review packet 用户可见边界。

No new endpoint, ACK, cursor, retry, or control side effect；Start Delivery / Confirm Dropoff / Cancel remains fail-closed。

### Product Manager / OKR Owner

- `OKR.md`：更新 4.1 latest sprint 为 `2026.05.20_03-04_pr5-vendor-source-review-packet`；Objective 5 保持约 68%，Objective 1 保持约 81%，Objective 4 保持约 99%。
- `docs/process/okr_progress_log.md`：追加本 sprint 进度条目、rerank 依据、验证结果和证据边界。
- 本文件、`side2side_check.md`、`final.md`：整理三位 Engineer 结果、Product closeout、remaining risks 和 scoped integration validation。

## 3. 验证结果

### Hardware Infra Engineer

- `test -f docs/vendor/VENDOR_INDEX.md`：通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/pr5_vendor_source_review_packet.py`：通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_pr5_vendor_source_review_packet.py`：`Ran 5 tests ... OK`。
- `python3 pc-tools/evidence/pr5_vendor_source_review_packet.py --output sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/evidence/pr5_vendor_source_review_packet.json --summary-output sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/evidence/pr5_vendor_source_review_packet_summary.json`：生成 artifact，status 为 `ready_for_pr5_vendor_source_review_packet_not_proven`。
- Required `rg` 与 scoped `git diff --check`：通过。

### Robot Platform Engineer

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 219 tests ... OK`。
- Required `rg` 与 scoped `git diff --check`：通过。

### User Touchpoint Full-Stack Engineer

- `PYTHONDONTWRITEBYTECODE=1 python3 mobile/web/test_mobile_web_entrypoint.py`：`Ran 147 tests in 0.906s OK`。
- `node --check mobile/web/app.js`：exit 0。
- Required `rg` 与 scoped `git diff --check`：通过。

### Product / Integration

- Product evidence coverage `rg`：复跑通过，覆盖 sprint type、Objective 5、Objective 1、`PRRT_kwDOSWB9286CJ3tX`、proof boundary、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 和 `OKR 最低优先级核对`。
- Integration scope `git diff --check`：复跑通过。
- Staged `git diff --cached --check`：复跑通过。

## 4. 偏差和修复

- Hardware 首轮 unsafe scanner 过度匹配 fail-closed examples 和 `/dev/tty*` examples；已收窄到 product/review copy，并保留 affirmative success/control claim blocking。
- Robot 首轮测试期望 missing summary 时 `thread_id` 保留在 blocked output；已修复。另一个 raw flag 名称包含 `raw_artifact_body`，已移除，避免把 raw body 入口暴露为允许字段。
- Full-Stack 未新增 endpoint、ACK、cursor、retry 或控制副作用，保持只读展示。

## 5. 剩余风险

- `PRRT_kwDOSWB9286CJ3tX` 仍只能写成 review-ready / still `not_proven`；未自动 resolved。
- 仍缺真实 2D LiDAR / ToF SKU、source、receipt、procurement、installation、wiring、power、calibration、HIL-entry 和 field evidence。
- 仍缺真实 WAVE ROVER/UART/HIL、真实 phone/browser、Objective 5 external proof、route/elevator field pass、dropoff/cancel completion 和 delivery success。
