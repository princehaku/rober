# Sprint 2026.05.18_23-24 Mobile Real Device Acceptance Execution Pack - Final

## 1. Sprint 结果

本轮完成 `mobile_real_device_field_trial_acceptance_execution_pack*` 的 Objective 4 software proof closeout。Full-stack 把上一轮真实手机验收复核交接推进为手机端只读 execution pack；Robot diagnostics 暴露同一 safe summary alias；Product closeout 更新 sprint 留档、`OKR.md` 和 `docs/process/okr_progress_log.md`。

证据边界固定为：`software_proof_docker_mobile_real_device_field_trial_acceptance_execution_pack_gate`。本轮保持 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 用户价值和产品北极星

北极星仍是让普通手机用户不接触命令行、ROS2、串口、云凭证或硬件调试，也能理解任务状态和异常下一步。本轮向这个目标推进了一层：现场 owner 现在能拿到可执行的真实手机验收包，知道要采集什么、如何打码、如何复跑和哪些证据仍不足。

本轮不是用户验收通过，也不是 production app 完成；它是把真实手机验收从 handoff 变成 execution package。

## 3. OKR 映射和 KR 收口

- Objective 4：保守保持约 99%。本地 software-proof 链路从 `mobile_real_device_field_trial_acceptance_review_handoff*` 推进到 `mobile_real_device_field_trial_acceptance_execution_pack*`，但仍未取得真实 iPhone/Android、production app、PWA prompt/user choice 或现场验收通过。
- Objective 5：保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。
- Objective 1：保持约 81%。本轮没有真实 WAVE ROVER、UART、HIL、底盘反馈、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 或 PR #5 2D LiDAR / ToF 真实材料。
- Objective 2 / Objective 3：保持约 99%。本轮不证明真实 route/elevator field pass、Nav2/fixed-route、route completion signal、task record、dropoff/cancel completion、delivery result 或 delivery success。

KR 收口：

- KR-A：execution pack fields 已由 Owner A 完成，包含 owner checklist、evidence capture steps、redaction requirements、rerun commands、`next_required_evidence` 和 safe copy。
- KR-B：mobile/web 只读 panel 已完成，主操作 gating 不变。
- KR-C：Robot diagnostics safe alias 已完成，白名单 fail-closed。
- KR-D：`docs/product/mobile_user_flow.md` 与 `docs/interfaces/ros_contracts.md` 已由对应 owner 同步。
- KR-E：Product closeout 已保守更新 sprint 文档、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 4. OKR 最低优先级核对回顾

`tech-plan.md` 写明 Objective 5 数字最低（约 68%），但下一步必须依赖真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof；当前 Docker-only 主机没有这些材料。这个理由在收口时仍成立，因此本轮不推进 O5 completion，也不重复新增本地 O5 metadata。

Objective 1 次低（约 81%），但需要真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 2D LiDAR / ToF 真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。Owner D 只读核对后确认这些材料仍缺，因此不把本轮 O4 execution pack 写成 O1 进度。

Objective 4 仍是本轮最可执行 fallback：在没有 O5/O1/PR #4 真实材料时，把 handoff packet 推进为真实手机验收 execution package，给下一轮真实手机材料回填建立可执行入口。

## 5. 验证命令结果

```text
$ node --check mobile/web/app.js
# exit 0

$ python3 -m unittest mobile.web.test_mobile_web_entrypoint
# Ran 98 tests in 0.602s
# OK

$ PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
# Ran 190 tests in 0.461s
# OK

$ test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/tech-done.md && test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/side2side_check.md && test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/final.md
# exit 0

$ rg -n "mobile_real_device_field_trial_acceptance_execution_pack|source=software_proof|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" mobile/web mobile/fixtures onboard/src/ros2_trashbot_behavior docs/product docs/interfaces sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack OKR.md docs/process/okr_progress_log.md
# exit 0

$ rg -n "Objective 5|Objective 1|Objective 4|PR #4|PR #5|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack OKR.md docs/process/okr_progress_log.md
# exit 0

$ git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack OKR.md docs/process/okr_progress_log.md
# exit 0
```

## 6. 不证明事项和剩余风险

本轮明确不证明：真实手机 / iPhone / Android、production app、PWA prompt/user choice、真实 route/elevator field pass、Nav2/fixed-route、WAVE ROVER/UART/HIL、dropoff/cancel completion、delivery success、Objective 5 external proof、PR #5 2D LiDAR / ToF real materials。

剩余风险：

- Objective 4 的下一步必须拿真实手机现场材料，不能继续用本地 execution pack 自证通过。
- Objective 5 仍需真实外部云/4G/OSS/CDN/DB/queue 证据。
- Objective 1 和 PR #5 仍需真实硬件材料与上车 HIL。
- PR #4 route/elevator 仍需真实门状态、楼层确认、人工协助、Nav2/fixed-route runtime log、task record、dropoff/cancel 或 delivery result。

## 7. 下一步建议

下一轮优先带这个 execution pack 到真实 iPhone/Android 或 production app / PWA prompt/user choice 场景采集同一 safe `evidence_ref` 的材料。若真实手机仍不可用，应不要继续堆 O4 本地 wrapper，改按 `OKR.md` 4.1 重新 rerank：O5 需要 external proof，O1/PR #5 需要真实硬件材料，PR #4 需要真实 route/elevator materials。
