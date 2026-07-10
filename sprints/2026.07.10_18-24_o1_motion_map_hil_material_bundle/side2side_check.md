# O1 Motion Map HIL Material Bundle Side-to-side Check

## sprint_type

sprint_type: epic

## 验收结论

Product closeout 通过。Hardware owner 本轮确实消费了历史同 run motion / feedback / LiDAR delta / operator / map material，并把它们收敛成 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`。本轮没有把历史 bundle 误写成 current live HIL、safe-to-control、delivery success 或 usable navigation map。

## 用户价值和产品北极星

产品北极星仍是“普通用户把垃圾交给小车后，小车能安全、可验证地完成送达”。O1 本轮的用户价值是把分散的历史现场 motion + map HIL 材料整理成当前可复验、可脱敏、可 fail-closed 的 intake 合同，让团队能明确区分：

- 哪些历史现场事实已经被 bundle 消费；
- 哪些 current live HIL 证据仍然缺失；
- 哪些地图材料只证明 artifact 存在，不证明可导航。

## Side-to-side 核对

| 计划口径 | 实际证据 | Product 判断 |
| --- | --- | --- |
| 消费同一历史现场 run 的 motion / feedback / scan delta / operator / map material | 默认消费 `2026.06.22_01-35_motion_map_runtime_probe` 的 `10`、`12`、`14`、`18`、`22-24`、`30-32` | 通过，本轮有新的历史现场 material delta |
| 输出清晰 bundle 合同 | 新增 `trashbot.wave_rover_motion_map_hil_material_bundle.v1` | 通过 |
| ready status 保守命名 | positive 输出 `motion_map_hil_material_bundle_ready_not_hil_pass` | 通过，不声称 HIL pass |
| 地图边界必须写死 | positive 输出 `map_output_present=true`，同时 `map_navigation_ready=false` | 通过，没有把 pixel review `has_free_cells=false` 说成导航可用 |
| 安全字段不可被输入抬高 | 固定 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` | 通过 |
| fail-closed 负向覆盖成立 | negative CLI exit `4`，`blocked_reasons=["feedback_all_samples_not_t1001"]` | 通过 |
| 脱敏输出 | `tech-done.md` 记录正例不泄露 `source_base_url`、endpoint、`/root/...` 和 runtime 上下文 | 通过 |

## OKR 映射和方向判断

- 映射 Objective：O1 硬件协议可信底盘。
- 方向判断：继续 O1，保守上调到约 88%。
- 上调原因：本轮不是 wrapper、review、handoff 或 checklist，而是成包消费了历史现场 motion + feedback + LiDAR delta + map material。
- O5 保持约 85%，因为上一轮 O5 仍是 `okr_credit_allowed=false`，没有真实 external production evidence。
- O6/O7 保持约 91%。
- 本轮不归档 KR；O1 仍未达到 current live HIL、safe-to-control 或 delivery success 的完成条件。

## 风险和剩余证据

- 本轮不证明 current live HIL。
- 本轮不证明 safe-to-control。
- 本轮不证明 delivery success。
- 本轮不证明 wheel direction。
- 本轮不证明 IMU/battery calibration。
- 本轮不证明 usable navigation map。
- 本轮不证明 production cloud。
- 下一轮 O1 仍需 current same-run `feedback_T1001.log`、motion command record、operator / external motion observation、HIL acceptance record，以及带 free cells 的 current live route map。

## Product 验收命令

Product closeout 后运行文件存在性、关键证据 `rg` 和 scoped `git diff --check`。最终命令结果记录在 `artifacts/product_worker_report.md` 和 `final.md`。
