# Sprint 2026.05.20_12-13 Field Evidence Rerun Material Dispatch - Final

## 1. 收口结论

本轮完成 `field_evidence_rerun_material_dispatch` epic sprint：Autonomy PC gate、Robot diagnostics safe alias、mobile/web 只读 panel 和 Product closeout 口径对齐。证据边界固定为 `software_proof_docker_field_evidence_rerun_material_dispatch_gate`，固定状态为 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

这是一轮现场材料派发与复跑准备，不是现场通过。它没有提高 Objective 5 或 Objective 1，也没有把 Objective 2 / 3 / 4 写成真实 route/elevator field pass。

## 2. OKR 最低优先级核对回顾

tech-plan 中的判断仍成立：

- Objective 5 仍是数字最低项，约 68%。本轮仍没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof，因此不能继续提高 O5。
- Objective 1 仍约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending；本轮没有真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery` 或真实 2D LiDAR / ToF HIL-entry 材料，因此不能提高 O1。
- 本轮选择 O2/O3/O4 的 field-evidence rerun material dispatch 仍合理：它把真实 route/elevator/phone field evidence 缺口转成 owner work orders、rerun commands 和 callback packet requirements，避免继续堆同义本地 wrapper。

## 3. OKR 影响

| Objective | 收口判断 |
| --- | --- |
| Objective 1 | 保持约 81%。本轮不触碰硬件协议、WAVE ROVER/UART/HIL 或 PR #5 真实材料；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending。 |
| Objective 2 | 保守保持约 99%。本轮为真实送达/电梯 rerun 输出材料派发包，但不证明真实电梯、dropoff/cancel completion、delivery result 或 delivery success。 |
| Objective 3 | 保守保持约 99%。本轮要求真实 Nav2/fixed-route runtime log、route completion signal 和 field task record，但没有真实路线实跑或上车复账。 |
| Objective 4 | 保守保持约 99%。mobile/web 增加只读材料派发面板，但不是真实手机/browser、production app 或 PWA prompt/userChoice 验收。 |
| Objective 5 | 保持约 68%。本轮没有 command/status/ack、公网、4G/SIM、OSS/CDN、production DB/queue 或 external proof 新证据。 |

## 4. 验证摘要

- Autonomy：`py_compile` 通过；`python3 -m unittest tests.test_field_evidence_rerun_material_dispatch` 输出 `Ran 5 tests in 0.048s OK`；`--help`、required `rg`、scoped diff check 通过。
- Robot：`py_compile` 通过；`PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 输出 `Ran 228 tests in 0.665s OK`；required `rg`、scoped diff check 通过。
- Full-stack：`node --check mobile/web/app.js` 通过；`python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` 输出 `Ran 163 tests ... OK`；JSON checks、required `rg`、scoped diff check 通过。
- Product closeout：required file check、required `rg`、scoped `git diff --check` 通过。

## 5. 剩余风险和下一步

- 下一步必须由现场 owner 按派发包补齐真实 route completion signal、field task record、Nav2/fixed-route runtime log、电梯门/楼层/人工协助 summaries、dropoff/cancel completion、delivery result 和真实手机/browser evidence。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍需真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料；本轮不解决该 thread。
- O5 仍需真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof，不能用本轮 dispatch package 代替。
