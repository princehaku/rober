# Side-by-side Check - O3 Live Full Structured Path Capture

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/`
- Product owner: `product-okr-owner`
- Product acceptance status: accepted as additive strict no-motion material
- Acceptance artifact: `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/product/product_acceptance_live_full_structured_path_capture.json`

## 用户价值和产品北极星

北极星仍是让普通手机用户发起一条可验证的固定路线送垃圾任务，而不是让工程侧反复包装
readiness 或历史材料。本轮的产品价值是把 21:57 旧 artifact 的 stdout-tail 缺口推进成新的
fresh same-run structured path material，让后续 fixed-route / route-intent consumer 有完整 pose
列表可消费。

## OKR 映射和方向判断

- 方向判断：继续 O3/O1 strict no-motion live path material lane。
- O5 仍是最低 Objective，约 `85%`，但本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、
  worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence，因此不推进 O5。
- O1 保持约 `94%`；本轮是 additive no-motion path material，不新增 current live HIL、safe-to-control、
  route execution 或 delivery 证据。
- O6/O7 保持约 `93%`；本轮没有把材料接入 archive/readback 或 PC consumer。
- KR 归档决策：`不归档`。没有任何 KR 达到完成、替换或取消条件。

## Side-by-side 验收

| 验收项 | 期望 | 本轮事实 | Product 判定 |
| --- | --- | --- | --- |
| Fresh live artifact | 使用本轮 live 材料 | `fresh_live_artifact_used=true`，`historic_21_57_artifact_reused_as_live_proof=false` | 通过 |
| Path generated | 生成 planner-only path | `path_generated=true` | 通过 |
| Structured pose count | 原目标 `path_structured_pose_count=21` | `path_structured_pose_count=28`，`path_point_count=28` | 原目标未达成 |
| Blocker | 若不是 21，要写明当前 blocker | `expected_21_structured_pose_count_not_reproduced_current_live_returned_28_after_map_bounds_adaptation` | 通过 |
| No-motion safety | 不触发运动/控制链 | `safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`robot_control_executed=false` | 通过 |
| Mission gates | 不声明 route/delivery/HIL | `route_execution_success=false`、`delivery_success=false`、`hil_pass=false` | 通过 |

## Product Acceptance Verdict

接受本轮作为 O3/O1 strict no-motion fresh structured planner path material。该接受只覆盖
28-pose current live artifact 对 fixed-route / route-intent consumer 的后续输入价值。

不接受为原始 21-pose target achieved；不接受为 route execution、fixed-route movement、
NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、
delivery/operator acceptance、HIL、safe-to-control 或 O5 production/external evidence。

## 优先级和验收口径

下一轮不应重复 route-intent/readiness 包装。优先级是：

1. `robot-algorithm-engineer` 消费本轮 28-pose structured artifact，接入 fixed-route 或 route-intent consumer。
2. 若产品仍要求复现 21-pose target，则 `robot-algorithm-engineer` 先用当前 live AMCL/map state 复跑，
   避免 `map_bounds_adapted_no_motion_planner_probe`。
3. 任何 OKR 增量必须来自更强证据：route execution、delivery/operator acceptance、current live HIL、
   safe-to-control 或 O5 external production evidence。

## 风险、阻塞和证据链缺口

- 当前 exact blocker 是 `expected_21_structured_pose_count_not_reproduced_current_live_returned_28_after_map_bounds_adaptation`。
- 28-pose artifact 可作为新材料消费，但不能反推 21-pose replay 已达成。
- safety/control/delivery/HIL fields 全部保持 false，不能对外宣称可控、可送达或可上车验收。
- O5 仍缺真实 external production evidence，不能通过本轮 O3 artifact 提升或归档。
