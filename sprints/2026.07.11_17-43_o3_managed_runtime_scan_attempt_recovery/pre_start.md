# O3 Managed Runtime Scan Attempt Recovery Pre Start

## Sprint Type

sprint_type: epic

## 用户价值和产品北极星

用户最终要的是固定路线可复跑、可定位、可送达的垃圾投递机器人，而不是一组看起来完整但不能驱动下一条现场命令的 support-only 报告。本轮继续走临时 O3 live no-motion lane，目标是把 true-board 最新 artifact 重新带回 `/scan` attempt 层，为后续 O1 路径生成、O6/O7 current-run route material 和真实 delivery evidence 铺前置事实。

## 背景

当前 `OKR.md` 4.1 中最低主 Objective 仍是 O5，约 `~85%`。但最近 O5 多轮已被真实 external production evidence 缺失锁死，且现有 packet / probe / readiness summary 均已明确 `okr_credit_allowed=false`。继续做 O5 support-only 只会重复消费同一 blocker，不会产生新的 mission artifact delta。

上一轮 `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/` 的最终 canonical artifact 没有稳定回到 `/scan` BEST_EFFORT / RELIABLE attempt 层，而是停在：

- `status=partial_runtime_in_progress`
- `evidence_type=partial_runtime_material`
- `/scan.probe.boundary=not_evaluated`
- `path_generated=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

这说明本轮不能再继续改 `/scan` QoS 合同本身，必须先恢复板端 managed runtime / ROS2 source 的稳定可用性，再决定 `/scan` 的 true blocker 是否仍在 QoS/sample timeout 层。

## OKR 映射和方向判断

- O5：本轮不继续推进。方向判断为 `暂停当前 support-only lane`，原因是连续 fail-closed 后仍缺真实 external production evidence。
- O1：本轮以 O3 no-motion supporting lane 方式补 `current same-run path generation success` 的前置事实链。方向判断为 `继续`。
- O6/O7：本轮不直接做 archive/readback/UI 包装；仅在 O3/O1 恢复 current-run `/scan` attempt 现场证据后，才有资格继续消费新的 route / delivery material。方向判断为 `继续，但本轮不做 support-only`.

## 本轮核心抓手

让最新 true-board helper 在 managed runtime / ROS2 source 恢复后，重新稳定落到 `/scan` probe attempt 层：

1. 若恢复后能进入 BEST_EFFORT / RELIABLE attempt，则继续记录 `/scan` sample / timeout / classification。
2. 若恢复后仍停在 partial runtime，则把 root cause 前移到 managed runtime wait、ROS2 source、CLI/runtime 可用性、lifecycle readiness 或 localization prerequisite 层。
3. 无论结果如何，都必须保持 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。

## Owner 和责任 Engineer

- Implementation owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`
- 本轮是单 owner 闭环；不拆给 O5/O6/O7 或硬件 lane。

## 连续 Blocker 核对

最近相关 sprint root cause 演化：

- `2026.07.11_14-42_o3_rclpy_scan_runtime_repair`：主进程 ImportError 已绕开，进入 ROS-sourced child runtime。
- `2026.07.11_15-44_o3_scan_endpoint_timing_inventory`：进入 `/scan` endpoint / sample timing inventory。
- `2026.07.11_16-43_o3_scan_long_window_reliable_probe`：首次曾到双 QoS attempt，但最终 canonical artifact 回退为 `partial_runtime_in_progress`。

因此本轮不是继续重复 `/scan_qos_or_window_timeout`，而是针对“managed runtime / ROS2 source 不稳定导致 latest artifact 回不到 `/scan` attempt 层”的新 blocker 做恢复。

## 优先级和验收口径

P0 接受：

- 最新 live artifact 重新进入 `/scan` attempt 层，并保留 BEST_EFFORT / RELIABLE attempt 事实；或
- 明确证明仍无法进入 `/scan` attempt 层，但 root cause 已前移并收敛到比上一轮更前置、更可执行的 managed runtime / ROS2 source / lifecycle blocker。

不接受：

- 回到 O5 support-only packet / readiness / wrapper；
- 只复述旧 artifact；
- 没有最新 true-board artifact；
- 误把 no-motion 诊断写成 `safe_to_control=true`、`robot_control_executed=true`、`delivery_success=true` 或 `hil_pass=true`。

## 风险、阻塞和需要补齐的证据链

- 风险：板端 ROS2 source、CLI 可用性、managed lifecycle 等状态可能漂移，导致 artifact 停在 partial runtime。
- 阻塞：若 `/scan` attempt 仍未出现，则 O1 same-run path generation、O6/O7 current-run route material 继续不能计分。
- 证据链缺口：需要最新 true-board `nav2_lifecycle_latest.json` 或同等 artifact，且必须能说明 `/scan` attempt 是否真正被执行。

## 需要创建或更新的 sprint 文档

本轮 planning 创建：

- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/pre_start.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/prd.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/tech-plan.md`

实施后应继续补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
