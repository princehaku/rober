# Pre Start: O9 Narrow Runtime Material Epic

## sprint_type

sprint_type: epic

## 用户价值和北极星

北极星不变：普通手机用户把垃圾交给低成本小车，小车沿固定路线送到垃圾站，必要时跨楼层进出电梯，并在异常时安全停止、请求人工协助和留下可复盘证据。

本轮价值不是再写接口，而是把 O9 从约 18% 的真实材料缺口推进到可验收材料：PC 同源 refresh 复验、continuous radar/status 或 SLAM `/map` lifecycle、真实/受控电梯图片、stop-first HIL 决策门。

## OKR 映射和方向判断

- 最低 Objective：O9，当前约 18%，是 `OKR.md` 4.1 当前最低 Objective。
- 方向判断：继续。继续沿 O9 窄 Epic 真实材料突破推进，不调整北极星，不更新 `OKR.md`。
- 本轮 KR 拆解：
  - O7/O9：PC 同源触发 live 8787 refresh，并读回 fresh proof 与 continuous not_proven 边界。
  - O3/O9：推进 continuous radar/status blocker 收敛，或形成 SLAM `/map` lifecycle 新 artifact。
  - O2/O9：交付真实/受控电梯图片 manifest 与 OpenCV eval。
  - O1/O9：执行 stop-first HIL 授权决策门；安全条件不足时升级 CEO blocker。

## 最近 2 轮 blocker 核对

| Sprint | 结论 | 本轮处理 |
| --- | --- | --- |
| `sprints/2026.06.05_02-03_o9_radar_status_fresh_proof/tech-done.md` | 本地 status contract 通过；远端未 restart/curl；PC 侧消费 fresh proof 失败后清理；continuous radar 仍 not_proven。 | 不再 Micro-only status/readback。Full-stack 必须做 PC 同源 live refresh 复验，Robot Software 必须推进 continuous radar/status 或 SLAM `/map`。 |
| `sprints/2026.06.05_04-05_okr-six-sprint-state-rewrite/tech-done.md` | Product/OKR 打回不实涨分，明确下一轮不得再做 Micro-only status/readback。 | 本轮启动窄 Epic，四个 owner 各交一个 artifact；资源缺失写 CEO blocker，不再拆成小 readback sprint。 |

最近两轮没有新的同根 blocker 被允许继续消费；反复出现的真实材料缺口是：PC 同源未复验、continuous radar/SLAM 未证明、真实/受控电梯图片缺失、stop-first HIL 现场授权缺失。本轮必须把这些缺口转为 artifact 或 CEO 决策 blocker。

## Owner 和并行边界

并行方式：四个 owner 可并行启动，因为 artifact、文件范围和验收命令互不重叠；Robot Software 负责 8787/ROS2 runtime，Full-stack 负责 PC 同源，Robot Algorithm 负责电梯图片/eval，Hardware Infra 负责 stop-first HIL 决策门。

接口边界：

- Full-stack 不改 radar collector，只证明 PC 同源按钮/API 到 live 8787 的链路。
- Robot Software 不改 PC UI，只证明 continuous radar/status 或 SLAM `/map` lifecycle。
- Robot Algorithm 不改状态机主链路，只交真实/受控电梯图片 manifest 与 OpenCV eval。
- Hardware Infra 不在安全条件不足时发运动命令；只做 stop-first HIL preflight 和 CEO blocker 判断。

## CEO blocker 记录口径

- 无法取得真实/受控电梯图片时：在后续 `tech-done.md`/`final.md` 记录 `blocked_with_root_cause=missing_real_or_controlled_elevator_images`、需要 CEO 提供拍摄场地/图片/授权，禁止写成 O2/O9 完成。
- 无法现场 HIL 时：记录 `blocked_with_root_cause=hil_safety_preconditions_not_met`，列出缺失的现场看护、净空、急停、授权或远端连接条件；禁止写成 HIL pass 或 `safe_to_control=true`。
- SSH 不可达或 8787 不可达时：记录 `blocked_with_root_cause=upper_ssh_or_8787_unreachable`，使用入口 `ssh root@192.168.1.11 -p 37878` 复核。

## 进入实现条件

`prd.md` 和 `tech-plan.md` 写清单 artifact 验收命令后即可派四个 L2 Engineer 并行执行。本轮 Product 只做计划与验收口径，不写产品代码。
