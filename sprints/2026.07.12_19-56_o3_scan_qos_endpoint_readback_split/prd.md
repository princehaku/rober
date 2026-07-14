# PRD - O3 Scan QoS Endpoint Readback Split

## Summary

本 sprint 延续 `2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair` 的 Product acceptance。上一轮已经证明 lifecycle-active baseline 不应再被旧 graph timeout 包住：

- `map_server_active=true`
- `amcl_active=true`
- `managed_runtime_log_lifecycle_readback.clean=true`
- `map_once_observed=true`
- `amcl_pose_observed=false`
- `map_to_odom_dynamic_source_missing`
- `path_generation_attempted=false`
- `path_generated=false`
- primary blocker: `Nav2 sensor input / /scan_reliable_and_best_effort_timeout`

本轮 PRD 要求 Robot Software 单 owner 继续 O3/O1 strict no-motion，把 `/scan_reliable_and_best_effort_timeout` first split 成 publisher endpoint、QoS/window/ROS readback、LiDAR runtime 三类事实。Product 不接受回退到 lifecycle、map_server configure/on_configure、loadmap、graph timeout wrapper 或 O5 support-only。

## 用户价值和产品北极星

北极星：普通手机用户不懂 ROS2、不看 SSH、不管硬件细节，也能让小车沿固定路线完成垃圾投递，并得到可验证的成功或失败结果。

本轮不交付用户界面或真实运动；本轮交付的是定位/路径链路的下一层可执行证据。只要 `/scan` 样本仍不能被可靠读到，AMCL 就无法形成 `/amcl_pose`，dynamic `map->odom` 也继续缺源，path generation 和 route execution 不能被安全地证明。

## Problem

18:56 canonical artifact 已经把 lifecycle/map_server/AMCL 上游 blocker 推过了，但 `/scan` 在 RELIABLE 和 BEST_EFFORT 读样本窗口中仍 timeout。这个 timeout 当前有三类可能：

1. `/scan` publisher endpoint 不存在、不稳定、topic type/endpoint 不符合预期。
2. ROS readback 本身有 QoS、window、CLI/rclpy、graph 或 timeout budget 问题。
3. LiDAR runtime 确实没有生产样本，后续可能落到 driver、serial、wiring 或硬件运行状态。

Product 的核心需求是先拆清前两类，再决定是否升级 Hardware。不能因为 `/scan` timeout 就直接改硬件配置或读 vendor 事实，也不能把旧 lifecycle/graph wrapper 重新包装成进度。

## Scope

In scope for Robot Software implementation:

- 在 strict no-motion helper/artifact 中保留 18:56 lifecycle-active baseline。
- 增强 `/scan` publisher endpoint inventory，记录 publisher count、node/topic/source clue、topic type、endpoint/QoS 可见性。
- 对 RELIABLE / BEST_EFFORT sample attempts 增加清晰的窗口、timeout、CLI/rclpy、readback classification。
- 将 `/scan_reliable_and_best_effort_timeout` 分裂成可验收的 primary/secondary root-cause 候选。
- 若证据指向 LiDAR runtime，输出 Hardware handoff 条件，但不直接改硬件配置。
- 保持 no-motion safety booleans false。
- 更新 helper tests、navigation docs 和 sprint implementation closeout。

Out of scope:

- O5 production/cloud support-only、cutover readiness、external probe wrapper。
- Product code、UI/API、O6/O7 consumer surface、handoff/checklist。
- WAVE ROVER、ESP32、UART、serial、baudrate、wiring、电压、vendor-backed hardware edits。
- `/cmd_vel`、`/api/base/manual`、NavigateToPose、route execution、delivery command 或 WAVE ROVER UART。
- 把旧 `map_server_lifecycle_not_active`、`map_server_on_configure_return_false_after_valid_map_io_deferred_completion`、`map_server_changestate_response_false_before_map_io_completion`、`loadMapResponseFromYaml` 或 `managed_runtime_graph_probe_timeout_after_lifecycle_active_log` 重新设为 primary，除非新 true-board artifact 推翻 18:56。

## OKR Mapping And Direction Judgment

- O5 是当前最低 Objective，约 `85%`；本轮不做 O5，因为缺真实 production/external evidence。继续 support-only/wrapper 只会重复 `okr_credit_allowed=false`。
- O3/O1 strict no-motion 是本轮最高可执行抓手，因为它直接阻塞 same-run path generation、route execution、delivery/operator evidence 和 current live HIL 的前置定位链路。
- 方向判断：继续 O3/O1，暂停 O5 support-only，冻结独立 O6/O7 surface。
- OKR 口径：本轮即使成功拆清 `/scan` timeout，也只算 supporting evidence，默认不调整百分比；只有产生 same-run path generation、route execution、delivery/operator acceptance、current live HIL 或 real production external evidence，才进入 Product percentage review。

## Acceptance Criteria

P0 accepted outcome must satisfy all:

- Artifact starts from the 18:56 accepted baseline: `map_server_active=true`、`amcl_active=true`、`managed_runtime_log_lifecycle_readback.clean=true` unless new true-board evidence explicitly disproves it.
- `/scan_reliable_and_best_effort_timeout` is split into publisher endpoint, QoS/window/ROS readback, or LiDAR runtime with evidence fields clear enough for the next owner decision.
- strict no-motion fields remain false, and proof explicitly says no /cmd_vel, no `/api/base/manual`, no NavigateToPose, no WAVE ROVER UART.
- `path_generation_attempted=false` and `path_generated=false` remain honest unless the implementation actually reaches a planner-only proof without motion, which is not the expected scope.
- `tech-done.md` records local validation, true-board validation if reachable, exact blocked fields, and remaining risks.

Accepted blocked outcome:

- If still blocked, Product accepts only when the blocker is narrower than the starting phrase and identifies whether the next action belongs to Robot Software, Hardware, or Algorithm.

Rejected outcomes:

- Repeating old lifecycle/map_server/loadmap/graph timeout wording as the primary blocker without new evidence.
- Claiming mission progress from readback/helper/docs alone.
- Calling Hardware before endpoint/QoS/window/ROS readback is separated.
- Calling Algorithm before `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough.
- Any motion/control action in this strict no-motion sprint.

## KR 拆解、更新或历史归档

本 planning pass 不归档任何 KR。当前 KR 历史位置保持不变：

- 已完成或归档 Objective/KR 仍在 `OKR.md` 的历史/归档区和 `docs/process/okr_progress_log.md`。
- 本轮只允许新增 O3/O1 supporting evidence。
- O5 继续约 `85%`，O1/O6/O7 继续约 `93%`，除非 implementation 产生 stronger mission evidence。

## Risks And Evidence Gaps

- `/scan` publisher 可能存在但 sample window 仍读不到。
- QoS/readback 可能仍受 CLI/rclpy、DDS discovery、daemon 或 timing 影响。
- LiDAR runtime 可能确实无样本，但本轮不应先改硬件配置。
- `/amcl_pose` 仍可能 false，dynamic `map->odom` 仍可能 missing。
- 当前没有 same-run path success、route execution、`route.csv`、keyframe、rosbag、replay JSONL、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。
