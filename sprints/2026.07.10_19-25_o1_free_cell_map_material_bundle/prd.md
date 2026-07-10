# O1 Free-Cell Map Material Bundle PRD

## 用户价值和产品北极星

普通用户最终需要的是机器人能沿可靠地图和路线安全送垃圾。对当前 O1 来说，用户价值不是再证明“有一个地图文件”，而是把同一现场 run 中已经修复 free cell 的地图材料变成可回归、可脱敏、可 fail-closed 的 O1 material summary。

本 sprint 的产品北极星是“证据链服务真实执行”。这次计划必须把下一步落到 Hardware owner 可执行命令和可验证产物：扩展 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，消费 33-38 free-cell materials。

## 背景和问题

上一轮 O1 bundle 已把 2026-06-22 同 run 的 motion、feedback、LiDAR delta、operator report 和两组 map outputs 接入当前软件合同，但只消费到：

- `22_field_first_jog_map.yaml`
- `23_field_first_jog_map.pgm`
- `24_field_first_jog_map_pixel_review.json`
- `30_manual_motion_map.yaml`
- `31_manual_motion_map.pgm`
- `32_manual_motion_map_pixel_review.json`

这两组 pixel review 均为 `has_free_cells=false`，所以上一轮正确保守地输出 `map_navigation_ready=false`。

同一目录后续还有 free-cell fix 材料：

- `33_pc_map_start_after_free_pixel_fix.json`：map lifecycle start after fix。
- `34_pc_map_list_after_free_pixel_fix.json`：`map_quality_summary.status=has_usable_map`、`usable_map_count=1`、`map_usable_for_navigation=true`。
- `35_fixed_free_cells_map.yaml`：引用 `fixed_free_cells_20260622_0112.pgm`。
- `36_fixed_free_cells_map.pgm`：free-cell fixed PGM。
- `37_fixed_free_cells_map_pixel_review.json`：`free_pixel_count=394`、`has_free_cells=true`。
- `38_pc_summary_after_map_fix.json`：PC summary 读到 map once / AMCL / localization 等只读状态，同时安全控制仍锁住。

这些材料能补上“上一轮地图材料没有 free cells”的明确缺口，但仍不足以证明 current live HIL 或送达成功。

## OKR 映射和方向判断

- O1：继续。目标是补强硬件协议可信底盘的 field material chain，把 free-cell map material 纳入现有 O1 bundle。
- O5：暂停本轮计分推进。O5 仍最低但缺真实 external production evidence，上一轮已 `okr_credit_allowed=false`；继续 O5 support-only 不产生 OKR 增量。
- O6/O7：不进入本轮范围。本轮只生成 O1 hardware bundle 材料，不做 archive/readback/UI 消费。

方向判断：调整到 O1。原因是本轮能消费新同 run field material 33-38，而不是重复上一轮 historical wrapper；同时 O5 没有真实 production 输入，继续做 readiness surface 会违反 artifact-delta gate。

## KR 拆解、更新或历史归档

- KR 拆解：
  - 读取并安全汇总 free-cell map lifecycle、map list、YAML/PGM、pixel review 和 PC summary。
  - 将 free-cell material 和上一轮 motion/map bundle 统一到现有 schema 的 additive summary。
  - 保留全部 false safety fields。
  - 增加正向和负向测试，证明 394 free pixels、has usable map、dangerous true 和 unsafe leak 处理。
- KR 更新：planning 阶段不更新 OKR 百分比。
- 历史归档：planning 阶段无已完成 KR，不归档。

## 本轮核心抓手

扩展 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，不是新增一个 review 文档、handoff、checklist 或面板。产品目标是让 Hardware owner 在实现后能输出类似：

- `status=motion_map_hil_material_bundle_ready_not_hil_pass`
- `free_cell_map_material_present=true`
- `free_cell_pixel_count=394`
- `free_cell_has_free_cells=true`
- `map_navigation_material_ready=true`
- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

`map_navigation_material_ready=true` 的产品含义必须限定为“free-cell map material ready for later localization/path proof”，不是“导航已成功”。

## 需要做什么

1. Product planning 创建 epic sprint 三文档。
2. Hardware owner 后续扩展现有 bundle 默认输入路径，加入 33-38 free-cell map group。
3. Hardware owner 实现 allowlisted safe summary，只输出 basename、counts、status、blocked reasons、next evidence 和 fixed false fields。
4. Hardware owner 增加单测和 CLI smoke，覆盖 positive 33-38、缺 artifact、pixel review mismatch、unsafe path/url/token/raw/base64/traceback、不允许 dangerous true。
5. Hardware owner 同步 `docs/hardware/wave_rover_motion_map_hil_material_bundle.md` 与 `tech-done.md`。
6. Product closeout 后再更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

## 优先级和验收口径

优先级：P0，本轮自动化只做 planning，下一步交给 Hardware owner。

Planning 验收口径：

- `pre_start.md`、`prd.md`、`tech-plan.md` 存在。
- 文档含 `sprint_type: epic`。
- `tech-plan.md` 含 `OKR 最低优先级核对`。
- 明确 O5 不继续 support-only 的原因。
- 明确本轮消费 33-38 free-cell materials，是新同 run field material，不是重复上一轮 `22-24` / `30-32`。
- 明确 `394`、`has_usable_map`、`robot-hardware-engineer` 和 `software_proof_o1_motion_map_hil_material_bundle_only`。

后续 implementation 验收口径：

- Positive summary 消费 33-38 并输出 `free_cell_pixel_count=394`。
- `map_navigation_material_ready=true` 只在 free-cell material 完整、安全、同 run 时出现。
- 所有 safety / production / delivery flags 仍为 false。
- Negative 输入必须 fail-closed，且不回显 URL、token、absolute path、raw frame、base64、traceback 或设备敏感上下文。
- 测试、CLI smoke、scoped `git diff --check` 通过。

## 对应责任 Engineer

- 后续主责：`robot-hardware-engineer`
- Product owner：`product-okr-owner`
- 其他 Engineer：本轮不需要并行。若后续要把材料接入 O6/O7 archive/readback/UI，再另起跨 owner sprint。

## 风险、阻塞和需要补齐的证据链

- 本轮材料来自历史同 run，不是 current live HIL。
- Free-cell map material 可证明地图 artifact quality improved，但不能证明 Nav2 route execution。
- `38_pc_summary_after_map_fix.json` 含 runtime endpoint / path 类原始上下文，实现只能消费安全投影，不能回显原始 URL 或绝对路径。
- 仍缺 wheel direction、IMU/battery calibration、HIL acceptance、operator/external current observation、delivery result 和 production cloud。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

- 已完成 KR：无。
- 历史记录位置：无，planning 阶段不移动 KR。
- 证据来源：
  - `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md`
  - `sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle/final.md`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/33_pc_map_start_after_free_pixel_fix.json`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/34_pc_map_list_after_free_pixel_fix.json`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/35_fixed_free_cells_map.yaml`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/36_fixed_free_cells_map.pgm`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/37_fixed_free_cells_map_pixel_review.json`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/38_pc_summary_after_map_fix.json`
- 剩余风险：这些证据只支持 software-proof material intake，不支持当前 live HIL pass、safe-to-control 或 delivery success。

## 需要创建或更新的 sprint 文档

本轮创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 implementation 后更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

`OKR.md` 和 `docs/process/okr_progress_log.md` 等到收口阶段再更新。
