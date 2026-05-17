# Sprint 2026.05.17_09-10 Route Task Field Retest Callback Intake - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `route_task_field_retest_callback_intake`，把 PR #4 route/elevator field material 链路从“证据包已派发”推进到“现场 sanitized callback 已可回填”。PC gate、Robot diagnostics 和 mobile/web 都围绕同一 `evidence_ref` 消费 metadata-only summary，并保持：

- `software_proof_docker_route_task_field_retest_callback_intake_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮是 Docker-only software proof。它证明 callback intake 链路可生成、消费、展示、fail closed，不证明真实 route/elevator field pass、Nav2/fixed-route runtime、task record、door/floor/human assistance material、dropoff/cancel completion、delivery success、HIL、真实手机/browser、Objective 5 external proof 或 PR #5 2D LiDAR / ToF material proof。

## 2. Worker 结果核对

Task A Autonomy：

- 新增 `pc-tools/evidence/route_task_field_retest_callback_intake.py` 与测试。
- 更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`。
- 验证通过：py_compile、unittest `Ran 5 tests in 0.066s OK`、CLI `--help`、required `rg` 243 matches、scoped `git diff --check`。
- 已修复：缺材料时不能采信 callback 的 "send to result intake"，强制转为 `collect_missing_materials_then_rerun_result_intake`。

Task B Robot：

- 更新 `operator_gateway_diagnostics.py`、diagnostics tests、`docs/interfaces/ros_contracts.md`。
- 验证通过：py_compile、unittest `Ran 140 tests in 0.208s OK`、required `rg`、scoped `git diff --check`。
- 已修复：env summary wrapper 误读 `robot_compatible_summary` 导致 `safe_evidence_ref` 丢失。

Task C Full-stack：

- 更新 `mobile/web/app.js`、`mobile/web/styles.css`、mobile fixture/test、`docs/product/mobile_user_flow.md`。
- 验证通过：mobile unittest `Ran 36 tests in 0.092s OK`、`node --check mobile/web/app.js`、required `rg`、scoped `git diff --check`。
- 主操作 gating 未改变，仍不新增 Start / Confirm / Cancel / ACK / cursor / robot command 请求。

Task D Product：

- 创建本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 当前快照、第 6 节最高优先级和第 7 节风险。
- 更新 `docs/process/okr_progress_log.md`。

## 3. OKR 更新

- Objective 1：保持约 77%。本轮无真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或 PR #5 2D LiDAR / ToF material proof。
- Objective 2：约 89% -> 约 90%。理由：callback intake 把 route/elevator field materials 从 evidence dispatch 推进到可接收现场回执、缺项、same-`evidence_ref` 检查和下一步回填动作。
- Objective 3：约 89% -> 约 90%。理由：Nav2/fixed-route runtime log、route completion signal、task record 的现场材料回填入口更完整，减少真实复测后错配或缺项未登记风险。
- Objective 4：保持约 99%。理由：mobile/web 只是只读支援 panel，未新增真实 iPhone/Android、production app、真实 PWA prompt/user choice 或真实现场 phone behavior。
- Objective 5：保持约 68%。理由：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或其他 external proof。

## 4. OKR 最低优先级核对回顾

当前数字最低仍是 Objective 5，约 68%。本轮没有继续 O5 local wrapper，原因仍成立：O5 下一步 completion 需要真实外部材料，包括公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser 证据。继续堆本地 O5 metadata depth 不能形成真实 external proof。

本轮也没有继续 O1 hardware wrapper。PR #5 hardware blocker 已多轮消费，仍缺真实 2D LiDAR / ToF SKU/source、receipt、采购、安装、接线、电源、标定、HIL-entry 和 field evidence；没有真实材料时继续包一层 precheck 只会重复消费同一根因 blocker。

O2/O3 callback intake 是当前 Docker-only 主机下的可执行功能前进：它承接上一轮 evidence dispatch，补齐现场人员回传 sanitized callback metadata 的入口，让 PC / Robot / mobile 能围绕同一 `evidence_ref` 看到推荐文件名收到状态、缺项和下一步回填动作，同时保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 剩余风险和下一步

- 真实 route/elevator field materials 仍需现场补齐：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- 真实手机/browser 验收仍缺：iPhone/Android device behavior、production app、真实 PWA prompt/user choice、真实现场 phone behavior。
- Objective 5 external proof 仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover。
- PR #5 2D LiDAR / ToF material proof 仍缺真实 SKU/source、receipt、采购、安装、接线、电源、标定、HIL-entry 和 field evidence。
- Git commit / push 由主会话在最终集成验收后执行，避免 Product closeout 在 A/B/C 工程范围仍未统一 staged 前提前收口。
