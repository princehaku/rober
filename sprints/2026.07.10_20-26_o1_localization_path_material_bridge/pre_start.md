# O1 Localization Path Material Bridge Pre-Start

## sprint_type

sprint_type: epic

## 用户价值和产品北极星

用户价值是把历史同 run free-cell map material 继续向定位和路径证明链推进：团队下一步需要知道同一 2026-06-22 field run 中是否已经读到 `map_once`、`amcl_pose`、localization TF，以及 Nav2 path 字段当前卡在哪里。这样后续 current live HIL / Nav2 路线验证可以直接对照缺口，而不是继续重复解释 free-cell map intake。

产品北极星仍是普通手机用户可安全、可验证地完成垃圾送达。本 sprint 只规划 O1 material bridge / localization readiness proof，不证明 current live HIL、真实 safe-to-control、真实 delivery success 或真实 Nav2 route execution success。

## 上轮状态和切换原因

O5 当前约 `85%`，是 `OKR.md` 4.1 节最低 Objective。但 `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已明确：

- `okr_credit_allowed=false`
- `support_only_reason=no_real_production_external_evidence`
- proof boundary 为 `software_proof_cloud_production_cutover_readiness_packet_only`
- 缺真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 和真实 phone/browser 材料

因此本轮不继续 O5 support-only packet / readiness / probe。没有真实 external production evidence 时，继续包装 O5 只能做回归守护，不能计主 OKR 增量。

O1 当前约 `89%`。最近两轮 O1 已连续消费 2026-06-22 historical same-run motion/map/free-cell materials：

- `sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle/final.md`：消费 first jog、feedback、LiDAR delta、operator report、`22-24` 和 `30-32` map materials，O1 到约 `88%`。
- `sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/final.md`：消费 artifacts `33-38` 的 free-cell map materials，输出 `free_cell_pixel_count=394`、`free_cell_has_free_cells=true`、`free_cell_usable_map_count=1`、`map_navigation_material_ready=true`，O1 到约 `89%`。

上一轮 final 已写明下一步必须把 free-cell material 接到 current/live localization/path proof。当前可移动的更强材料是同一 `38_pc_summary_after_map_fix.json` 中已经出现 localization/material readback：

- `map_once_observed=true`
- `amcl_pose_observed=true`
- `localization_tf_observed={"map_to_odom":true,"map_to_base_link":true}`
- `nav2_proof_latest.path_generation_requested=true`
- `path_generation_succeeded=false`
- `path_generated=false`
- `path_point_count=0`

这说明同 run localization readiness 有材料可消费，但 same-run path 仍未证明。本轮只规划 bridge，不把 path false 包装成路线成功。

## OKR 映射和方向判断

- O5：暂停本轮主线推进。方向判断为“暂停计分，等待真实 external production evidence”。
- O1：继续推进。方向判断为“调整到 localization_path_material_bridge”，把 free-cell material 与同 run localization/path readback 接起来。
- O6/O7：本轮不推进。若未来要归档或展示该 O1 bridge，需另起跨 owner sprint 明确 O6/O7 archive/readback/UI 范围。

若后续 implementation 确实消费新的 same-run localization material，并 fail-closed 标明 same-run path 仍未证明，Product closeout 可保守评估 O1 是否从 `89%` 到 `90%`。若 implementation 只重复 free-cell fields、只引用 cross-run comparator，或没有消费 `38` 中的 localization/path readback，则 O1 不应上调。

## KR 拆解、更新或历史归档

- O1 KR1/KR3：补强同 run motion / feedback / map / localization 材料链，但不证明 current live HIL 或实测里程计闭环。
- O1 KR4：下一步由 Hardware owner 增加 fail-closed 单测，覆盖 localization/path readback 正例、path 未证明、unsafe 字段和 dangerous true。
- O1 KR5：不改 launch 参数、不改串口参数、不改命令模式。
- 已完成 KR：本 planning 阶段不归档任何 KR，不更新 `OKR.md`。
- 历史记录位置：待 implementation 和 Product closeout 后，再在 `OKR.md` 与 `docs/process/okr_progress_log.md` 记录；本轮禁止提前移动 KR。

## 本轮核心抓手

核心抓手是继续扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，新增 `localization_path_material_bridge` 摘要，消费 `38_pc_summary_after_map_fix.json` 的 same-run localization/path readback，并可选引用 June 11 clean-baseline path evidence 作为 cross-run comparator。

建议输出字段：

- `localization_path_material_bridge_present=true`
- `same_run_localization_material_present=true`
- `same_run_map_once_observed=true`
- `same_run_amcl_pose_observed=true`
- `same_run_localization_tf_map_to_odom=true`
- `same_run_localization_tf_map_to_base_link=true`
- `same_run_path_generation_requested=true`
- `same_run_path_generation_succeeded=false`
- `same_run_path_generated=false`
- `same_run_path_point_count=0`
- `same_run_path_proven=false`
- `cross_run_clean_baseline_path_comparator_present=true` only if June 11 artifacts are safely consumed
- `cross_run_clean_baseline_path_point_count=31` only as comparator, not same-run proof

以上字段只表示 localization/path material bridge 已被安全 intake；不表示 current live HIL、Nav2 route execution、delivery success 或 hardware safety。

## 固定禁止宣称

本 sprint 及后续 implementation 必须固定：

- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `same_run_path_proven=false`
- `nav2_route_execution_success=false`

不得宣称：

- current live HIL
- hardware safe-to-control
- delivery success
- wheel direction
- IMU/battery calibration
- production cloud
- current live map navigation readiness
- 真实 Nav2 route execution success

## Owner 和执行方式

- Product planning owner：`product-okr-owner`
- 后续 implementation owner：`robot-hardware-engineer`
- 执行方式：单 owner 单线闭环，由 `robot-hardware-engineer` 扩展现有 hardware bundle、测试、文档和 `tech-done.md`。

## 需要创建或更新的 sprint 文档

本 planning 阶段创建：

- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/pre_start.md`
- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/prd.md`
- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/tech-plan.md`

后续 implementation 完成后必须创建或更新：

- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/tech-done.md`
- 若进入收口：`side2side_check.md`、`final.md`

本轮禁止改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 产品代码、测试代码和硬件配置

## 风险、阻塞和需要补齐的证据链

- `38` 是 historical same-run software material，不是 current live HIL。
- `map_once`、`amcl_pose` 和 localization TF 可证明 localization readiness material，但不能证明路径生成成功。
- same-run path 当前仍是 `path_generation_succeeded=false`、`path_generated=false`、`path_point_count=0`。
- June 11 clean-baseline path 的 `path_point_count=31` 只能作为 cross-run comparator，不能替代 same-run path proof。
- 仍缺 current same-run `feedback_T1001.log`、motion command record、operator/external observation、HIL acceptance record、wheel direction、IMU/battery calibration、delivery result 和 live Nav2 route execution。
- 后续实现若只新增字段但没有真实读取 `38` 的 localization/path readback 并做 fail-closed 校验，不满足本轮目标。
