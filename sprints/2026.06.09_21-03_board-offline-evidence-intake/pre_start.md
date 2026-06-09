# Board Offline Evidence Intake Sprint Pre-start

## sprint_type: epic

## 触发背景

CEO 要求开始新一轮迭代，先完成只读设计与 sprint 启动判断，设计好再写功能点，结束时提交并推送。本轮开工前已按要求读取：

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.06.09_20-21_board-live-evidence-capture/final.md`
- `sprints/2026.06.09_18-19_board-evidence-to-archive-consumer/final.md`

最近两轮相关结论显示，当前开发机到真实上位机入口：

```bash
ssh root@192.168.1.11 -p 37878
```

仍失败于同一网络根因：`No route to host` / `blocked_ssh_unreachable`。按 `AGENTS.md` 和 `docs/process/iteration_velocity.md` 的同一 blocker 重复消费红线，从第 3 轮起不能继续把连通 `192.168.1.11:37878` 作为主目标反复消费。本轮必须切换到不依赖该 SSH 可达性的可验证工作，或升级 CEO 求网络/现场入口决策。

## Blocker 重复消费判断

- blocker_root_cause: `board_ssh_192_168_1_11_37878_unreachable`
- 最近消费记录：
  - `sprints/2026.06.09_20-21_board-live-evidence-capture/final.md`：主状态为 `blocked_live_ssh_unreachable_with_fallback_evidence_ready`，真实 SSH 返回 `No route to host`。
  - `sprints/2026.06.09_18-19_board-evidence-to-archive-consumer/final.md`：软件闭环通过，但真实 SSH 路径仍输出 `status=blocked_ssh_unreachable`，未补齐真实 `map.yaml/route.csv/keyframes/rosbag/replay.jsonl`。
- 本轮判断：**不再把真实 SSH 连通作为 P0 验收或主路径**。真实 SSH 只保留为可选附加检查；主路径切换为“现场人工导出材料 / 离线 evidence packet 导入 / manifest gate 复用”。

## 用户价值和北极星

用户价值仍是让普通手机用户最终能把垃圾交给小车，小车按真实路线送达并可复盘。当前最短路径不是继续等待同一 LAN/SSH 条件，而是把现场材料入口产品化：只要现场有人能导出 `map.yaml`、`route.csv`、keyframes、`route_bag/` 或 `replay.jsonl`，后续 O6 archive 与 O7 consumer 就能消费同一份证据，推进路线回放、标注和送达诊断。

## OKR 映射与方向判断

- 方向判断：**调整执行路径，继续推进现场证据链**。
- 切换前目标：真实上位机 live SSH route capture。
- 切换后目标：离线现场材料 intake，使 O3 现场证据、O6 archive、O7 consumer 不再被 `192.168.1.11:37878` 锁死。
- OKR 映射：
  - O6：云端核心后端需要真实/现场 evidence packet 作为 archive 与 consumer read 的输入。
  - O7：PC 端历史路线回放与标注队列需要可导入的 route/evidence 详情。
  - 归档 O3 现场 lane：本轮不宣称 O3 重新完成，只为真实材料补一条可落地交付路径。

## 本轮核心抓手

本轮设计一个下一步可派发的工程 sprint：`board_offline_evidence_intake`。

核心功能点是新增或补齐离线导入入口，让工程同学后续可以把一个本地 evidence packet 目录转换为既有 `trashbot.field_evidence_manifest.v1`，并复用 O6/O7 consumer 的 manifest gate，而不是必须先 SSH 到板子。

## Owner 与协作方式

- 主责 owner：`robot-software-engineer`
- 协作 owner：`full-stack-software-engineer`
- 只读咨询：`robot-algorithm-engineer`

协作判断：这是跨 owner Epic。`robot-software-engineer` 负责离线 intake/manifest glue 与集成验证；`full-stack-software-engineer` 负责 O6/O7 consumer 侧 fixture 或展示契约是否需要同步；`robot-algorithm-engineer` 只读确认现场材料最小集合和路线语义，不改 SLAM/Nav2 代码。

## 本轮非目标

- 不修改工程代码；本轮只完成产品设计和 sprint 启动判断。
- 不继续把 `ssh root@192.168.1.11 -p 37878` 作为 P0 阻塞项。
- 不新增 WAVE ROVER、UART、Orange Pi 引脚、电压、波特率、速度映射或底盘反馈假设。
- 不宣称真实 delivery success、真实 robot control 或真实 HIL 通过。

## 启动结论

建议启动下一轮 Epic 实现 sprint：`board_offline_evidence_intake`。只有当 CEO 明确要求继续攻坚同一 SSH blocker，或提供新的 host/port/VPN 条件时，才重置 blocker 计数并恢复 live SSH capture 为 P0。
