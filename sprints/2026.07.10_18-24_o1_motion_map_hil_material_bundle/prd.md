# O1 Motion Map HIL Material Bundle PRD

## 用户价值和产品北极星

产品北极星仍是“机器人可以安全、可验证地完成垃圾收取与送达”。这轮 O1 的用户价值不是再写一个 HIL 口号，而是把已经存在的历史现场 motion + map 材料整理成当前可复验、可脱敏、可 fail-closed 的 `motion_map_hil_material_bundle` 合同。这样后续团队就能清楚区分：

- 哪些事实已经被历史现场材料补强；
- 哪些仍然只是 `software_proof_o1_motion_map_hil_material_bundle_only`；
- 哪些 current live HIL 证据还没拿到。

## OKR 映射和方向判断

- 映射 Objective：O1 硬件协议可信底盘。
- 方向判断：**继续推进 O1，暂停 O5 的新增百分比推进**。

判断理由：

1. O5 约 `85%`，仍是最低 Objective，但 `2026.07.10_17-22` final 已明确 `okr_credit_allowed=false`。
2. 当前仓库没有新的真实 external production evidence，继续做 O5 readiness/support-only 包装不应再计 OKR。
3. O1 约 `87%`，虽然不是最低，但仓库里存在尚未成包消费的历史真实现场材料：first jog command、WAVE ROVER feedback sample、LiDAR scan delta、map output/pixel review、operator report。
4. 这批材料能补强 O1 的材料链，但不会越界声称 current live HIL pass、safe-to-control、delivery success 或 usable navigation map。

## KR 拆解

本轮不归档 KR，也不修改 `OKR.md`。后续 implementation 应推进 O1 当前 KR 的材料化子项：

1. **同 run 材料消费**：读取 `10`、`12`、`14`、`18`、`22-24`、`30-32`，确认 motion / feedback / scan delta / map / operator 材料来自同一历史现场 run。
2. **合同输出**：新增 `motion_map_hil_material_bundle` 合同，建议 schema 名含 `motion_map_hil_material_bundle`，至少输出 material status、safe source refs、motion summary、feedback summary、scan delta summary、map output summary、pixel review summary、operator summary、blocked reasons、next required evidence 和固定 false safety fields。
3. **地图边界写死**：bundle 只能承认 `map_output_present=true` 与 `pixel_review_present=true`；因为 `24` 和 `32` 都是 `has_free_cells=false`，所以不得把历史地图写成“可导航地图已证明”。
4. **HIL 边界写死**：bundle 必须固定 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，并明确这不是 current live HIL pass。

## 本轮核心抓手

核心抓手是 O1 的 `motion_map_hil_material_bundle`，不是 review、handoff、面板或 checklist。`robot-hardware-engineer` 要把历史现场 run 的多类证据收束成一个单一、安全、可回归的 bundle，为下一轮真实 current live HIL 执行命令服务。

## 需要做什么

- 规划一个单 owner implementation，让 `robot-hardware-engineer` 完成：
  - bundle 生成模块或脚本；
  - 单元测试 / fixture；
  - 最小必要硬件文档同步；
  - 本 sprint `tech-done.md` 留档。
- Product / 主节点只做验收和收口，不进入代码实现。
- 本 planning 阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。

## 优先级和验收口径

- 优先级：P0。
- 验收口径：
  1. 能消费指定历史 artifact，并输出 `motion_map_hil_material_bundle`。
  2. 能从 `10` 摘要出 first jog command，从 `12` 摘要出 `T=130` / `T=1001` 反馈存在，从 `14` 摘要出 `median_abs_diff_m` / `changed_bin_ratio` / `field_pack_pass=true`。
  3. 能从 `18` 摘要出 `physical_motion_lidar_delta_proven=true`、`wheel_feedback_lr_nonzero_proven=false`、`real_route_map_proven=false`。
  4. 能从 `22-24`、`30-32` 摘要出 map output 存在，但 pixel review 为 `has_free_cells=false`。
  5. 对危险输入 fail-closed，并把 `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`、`hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 固定为不可被输入覆盖。
  6. 输出 next required evidence：current live same-run feedback / wheel direction、IMU/battery calibration、HIL acceptance record、真实可用地图或导航执行材料。

## 对应责任 Engineer

- `robot-hardware-engineer`

## 风险、阻塞和需要补齐的证据链

- 这批 artifact 来自历史真实现场 run，但不是 current live HIL。
- `12_pc_feedback_samples_after_scan_delta_jog.json` 只能证明 `T=1001` 采样被观察到，不能证明轮速方向或安全准入。
- `14_scan_delta_metrics.json` 与 `18_operator_report_lidar_delta_response.json` 能补强物理运动的 LiDAR delta 材料链，但不证明 delivery success。
- `22-24` 和 `30-32` 的 pixel review 都是 `has_free_cells=false`，所以 bundle 不能把 map output 误写成导航地图通过。
- 仍缺当前同 run 的：
  - live WAVE ROVER HIL pass
  - 轮速方向确认
  - IMU / battery 标定
  - HIL acceptance record
  - 真实可用地图 / route execution 证据

## 已完成 KR 的历史记录位置、证据来源和剩余风险

- 本轮 planning 不移动已完成 KR，不更新 `OKR.md` 历史区。
- 证据来源：
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/tech-done.md`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/10_pc_first_jog_for_scan_delta.json`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/12_pc_feedback_samples_after_scan_delta_jog.json`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/14_scan_delta_metrics.json`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/18_operator_report_lidar_delta_response.json`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/22_field_first_jog_map.yaml`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/24_field_first_jog_map_pixel_review.json`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/30_manual_motion_map.yaml`
  - `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/32_manual_motion_map_pixel_review.json`
- 剩余风险：这些材料足以启动 `motion_map_hil_material_bundle`，不足以把 O1 标为 HIL 完成或 safe-to-control 完成。

## 需要创建或更新的 sprint 文档

本轮创建：

- `sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle/pre_start.md`
- `sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle/prd.md`
- `sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle/tech-plan.md`

implementation 和收口阶段后续再补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
