# Sprint 2026.05.17_00-01 Route Task Field Retest Material Pack - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `route_task_field_retest_material_pack` 的 PC material directory 打包校验、Robot diagnostics metadata-only 消费、mobile/web 只读“现场材料包” panel，以及 Product closeout / OKR / progress log 同步。

本轮结果是 `software_proof_docker_route_task_field_retest_material_pack_gate`，状态保持：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- Docker-only

这不是真实 field pass、真实 Nav2/fixed-route、真实电梯、HIL、真实手机/browser、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 2. 用户价值和产品北极星

用户价值：现场人员可以把一次 route/task field retest 的八类材料放进一个目录，由 PC 工具校验同一 `evidence_ref`、缺失材料、placeholder、raw path、credential 和 unsafe success phrasing，再把 sanitized summary 交给 Robot/mobile 解释。

产品北极星：把普通手机用户可理解、现场支持可复账、工程团队可追溯的低成本 ROS2 自主垃圾投递机器人继续推进到“真实现场材料可回填”的前一层。当前仍是 software proof，不替代真实路线、真实电梯、真实硬件或真实云材料。

## 3. OKR 更新摘要

- Objective 1 保持约 75%。本轮没有真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或真实 2D LiDAR / ToF 材料。
- Objective 2 从约 84% 保守更新到约 85%。理由是 material pack 把 `door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion`、`delivery_result` 前移到可打包校验、可拒绝、可补证据的入口。
- Objective 3 从约 84% 保守更新到约 85%。理由是 material pack 把 `nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record` 组织成同一 `evidence_ref` 的材料包入口，支撑后续 result intake / reconciliation。
- Objective 4 从约 93% 保守更新到约 94%。理由是 mobile/web 新增 phone-safe material pack panel，现场人员能看懂材料完整度、缺失/拒绝原因和下一步，但控制按钮授权不变。
- Objective 5 保持约 66%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料。

## 4. KR 拆解和完成情况

KR-O2-field-material：完成 software proof。

- 八类材料覆盖：完成。
- 同一 safe `evidence_ref` 校验：完成。
- 缺失、placeholder、raw path、credential、unsafe success phrasing、`delivery_success=true`、`primary_actions_enabled=true` fail closed：完成。
- 真实现场材料回填：未完成，仍需下一轮外部材料。

KR-O3-route-material：完成 software proof。

- `nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record` 进入 material pack：完成。
- 后续 result intake / reconciliation 可消费 sanitized summary：完成。
- 真实 Nav2/fixed-route 实跑：未完成。

KR-O4-phone-safe-material：完成 software proof。

- mobile/web 只读展示 material completeness、same evidence ref、八类材料状态、missing/rejected、operator next steps、boundary：完成。
- Start Delivery、Confirm Dropoff、Cancel gating 不变：完成。
- 真实手机/browser 或 production app proof：未完成。

## 5. 验收证据

Task A Autonomy：

```text
py_compile pass
unittest Ran 5 tests in 0.017s OK
CLI --help pass
required rg pass
scoped git diff --check pass
fixture dry-run: ready_for_field_retest_material_pack_not_proven; delivery_success=false; primary_actions_enabled=false
```

Task B Robot：

```text
py_compile pass
diagnostics unittest Ran 120 tests in 0.160s OK
required rg pass
scoped git diff --check pass
```

Task C Full-stack：

```text
mobile unittest Ran 22 tests in 0.047s OK
node --check mobile/web/app.js pass
required rg pass
scoped git diff --check pass
```

Task D Product Closeout：

```text
required rg pass
closeout scoped git diff --check pass
```

## 6. 风险、阻塞和证据链

- Objective 5 仍是数值最低，约 66%；但 Docker-only host 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，不能提升 O5。
- PR #4 elevator-assisted delivery 仍缺真实门状态、目标楼层确认、人工协助记录和同一 `evidence_ref` 的现场材料。
- PR #5 硬件 baseline / 2D LiDAR / ToF / vendor-source 仍缺真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 下一步若继续 O2/O3，应拿至少一组真实 `route_task_field_retest_material_pack` material directory，用同一 `evidence_ref` 跑 material pack、result intake 和 result reconciliation；如果 O5 外部材料到位，则转回 Objective 5 external proof。

## 7. 提交状态

本轮按用户指令不要提交、不要推送；当前只完成允许范围内 closeout 文档、`OKR.md` 和 `docs/process/okr_progress_log.md` 更新。
