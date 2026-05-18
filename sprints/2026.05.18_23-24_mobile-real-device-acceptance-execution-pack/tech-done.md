# Sprint 2026.05.18_23-24 Mobile Real Device Acceptance Execution Pack - Tech Done

## 1. Sprint 声明

- sprint_type: epic
- closeout owner：Product Manager / OKR Owner
- 完成时间：2026-05-18 23:19 Asia/Shanghai
- 证据边界：`software_proof_docker_mobile_real_device_field_trial_acceptance_execution_pack_gate`
- 安全边界：`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`

## 2. 实际改动

### Owner A：User Touchpoint Full-Stack Engineer

- 修改 `mobile/web/app.js`，新增 `mobile_real_device_field_trial_acceptance_execution_pack*` 手机端只读 panel，位置接在“现场验收复核交接”后。
- 修改 `mobile/fixtures/mobile_web_status.fixture.json`，补充 execution pack fixture / summary / copy。
- 修改 `mobile/web/test_mobile_web_entrypoint.py`，覆盖 execution pack panel、safe copy、安全字段和主操作 gating 不变。
- 修改 `docs/product/mobile_user_flow.md`，同步真实手机现场验收执行包的用户流程和不证明事项。

实现结果：execution pack 消费 `mobile_real_device_field_trial_acceptance_review_handoff*` safe summary / copy，生成 owner checklist、evidence capture steps、redaction requirements、rerun commands、`next_required_evidence` 和 safe copy。手机端只读展示，不改变 Start Delivery、Confirm Dropoff、Cancel gating。

### Owner B：Robot Platform Engineer

- 修改 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`，新增 `mobile_real_device_field_trial_acceptance_execution_pack`、`mobile_real_device_field_trial_acceptance_execution_pack_summary` 和 `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_pack_summary`。
- 修改 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`，覆盖 explicit ref、env、latest_status、nested diagnostics summary、白名单过滤和 fail-closed 行为。
- 修改 `docs/interfaces/ros_contracts.md`，同步 Robot diagnostics safe alias、字段来源和边界。

实现结果：Robot diagnostics 只复制白名单字段，不触发 collect、dropoff、cancel、ACK、cursor、Nav2、HIL 或 robot command。

### Owner D：Hardware Infra Engineer

- 只读核对 `docs/vendor/VENDOR_INDEX.md`、`docs/product/production_hardware_boundary.md` 和 WAVE ROVER vendor sources。
- 结论：当前 repo 没有真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料；WAVE ROVER vendor app 中通用 lidar 示例不能证明本项目 2D LiDAR / ToF 已采购或安装。
- 无硬件配置、driver、launch 或 vendor 文件改动。

### Owner C：Product Manager / OKR Owner

- 创建本文件、`side2side_check.md`、`final.md`。
- 保守更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，把最新 sprint 从 handoff 推进到 execution pack。
- Objective 4 保持约 99%；Objective 5 保持约 68%；Objective 1 保持约 81%；Objective 2 / Objective 3 保持约 99%。

## 3. 验证结果

### Owner A 验证

```text
node --check mobile/web/app.js
# pass

python3 -m unittest mobile.web.test_mobile_web_entrypoint
# Ran 98 tests ... OK

rg execution-pack contracts
# pass

git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
# pass
```

### Owner B 验证

```text
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
# Ran 190 tests in 0.425s OK

rg diagnostics execution-pack contracts
# pass

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
# pass
```

### Product closeout 集成围栏

Product closeout 复跑以下命令，结果记录在 `final.md`：

```text
node --check mobile/web/app.js
python3 -m unittest mobile.web.test_mobile_web_entrypoint
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
test -f tech-done.md && test -f side2side_check.md && test -f final.md
rg execution-pack / evidence-boundary contracts
git diff --check scoped files
```

## 4. 偏差和失败定位

- 未发现需要修复的 closeout blocker。
- 本轮没有真实手机、真实 iPhone/Android、production app、PWA prompt/user choice、真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、delivery success、WAVE ROVER/UART/HIL 或 O5 external proof。
- Hardware 只读核对确认 PR #5 2D LiDAR / ToF 真实材料仍缺，不在本轮解决。

## 5. 剩余风险

- execution pack 只能降低现场 owner 采集真实手机材料的遗漏风险，不能替代真实现场验收。
- 下一轮若要推动 Objective 4 从约 99% 进入真实完成，需要带同一 safe `evidence_ref` 回填真实 iPhone/Android device behavior、production app 或 PWA prompt/user choice 证据。
- Objective 5 仍需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover；本轮不应消耗 O5 blocker。
- Objective 1 和 PR #5 仍需要真实 WAVE ROVER/UART/HIL、2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
