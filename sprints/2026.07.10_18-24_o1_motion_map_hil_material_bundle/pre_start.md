# O1 Motion Map HIL Material Bundle Pre-start

## sprint_type

sprint_type: epic

## 启动事实

本轮已读取 `AGENTS.md`、`OKR.md`、`docs/vendor/VENDOR_INDEX.md`、最近 3 个相关 `final.md`，以及 `sprints/2026.06.22_01-35_motion_map_runtime_probe/` 的历史现场材料。当前 `OKR.md` 4.1 显示：

- O5 云中转控制面约 `85%`，仍是当前最低 Objective。
- O1 硬件协议可信底盘约 `87%`，是当前仍可被真实历史现场材料补强的软件侧目标。
- O6 / O7 约 `91%`，近期只允许在有 live route execution、delivery record、operator acceptance 或 production readback 时继续推进。

最近 3 个收口已经把方向说清楚：

- `2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 明确 O5 `okr_credit_allowed=false`，没有真实 external production evidence 时不得继续上调。
- `2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/final.md` 明确 O1 已消费历史 same-session wheel feedback artifact，但仍缺 current live HIL pass、轮速方向、IMU/battery 标定和 HIL 准入。
- `2026.07.10_15-22_o6_o7_field_operator_confirmation_material/final.md` 明确 O6/O7 继续推进必须接 live route execution、delivery record、operator acceptance 或 production cloud readback。

因此，本轮不继续消费 O5 的同类 blocker，也不继续给 O6/O7 做 wrapper/surface，而是转向 O1 的 `motion_map_hil_material_bundle` 规划：把同一历史现场 run 里的 motion、feedback、scan delta、map output/pixel review、operator report 汇总成一个 fail-closed 的 software-proof material contract。

## 历史材料事实

本轮要消费的历史材料均来自 `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/`：

- `10_pc_first_jog_for_scan_delta.json`：first jog 命令经 PC 代理转发，`proxy_status=command_forwarded`、`remote_http_status=200`、`requested_direction=forward`、`clamped_speed_mps=0.08`、`clamped_duration_ms=800`。
- `12_pc_feedback_samples_after_scan_delta_jog.json`：反馈采样读回 `completed_sample_count=3`、`t1001_observed_count=3`、`all_samples_observed_t1001=true`、`observed_feedback_types=[130,1001]`。
- `14_scan_delta_metrics.json`：LiDAR scan delta 结果 `paired_bins=162`、`median_abs_diff_m=1.735...`、`changed_bin_ratio=1.0`、`field_pack_pass=true`。
- `18_operator_report_lidar_delta_response.json`：operator report 已声明 `physical_motion_lidar_delta_proven=true`，同时保留 `wheel_feedback_lr_nonzero_proven=false`、`real_route_map_proven=false`、`delivery_success=false`。
- `22_field_first_jog_map.yaml`、`23_field_first_jog_map.pgm`、`24_field_first_jog_map_pixel_review.json`：first jog map output 已存在，但 pixel review 仍是 `has_free_cells=false`。
- `30_manual_motion_map.yaml`、`31_manual_motion_map.pgm`、`32_manual_motion_map_pixel_review.json`：manual mapping output 已存在，但 pixel review 仍是 `has_free_cells=false`。

这些材料足以补强 O1 的“历史现场 motion + map 材料链”，但它们不等于 current live HIL pass，也不等于 safe-to-control、delivery success 或可导航地图通过。

## 本轮目标 Objective

- 主目标：O1 硬件协议可信底盘。
- 本轮目标：规划一个 `motion_map_hil_material_bundle` 软件合同，让后续 `robot-hardware-engineer` 能把上述同一历史现场 run 材料接入为可复验、可脱敏、可 fail-closed 的摘要合同。
- 本轮不是做 current live HIL pass，也不是把历史 map output 误写成导航可用结论。

## 证据边界

本轮后续实现必须固定保守边界：

- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

允许承认的事实仅限于：

- 历史现场 first jog command 已发生并被代理转发；
- 同 run 反馈采样观察到 `T=130` / `T=1001`；
- LiDAR scan delta 达到 field pack 阈值；
- operator report 认定 `physical_motion_lidar_delta_proven=true`；
- 两组 map output 与 pixel review artifact 存在，但 `has_free_cells=false`，因此不能证明导航可用地图。

## Owner

- 主责 owner：`robot-hardware-engineer`
- 执行方式：单线闭环，由 `robot-hardware-engineer` 后续负责实现、测试、修复和 `tech-done.md` 留档。
- Product / 主节点：只负责规划、验收口径、sprint 收口和最终汇总，不改产品代码、不跑实现测试。

## 范围约束

本 planning sprint 只创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

本轮 planning 禁止修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 产品代码、测试代码、硬件配置、launch 参数

## 验收口径

planning 完成后，后续 implementation 必须做到：

1. 能消费上述 8 个核心历史 artifact，并确认它们属于同一历史现场 run。
2. 输出 `motion_map_hil_material_bundle` 安全摘要，只保留 status、safe refs、关键数值摘要、blocked reasons 和 next required evidence。
3. 对缺文件、artifact 形状不匹配、引用不一致、危险 true、unsafe path/url/base64/token/traceback 等情况 fail-closed。
4. map output 只能标记为 `map_output_present`，不得把 `24` / `32` 中 `has_free_cells=false` 说成地图可导航。
5. 合同必须显式保留 `software_proof_o1_motion_map_hil_material_bundle_only` 和全部 false safety fields，并说明下一步仍需 current live HIL pass、轮速方向、IMU/battery 标定和 HIL acceptance record。
