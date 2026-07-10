# O1 Localization Path Material Bridge PRD

## sprint_type

sprint_type: epic

## 背景

O5 是当前最低 Objective，约 `85%`，但上一轮 `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已把 O5 锁定为 `okr_credit_allowed=false`。没有真实 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、真实 phone/browser 证据时，O5 support-only packet 不能继续涨分。

O1 当前约 `89%`。最近两轮已消费 2026-06-22 historical same-run motion/map/free-cell materials，下一步需要把 `free_cell` material 接到 localization/path proof。现有 `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/38_pc_summary_after_map_fix.json` 中已经有同 run readback：

- `/api/status` 与 `/api/localize/proof/latest` 读到 `map_once_observed=true`、`amcl_pose_observed=true`、localization TF map-to-odom / map-to-base-link。
- `/api/nav2/proof/latest` 读到 `path_generation_requested=true`，但 `path_generation_succeeded=false`、`path_generated=false`、`path_point_count=0`。

这份材料可以证明 localization readiness material 已出现，不能证明 same-run path 成功。

## 用户价值和产品北极星

用户价值是让 O1 从“地图有 free cells”继续靠近“能定位、能规划、能执行路线”的真实验收链。普通用户最终只关心小车能安全送达；本 sprint 的价值是把定位/path 缺口收敛成可复验材料，而不是把未成功的 path 误写成送达闭环。

产品北极星仍是普通手机用户可安全、可验证地完成垃圾送达。本 sprint 是 material bridge / localization readiness proof only，不是 current live HIL，不是真实 safe-to-control，不是真实 delivery success，不是真实 Nav2 route execution success。

## 需求目标

由 `robot-hardware-engineer` 在后续 implementation 中扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`：

1. 继续保留现有 motion、feedback、LiDAR delta、operator、map、free-cell 摘要。
2. 消费 `38_pc_summary_after_map_fix.json` 中 allowlisted same-run localization/path readback。
3. 输出 `localization_path_material_bridge` 相关安全字段。
4. 明确 `same_run_path_proven=false`，不得把 `path_generation_requested=true` 解释为 path 成功。
5. 可选引用 June 11 clean-baseline Nav2 path proof 作为 cross-run comparator，但 comparator 不能改写 same-run path 结论。
6. 对 unsafe raw path、URL、endpoint、token、traceback、`/dev/tty`、baudrate、dangerous true fail-closed。

## 非目标

- 不执行真实 HIL。
- 不打开 WAVE ROVER 底盘 UART。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不执行 NavigateToPose / FollowPath / controller / BT。
- 不改 launch 参数、串口参数、速度映射或固件假设。
- 不改 O5/O6/O7、PC UI、cloud relay 或 OKR 文档。
- 不归档 KR。

## OKR 映射和方向判断

- O1：继续。理由是存在新的 same-run localization/path material delta，可在不打开控制面的前提下补强 readiness proof。
- O5：暂停计分。理由是最低 Objective 当前缺真实 external production evidence，上一轮已明确 `okr_credit_allowed=false`。
- O6/O7：本轮不推进。若后续需要云端存档或 UI 展示，应另起 sprint，不能把 O1 hardware bundle 扩散成跨 owner work。

方向判断：继续 O1，但 closeout 必须保守。只有实际消费 `38` 中的 same-run localization material，并把 same-run path 未证明 fail-closed 写进合同，才可建议 Product closeout 评估 O1 `89% -> 90%`。只引用 June 11 comparator 或重复 free-cell fields 不应上调。

## KR 拆解、更新或历史归档

- O1 KR1/KR3：补强硬件现场 run 的材料链，从 wheel / LiDAR / map 延伸到 localization readiness。
- O1 KR4：补充 fail-closed 测试，避免未成功 path、dangerous true 或 unsafe raw 字段被误计。
- O1 KR5：不调整 launch 参数，仅保留当前配置边界。
- 已完成 KR：无。
- 历史记录位置：本 planning 阶段不移动 KR。后续若 closeout 通过，在 `OKR.md` 和 `docs/process/okr_progress_log.md` 记录证据和剩余风险。

## 核心验收口径

后续 implementation 通过的最低验收口径：

- 输出 schema 仍为 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`。
- 输出 proof scope 仍为 `software_proof_o1_motion_map_hil_material_bundle_only`。
- `localization_path_material_bridge_present=true`。
- `same_run_map_once_observed=true`。
- `same_run_amcl_pose_observed=true`。
- `same_run_localization_tf_map_to_odom=true`。
- `same_run_localization_tf_map_to_base_link=true`。
- `same_run_path_generation_requested=true`。
- `same_run_path_generation_succeeded=false`。
- `same_run_path_generated=false`。
- `same_run_path_point_count=0`。
- `same_run_path_proven=false`。
- `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- Positive output 不泄露 `source_base_url`、endpoint、absolute path、camera refs、raw runtime context、`/dev/tty`、baudrate、token、secret、password、traceback 或长 base64。
- Negative tests 覆盖缺 endpoint、缺 TF、path 被伪造为成功、unsafe 字段和 dangerous true。

## 对应责任 Engineer

- 主责：`robot-hardware-engineer`
- Product planning：`product-okr-owner`
- 不需要并行 owner。该任务文件范围集中在 hardware bundle、hardware tests、hardware docs 和本 sprint `tech-done.md`。

## 证据来源

本 sprint planning 已读并采用：

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md`
- `sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle/final.md`
- `sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/final.md`
- `sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/tech-done.md`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/38_pc_summary_after_map_fix.json`
- `sprints/2026.06.11_11-15_clean_baseline_nav2_path_refresh/tech-done.md`
- `sprints/2026.06.11_11-15_clean_baseline_nav2_path_refresh/artifacts/nav2_latest_after_success.json`

## 风险和阻塞

- `38` 中 localization readiness 是 historical same-run material，不是 current live proof。
- same-run path 仍未生成，`path_point_count=0`。
- June 11 clean-baseline path 是 cross-run comparator，不能替代 current/same-run path proof。
- 仍缺 current live HIL acceptance、轮向、IMU/battery 标定、真实 Nav2 route execution、delivery result 和 production cloud。
- 如果 implementation 只做字段包装而不做 allowlist/fail-closed 校验，不能计为有效 O1 material delta。

## 后续文档要求

后续 implementation 必须同步更新：

- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/tech-done.md`

Product closeout 若发生，必须创建：

- `side2side_check.md`
- `final.md`

本 planning 阶段按用户限定范围不修改 `OKR.md`、`docs/process/okr_progress_log.md` 或产品代码。
