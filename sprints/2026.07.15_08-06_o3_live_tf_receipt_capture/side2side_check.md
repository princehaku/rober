# Side2Side Check - O3 Live TF Receipt Capture

## Sprint Metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/`
- Product owner：`product-okr-owner`
- Engineering owner：`robot-algorithm-engineer`
- Acceptance date：`2026-07-15 Asia/Shanghai`
- Product status：`accepted_current_run_receipt_artifact_blocked_missing_map_to_odom_no_okr_credit`
- Proof boundary：`live_strict_no_motion_localization_receipt_artifact_blocked_missing_map_to_odom`

## 用户价值与北极星对照

本轮把上一轮仅离线成立的 TF receipt-time freshness 合同带进真实上位机 current runtime，形成可复算、
可归因且有清理边界的传感器/定位 artifact。这提升了“定位证据可信”这一条 route 安全前置链，但没有产生
可验证的垃圾送达、真实 route execution、operator acceptance 或 production cloud 结果，因此不满足产品北极星
中的可靠送达闭环。

## Product Acceptance 对照

| 验收项 | 工程证据 | Product 判断 |
| --- | --- | --- |
| 唯一 live run | `capture-envelope.json` 记录 `final_live_run_count=1`、natural exit=`2` | 接受一次 current-run fail-closed artifact，不把 exit `2` 包装为成功 |
| runtime 与 sensor | map_server/AMCL active，`/scan` fresh `21ms` | 接受 localization-only runtime 与 fresh scan 事实 |
| receipt 合同 | TF inventory `3/3` transforms 含整数 `received_at_ms` | 接受上一轮离线合同已在 current runtime 落地 |
| age 复算 | dynamic `odom->base_link` 三类 age 为 `6/39677/39683ms`，decision basis=`header_age_at_receipt_ms` | 接受 collector evaluation delay 未污染 receipt-time freshness decision |
| 目标 edge | dynamic `map->odom` missing，三类 age 为 `null` | 拒绝 clean localization 与目标 edge receipt 结论 |
| exact blocker | `amcl_requires_initial_pose_but_initialpose_forbidden_in_current_safety_scope`、`/amcl_pose_probe_timeout`、`map_to_odom_dynamic_source_missing` | 接受 fail-closed 根因，不授权本轮发布 `/initialpose` 或重跑 |
| Safety | initialpose attempts=`0`；path/planner/controller/UART/control/route/delivery/HIL 均 false | 接受安全边界，拒绝 safe-to-control、route、delivery、HIL 声明 |
| Cleanup | helper-owned cleanup residual=`0`，post inventory residual=`0` | 接受 helper-owned runtime 已清理，不推断未知进程状态 |

## O5 最低优先级复核

O5 仍约 `85%` 且最低。本 sprint 前置记录的 live tunnel 只读审计未观察到
cloudflared/ngrok/frp/WireGuard/tailscale 或 relay/tunnel runtime；当前 exact blocker 是缺 public endpoint、
TLS/DNS、provider runtime 与 credential。该审计只证明当前上位机没有可用 cutover 通道，不是 external
production artifact，也不允许重启 preflight/readback/export/browser/voice/packet/mock wrapper 链。

本轮切到 O3 的理由在收口时仍成立：确实新增 current-run true-board receipt artifact，而不是另一个离线
wrapper；但它仍低于 Mission Objective 0，因此不调整 O5/O6/O7/O1 主百分比。

## Mission Objective 0 与 OKR 判定

- `current_run_artifact_delta=true`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`
- O5 约 `85%`、O6/O7 各约 `93%`、O1 约 `94%`，全部保持。
- KR：`不归档`；没有已完成 KR 移入历史区。本轮证据历史留档位置为当前 sprint 与
  `docs/process/okr_progress_log.md`。

## 拒绝项与风险边界

- 不证明 physical localization ground truth、fresh dynamic `map->odom`、clean map-to-base chain。
- 不证明 planner/controller/path、NavigateToPose、`/cmd_vel`、`/api/base/manual`、UART 或机器人运动。
- 不证明 route execution、delivery/operator acceptance、HIL、safe-to-control 或 production cloud。
- `odom->base_link` receipt age 只能验证该 observed edge 的合同，不能代替缺失的 `map->odom`。

## 方向判断与责任 Owner

- O3：`继续但调整抓手`。停止重复“无 initial pose 的同一 managed runtime capture”；下一轮必须由
  `robot-algorithm-engineer` 消费 verified persisted pose，或在新的明确授权下产生一次 controlled
  localization input，再只读采目标 dynamic `map->odom` receipt evidence。
- O5：`暂停本地包装`。只有 success-class public-cloud endpoint/TLS/runtime evidence 到位时，再由
  `robot-software-engineer` 接回 production cutover lane。
- route/control/HIL：继续隔离；只有 explicit operator approval 与 current HIL gate 后，分别路由
  `robot-algorithm-engineer` / `rober-hardware-engineer`，不得由本 sprint 延伸授权。
