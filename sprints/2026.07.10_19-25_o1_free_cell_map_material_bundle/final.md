# O1 Free-Cell Map Material Bundle Final

## sprint_type

sprint_type: epic

## Product 收口结论

本 sprint 收口为 `software_proof_o1_motion_map_hil_material_bundle_only`。Hardware owner 已扩展 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，消费同一 2026-06-22 field run 的 free-cell map artifacts 33-38，并产出 `free_cell_map_material_bundle` 相关安全摘要。

OKR 决策：O1 从约 88% 保守上调到约 89%。O5 保持约 85%，O6/O7 保持约 91%。本轮不归档 KR。

## 用户价值和产品北极星

用户价值是让后续 current live HIL / Nav2 localization/path proof 能直接复用“同 run 地图材料已有 free cells”这一前置证据，而不是继续停留在上一轮 `has_free_cells=false` 的地图材料结论。

产品北极星仍是普通手机用户可安全、可验证地完成垃圾送达。本轮只推进 O1 底盘/地图材料证据链，不声称送达闭环完成。

## OKR 映射和方向判断

- O1：继续，约 89%。本轮消费新的 historical same-run free-cell map material 33-38，形成可复验 material summary。
- O5：暂停计分，保持约 85%。O5 最低，但上一轮 `okr_credit_allowed=false`，且没有真实 external production evidence。
- O6/O7：保持约 91%。本轮没有新增 archive/readback/UI 消费。
- 方向判断：继续 O1，下一轮必须转 current same-run HIL acceptance 和 live localization/path proof。

## KR 拆解、更新或历史归档

- O1 KR1/KR3：补强同 run motion / feedback / map 材料链，但不证明 current live HIL。
- O1 KR4：新增 fail-closed 测试覆盖 free-cell map materials 和 negative pixel review。
- O1 KR5：未改 launch 参数、串口参数或控制模式。
- 已完成 KR：无。
- 历史归档：不移动任何 KR；当前证据仍不足以归档 O1 KR。

## 本轮核心抓手

核心抓手是把 artifacts 33-38 接入现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，而不是新增 review / handoff / checklist。核心 positive 字段为：

- `free_cell_map_material_present=true`
- `free_cell_pixel_count=394`
- `free_cell_has_free_cells=true`
- `free_cell_usable_map_count=1`
- `map_navigation_material_ready=true`

同时继续固定：

- `status=motion_map_hil_material_bundle_ready_not_hil_pass`
- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `map_navigation_ready=false`

## 验收口径和证据

- `py_compile` pass。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'` 输出 `Ran 16 tests in 0.051s OK`。
- Positive CLI exit 0，含 `free_cell_pixel_count=394`、`map_navigation_material_ready=true`。
- Negative free-cell pixel review smoke exit 4，命中 `free_cell_pixel_count_not_394`。
- Hardware scoped `git diff --check` pass。

## OKR 最低优先级复核

O5 仍是最低 Objective，约 85%。但 `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已明确 `okr_credit_allowed=false`，原因是缺真实 external production evidence。继续 O5 readiness / probe / cutover packet 只能做 support-only 守护，不能计主 OKR 增量。

本轮转 O1 是因为有新的同 run free-cell field material 33-38：`34` 显示 `has_usable_map` / `usable_map_count=1` / `map_usable_for_navigation=true`，`37` 显示 `free_pixel_count=394` / `has_free_cells=true`。Hardware implementation 已消费这些材料并用 negative smoke 证明 fail-closed。

## 风险和未完成事项

- 不是 current live HIL。
- 不是 safe-to-control。
- 不是 delivery success。
- 不证明 wheel direction。
- 不证明 IMU/battery calibration。
- 不证明 Nav2 route execution success。
- 不证明 current live map navigation readiness。
- 不证明 production cloud。
- 下一轮 O1 必须采 current same-run `feedback_T1001.log`、motion command record、operator / external motion observation、HIL acceptance record，并把 free-cell material 接到 current live localization/path proof。

## 需要更新的文档

- 已更新：`OKR.md`。
- 已更新：`docs/process/okr_progress_log.md`。
- 已创建：`side2side_check.md`。
- 已创建：`final.md`。
- 已创建：`artifacts/product_worker_report.md`。
