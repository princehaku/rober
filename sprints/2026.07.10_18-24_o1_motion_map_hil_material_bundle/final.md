# O1 Motion Map HIL Material Bundle Final

## sprint_type

sprint_type: epic

## Product 收口结论

本 sprint 收口为 `software_proof_o1_motion_map_hil_material_bundle_only`。Hardware owner 完成 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`：成包消费历史 first jog command、feedback sample、LiDAR scan delta、operator report、field/manual map output 与 pixel review，输出 `motion_map_hil_material_bundle_ready_not_hil_pass`。

本轮可以给 O1 一个保守增量：O1 从约 87% 上调到约 88%。这次增量来自“消费历史现场 motion + feedback + LiDAR delta + map material 并形成单一 fail-closed bundle”，不是 current live HIL pass，也不是 wrapper、review、handoff、checklist 或同层 readback。O5 保持约 85%，O6/O7 保持约 91%。本轮不归档 KR。

## 证据

- 输入材料：`sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/10_pc_first_jog_for_scan_delta.json`、`12_pc_feedback_samples_after_scan_delta_jog.json`、`14_scan_delta_metrics.json`、`18_operator_report_lidar_delta_response.json`、`22-24` 与 `30-32` map / pixel review artifacts
- 合同：`trashbot.wave_rover_motion_map_hil_material_bundle.v1`
- ready status：`motion_map_hil_material_bundle_ready_not_hil_pass`
- 核心摘要：`same_run_material_present=true`、`map_output_present=true`、`map_navigation_ready=false`
- fail-closed 负例：negative CLI exit `4`，`blocked_reasons=["feedback_all_samples_not_t1001"]`
- 固定安全边界：`hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`
- Hardware 验证：`py_compile` 通过；`python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'` 输出 `Ran 10 tests in 0.017s OK`；positive CLI exit `0`；negative CLI exit `4`；scoped `git diff --check` 通过

## Product 验证结果

- `test -f side2side_check.md && test -f final.md && test -f artifacts/product_worker_report.md`：exit 0，无输出。
- `rg -n "motion_map_hil_material_bundle|software_proof_o1_motion_map_hil_material_bundle_only|约 88%|Ran 10 tests|map_navigation_ready=false|feedback_all_samples_not_t1001|current live HIL|O5" ...`：exit 0；关键命中包括 `OKR.md` 当前进度约 88%、4.1 O1 `~88%`、`docs/process/okr_progress_log.md` 顶部 18-24 收口，以及本 sprint `final.md` / `side2side_check.md` / `artifacts/product_worker_report.md`。
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle`：exit 0，无输出。

## 用户价值和北极星

用户价值是把 O1 历史现场 motion + map 材料变成一个当前可复验的 bundle，让后续 current live HIL 执行可以直接对照缺口，而不是继续人工解释散落 artifact。产品北极星仍是“安全、可验证的垃圾送达”；本轮只推进底盘可信证据链，不声称送达闭环完成。

## OKR 方向判断

- O1：继续推进，当前上调到约 88%。
- O5：保持约 85%，因为上一轮 O5 `okr_credit_allowed=false`，当前仍无真实 external production evidence。
- O6/O7：保持约 91%，下一步必须消费 live route execution、delivery record、operator acceptance 或 production cloud readback。
- 已完成 KR：本轮无 KR 归档，无历史区移动。

## 风险和未完成事项

- 不是 current live HIL。
- 不是 safe-to-control。
- 不是 delivery success。
- 不证明 wheel direction。
- 不证明 IMU/battery calibration。
- 不证明 usable navigation map。
- 不证明 production cloud。
- 下一轮 O1 必须采 current same-run `feedback_T1001.log`、motion command record、operator / external motion observation、HIL acceptance record，以及带 free cells 的 current live route map。

## 需要更新的文档

- `OKR.md`：O1 当前进度与 4.1 快照更新到约 88%，不归档 KR。
- `docs/process/okr_progress_log.md`：顶部新增本 sprint 证据和边界。
- `side2side_check.md`：记录 Product side-to-side 验收。
- `artifacts/product_worker_report.md`：记录 Product worker closeout 与验证命令。
