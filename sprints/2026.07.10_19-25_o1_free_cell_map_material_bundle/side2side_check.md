# O1 Free-Cell Map Material Bundle Side-to-Side Check

## sprint_type

sprint_type: epic

## Product 验收结论

验收通过。本 sprint 的产品结果是把同一 2026-06-22 field run 中的 free-cell map materials 33-38 接入 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，形成可复验、可脱敏、可 fail-closed 的 O1 material summary。

本轮可以给 O1 一个保守增量：O1 从约 88% 调整到约 89%。该增量来自新的 historical same-run free-cell map material intake，不是 review、handoff、checklist、同层 wrapper 或 support-only surface。

## Side-to-Side 核对

| 核对项 | Planning 口径 | Hardware 实际结果 | Product 判断 |
| --- | --- | --- | --- |
| 目标材料 | 消费同 run artifacts 33-38 | 已接入 33-38 free-cell lifecycle/list/YAML/PGM/pixel review/PC summary | 通过 |
| 合同 | 继续使用 `trashbot.wave_rover_motion_map_hil_material_bundle.v1` | 未新增误导性成功 schema，仍输出 `motion_map_hil_material_bundle_ready_not_hil_pass` | 通过 |
| Free-cell 摘要 | `free_cell_pixel_count=394`、`free_cell_has_free_cells=true` | positive output 包含 `free_cell_pixel_count=394`、`free_cell_has_free_cells=true`、`free_cell_usable_map_count=1` | 通过 |
| Material readiness | `map_navigation_material_ready=true` 只表示 material ready | positive output 包含 `map_navigation_material_ready=true`，同时 `map_navigation_ready=false` | 通过 |
| 安全字段 | 固定 false | `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` | 通过 |
| 负向验证 | free-cell pixel mismatch fail-closed | negative smoke exit 4，命中 `free_cell_pixel_count_not_394` | 通过 |

## OKR 最低优先级复核

O5 仍是当前最低 Objective，约 85%。但 `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已把 O5 标成 `okr_credit_allowed=false`，原因是缺真实 external production evidence。没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 或真实 phone/browser 时，继续 O5 只能产生 support-only readiness 守护。

本轮转 O1 的理由仍成立：O1 有新的 historical same-run free-cell field material 33-38，且 Hardware implementation 确实消费了这些材料并产出 `map_navigation_material_ready=true`。这不是 current live HIL，也不是 delivery success，但比上一轮 `has_free_cells=false` 的地图材料有明确 artifact delta。

## 验证证据

- `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py`：pass。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'`：`Ran 16 tests in 0.051s OK`。
- Positive CLI：exit 0，含 `free_cell_map_material_present=true`、`free_cell_pixel_count=394`、`map_navigation_material_ready=true`。
- Negative free-cell pixel review smoke：exit 4，含 `free_cell_pixel_count_not_394`。
- Hardware scoped `git diff --check`：pass。

## 不能宣称的事项

- 不证明 current live HIL。
- 不证明 safe-to-control。
- 不证明 delivery success。
- 不证明 wheel direction。
- 不证明 IMU/battery calibration。
- 不证明 Nav2 route execution success。
- 不证明 current live map navigation readiness。
- 不证明 production cloud。

## 剩余风险

下一轮 O1 必须补 current same-run `feedback_T1001.log`、motion command record、operator / external motion observation、HIL acceptance record，并把本轮 free-cell material 接到 current live localization/path proof。否则 O1 只能停留在 historical same-run material intake。
