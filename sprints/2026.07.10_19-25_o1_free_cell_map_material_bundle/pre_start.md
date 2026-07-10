# O1 Free-Cell Map Material Bundle Pre-Start

## sprint_type

sprint_type: epic

## 用户价值和产品北极星

用户价值是把已经存在的同一 2026-06-22 现场 run free-cell 地图材料接入 O1 证据链，让后续 current live HIL / Nav2 路线执行能直接知道“地图是否已有可导航材料候选”，而不是继续停在上一轮 `has_free_cells=false` 的历史 wrapper 结论。

产品北极星仍是普通手机用户可安全、可验证地完成垃圾送达。本 sprint 只规划 O1 底盘/建图材料 intake，不证明真实送达、真实 safe-to-control、current live HIL 或 production cloud。

## 上轮状态和切换原因

O5 当前约 `85%`，是 `OKR.md` 4.1 节最低进度 Objective。但 `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已明确：

- `okr_credit_allowed=false`
- `support_only_reason=no_real_production_external_evidence`
- proof boundary 为 `software_proof_cloud_production_cutover_readiness_packet_only`
- 缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser 材料

因此本轮不继续 O5 support-only。没有真实 external production evidence 时，继续包装 O5 readiness / probe / cutover packet 只能做回归守护，不能计主 OKR 增量。

O1 当前约 `88%`。上一轮 `sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle/final.md` 已消费同 run 2026-06-22 的 first jog、feedback、LiDAR delta、operator report 和 `22-24` / `30-32` 两组 map materials，但这两组 pixel review 都是 `has_free_cells=false`，因此上一轮固定 `map_navigation_ready=false`。

同一 artifact 目录还存在未被上一轮 bundle 消费的 free-cell map materials：

- `33_pc_map_start_after_free_pixel_fix.json`
- `34_pc_map_list_after_free_pixel_fix.json`
- `35_fixed_free_cells_map.yaml`
- `36_fixed_free_cells_map.pgm`
- `37_fixed_free_cells_map_pixel_review.json`
- `38_pc_summary_after_map_fix.json`

其中 `34` 显示 `map_quality_summary.status=has_usable_map`、`usable_map_count=1`、`map_usable_for_navigation=true`；`37` 显示 `free_pixel_count=394`、`has_free_cells=true`。这是同一 run 的新 free-cell map material，不是对上一轮 `22-24` / `30-32` historical wrapper 的重复消费。

## OKR 映射和方向判断

- O5：暂停本轮主线推进。方向判断为“暂停计分，等待真实 external production evidence”。
- O1：继续推进。方向判断为“调整到同 run free-cell map material intake”，在不打开安全控制字段的前提下补强地图材料链。
- O6/O7：本轮不推进。若后续消费该 O1 material，应另起跨 owner sprint 明确 O6/O7 archive/readback 范围。

## KR 拆解、更新或历史归档

- O1 KR1/KR3：间接补强硬件现场 run 的材料链，证明同 run 中已有 first jog / feedback / LiDAR delta / map fix 材料可被统一消费。
- O1 KR4：下一步由 Hardware owner 增加 fail-closed 单测，覆盖 free-cell map material ready 和 unsafe / dangerous true blocked。
- O1 KR5：不改 launch 参数、不改串口参数、不改命令模式。
- 已完成 KR：本轮 planning 不归档任何 KR，不更新 `OKR.md`。
- 历史记录位置：待 implementation 和 Product closeout 后，再在 `OKR.md` 与 `docs/process/okr_progress_log.md` 记录；本轮禁止提前移动 KR。

## 本轮核心抓手

核心抓手是扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，消费同 run free-cell map materials 33-38，输出安全 additive 字段。建议字段包括：

- `free_cell_map_material_present=true`
- `free_cell_map_lifecycle_present=true`
- `free_cell_map_list_present=true`
- `free_cell_pixel_review_present=true`
- `free_cell_pixel_count=394`
- `free_cell_has_free_cells=true`
- `free_cell_usable_map_count=1`
- `map_navigation_material_ready=true`

这些字段只表示 free-cell map material 已被安全 intake；不表示 current live HIL、Nav2 route execution、delivery success 或 hardware safety。

## 固定禁止宣称

本 sprint 及后续 implementation 必须固定：

- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

不得宣称：

- current live HIL
- hardware safe-to-control
- delivery success
- wheel direction
- IMU/battery calibration
- production cloud
- 真实 Nav2 route execution success

## Owner 和执行方式

- Product planning owner：`product-okr-owner`
- 后续 implementation owner：`robot-hardware-engineer`
- 执行方式：单 owner 单线闭环，由 `robot-hardware-engineer` 扩展现有 hardware bundle、测试、文档和 `tech-done.md`。

## 需要创建或更新的 sprint 文档

本 planning 阶段创建：

- `sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/pre_start.md`
- `sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/prd.md`
- `sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/tech-plan.md`

后续 implementation 完成后必须创建或更新：

- `sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/tech-done.md`
- 若进入收口：`side2side_check.md`、`final.md`

本轮禁止改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 产品代码、测试代码和硬件配置

## 风险、阻塞和需要补齐的证据链

- 33-38 是同 run historical field material，不是 current live HIL。
- `map_navigation_material_ready=true` 只能表示 map material 有 free cells，可进入后续定位/路径检查；不等于 Nav2 已成功执行路线。
- 仍缺 current same-run `feedback_T1001.log`、motion command record、operator/external motion observation、HIL acceptance record、wheel direction、IMU/battery calibration 和 delivery result。
- 后续实现若只新增字段但没有真实读取 33-38 artifact 并做 fail-closed 校验，不满足本轮目标。
