# Pre Start - O3 TF Receipt-Time Freshness Recovery

## Sprint Metadata

- `sprint_type: epic`
- Sprint: `sprints/2026.07.15_05-55_o3_tf_receipt_time_freshness_recovery/`
- Started: `2026-07-15 06:54 Asia/Shanghai`
- Target Objective: O3 自主导航与 current localization evidence chain
- Product owner: `product-okr-owner`
- Engineering owner: `robot-algorithm-engineer`
- Execution mode: single-owner closure；不做跨 owner 假并行

## 上轮事实与未完成项

`sprints/2026.07.15_04-55_o3_controlled_initialpose_localization_proof/` 已在真实上位机一次性完成
受控 `/initialpose` 后，拿到 fresh `/scan`、fresh `/amcl_pose`、dynamic `map->odom` 与唯一 AMCL
publisher attribution。唯一 post gate blocker 是 `map_to_odom_fresh`：最终判定 age=`5090ms`，超过
threshold=`3000ms`。该 sprint 的 `/initialpose` 发布额度已消费，永久禁止以任何 wrapper 或重跑方式
再次发布。

当前 helper 的 TF 回调只保存 header stamp，没有像 `/amcl_pose` 一样保存 callback
`received_at_ms`；`tf_edge_freshness_entry` 又以 collector 后段的 `generated_at_ms` 计算 age。因而现有
artifact 无法区分“TF 到达时就已过期”与“TF 到达后 collector 又执行约 5 秒才统一判定”。这是上轮
明确留下的新根因，不是对 route/readback/readiness wrapper 的重复消费。

## 同一 Blocker 扫描与切换理由

- 最近两轮的根因分别为缺 initial pose、以及一次授权后的 TF freshness 语义歧义；本轮只消费后者，
  没有第三次包装同一缺 initial pose blocker。
- O5 约 `85%`，仍是 `OKR.md` 4.1 中最低 Objective；但 production/public-cloud external evidence
  需要当前环境没有的新凭证/公网生产材料，且 CDN/relay/browser/export/review/readiness family 已被明确
  退役。本轮继续做 O5 support wrapper 会触发重复消费红线。
- 因此切换到可在当前代码、既有 artifact 与真实上位机只读窗口中推进的 O3。该修复直接决定
  current localization clean gate 是否可信，是后续 path/route 现场证据的前置条件。

## 本轮目标与用户价值

修复 TF edge 的 receipt-time freshness 合同：在回调时保存每条 transform 的接收时间，并同时输出
header、receipt 与 evaluation 三个时间基准，让 clean gate 判断“消息到达时是否新鲜”，而不是把
collector 后续耗时误算成传感器/AMCL stale。用户价值是减少误阻塞，同时继续对真实旧 TF、无时间戳
或无 receipt 的证据 fail closed。

## 范围和安全边界

- 优先离线复用上轮 artifact 证明根因、实现合同并跑 targeted regression。
- 工程完成后最多允许一次对 `root@192.168.1.11:37878` 的 read-only、no-topic-write、no-motion
  live capture；只有命令能够证明复用既有 runtime 且不会 start/stop runtime 时才可执行。
- 永久禁止本 sprint 发布 `/initialpose`。
- 禁止启动/停止 Nav2 runtime、planner/controller/path、NavigateToPose、`/cmd_vel`、
  `/api/base/manual`、UART、底盘控制或任何运动。
- `safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、
  `delivery_success=false`、`hil_pass=false` 在本轮保持不变。

## Owner 与交付物

`robot-algorithm-engineer` 单线负责 helper、targeted tests、导航文档、可选只读现场 artifact、验证修复
和 `tech-done.md`。Product closeout 只在工程证据完整后进行；当前阶段不得提前生成
`side2side_check.md` 或 `final.md` 冒充完成。

## 主要风险

1. 若把 `generated_at_ms - received_at_ms` 误当作消息自身新鲜度，仍会把 collector 延迟混入 gate。
2. 若只看 receipt 而不比较 header 与 receipt，会掩盖真正迟到的旧 TF。
3. CLI fallback 没有 callback receipt time 时必须保持 unknown/fail-closed，不能用进程结束时间伪造。
4. 现有 runtime 可能已停止；安全边界不允许本轮为取证自行重启。

