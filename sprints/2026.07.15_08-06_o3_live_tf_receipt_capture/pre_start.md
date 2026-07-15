# Pre Start - O3 Live TF Receipt Capture

## Sprint Metadata

- `sprint_type: epic`
- Sprint: `sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/`
- Started: `2026-07-15 08:06 Asia/Shanghai`
- Target Objective: O3 current localization evidence chain，supporting O1 safe route precondition
- Product owner: `product-okr-owner`
- Engineering owner: `robot-algorithm-engineer`
- Execution mode: single-owner closure；不做跨 owner 假并行

## 上轮事实与未完成项

`sprints/2026.07.15_05-55_o3_tf_receipt_time_freshness_recovery/` 已完成 TF receipt-time
freshness 合同修复和 160 项 targeted regression，但当时只读 SSH preflight 证明 localization runtime
未运行，所以没有形成新的 live callback receipt artifact。该离线合同已退役，禁止再包装为新交付。

本轮 CEO 再次明确给出真实上位机 `root@192.168.1.11:37878` 并要求持续推进 OKR。主节点把这次新指令
解释为仅授权 `strict-no-motion localization-only runtime` 的一次受控启动、采集与 helper-owned cleanup；
授权不包含 `/initialpose`、path/planner/controller、NavigateToPose、底盘控制、UART、运动、route、delivery
或 HIL。若工程 owner 判断该解释与现场安全前置冲突，必须 fail closed，不得自行扩大权限。

## 同一 Blocker 扫描与切换理由

- O5 约 `85%`，仍是最低 Objective。Robot Software 已在本轮做只读现场审计：上位机没有
  cloudflared/ngrok/frp/WireGuard/tailscale，也没有 relay/tunnel 进程；仓库只有 loopback Docker relay，
  缺公网 endpoint、TLS/DNS、tunnel runtime 与凭证，不能产出 success-class external evidence。
- O5 的 preflight/readback/export/browser/voice/packet/mock wrapper 已退役；本轮不得用 local relay 包装再次
  消费同一 production blocker。
- O6/O7 约 `93%` 的本地 consumer/voice/browser 包装同样已退役；O1 约 `94%` 的控制/HIL 缺口涉及真实
  运动与 operator acceptance，不在本轮授权内。
- 因此本轮切换到上轮明确允许的唯一下一步：用已修复合同采一次真实上位机 live receipt artifact。
  这是 current-run sensor/localization artifact，不是新的离线 wrapper。

## 本轮目标与用户价值

在真实上位机同一窗口内启动严格无运动 localization-only runtime，消费实际 `/scan`、`/amcl_pose`、
`/tf`、`/tf_static` callback，并生成可复算 `received_at_ms`、`header_age_at_receipt_ms`、
`receipt_age_at_evaluation_ms` 与 `header_age_at_evaluation_ms` 的新 artifact。目标是验证 TF freshness
修复在真实运行时的行为，并把下一阻塞收敛为可行动的现场事实。

## 范围与安全边界

- 开工前必须阅读 `docs/vendor/VENDOR_INDEX.md`；LiDAR 串口只采用仓库已验证的当前现场参数来源，
  不推导 WAVE ROVER UART 或 Orange Pi 固定设备名。
- 只允许一次 helper-owned managed localization runtime；必须 `--strict-no-motion --no-base-uart`，不得传
  `--initialpose-opt-in` 或 `--path-generation-opt-in`。
- runtime 只允许 map_server、AMCL、LiDAR 与 helper 所需 static TF；不得启动 planner/controller。
- helper 必须清理自己创建的 process group，并验证没有残留；不得停止 helper 启动前已存在的进程。
- 固定禁止 `/initialpose`、NavigateToPose、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、底盘运动、
  route execution、delivery 与 HIL。
- `safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、
  `delivery_success=false`、`hil_pass=false` 必须保持。

## Owner 与交付物

`robot-algorithm-engineer` 单线负责本地回归、远端 helper SHA 同步、唯一一次 managed no-motion capture、
artifact 拉回与结构验收、必要修复复验、导航文档同步和 `tech-done.md`。工程完成前不得生成
`side2side_check.md` 或 `final.md`。

## 主要风险

1. 未发布 `/initialpose` 时 AMCL 可能不产生 dynamic `map->odom`；必须记录 exact blocker，不能绕过安全边界。
2. managed runtime 会打开真实 LiDAR，但禁止打开 base UART；设备/波特率必须引用本地 vendor 和既有现场证据。
3. 若远端 helper SHA、ROS source、map 或 LiDAR前置不一致，必须在写 topic/control 前 fail closed。
4. 本轮 live artifact 仍可能低于 Mission Objective 0；不得因为 current-run artifact 就声称 route/delivery 完成。
