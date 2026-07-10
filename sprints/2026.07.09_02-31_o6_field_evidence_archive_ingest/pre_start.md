# O6 Field Evidence Archive Ingest Pre Start

- sprint_type: epic
- time: 2026-07-09 02:31 Asia/Shanghai
- target_objectives: O6, O7
- primary_owner: full-stack-software-engineer
- support_owner: robot-software-engineer
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false

## 上轮与当前状态

最近两轮 `2026.07.09_00-53_pc_keyboard_motion_condition_split` 和 `2026.07.09_01-52_pc_keyboard_realtime_hold_watchdog` 都在 O7 PC 键盘手控体验上推进，验证边界仍是 PC/Vitest/build 与远端只读部署，未做真实长按 HIL。

当前 `OKR.md` 4.1 最低完成度为 O6/O7 并列约 30%。O7 最近已连续多轮消费 PC 手控和现场相机/轮速风险；本轮切换到 O6/O7 共享的数据主链，避免继续围绕真实相机、wheel raw 或现场长按复验 blocker 打转。

## 本轮目标

把 `trashbot.field_evidence_manifest.v1` 现场材料入口转成 O6 local/mock archive 可读任务，再由 O7 consumer read 主路径消费。目标是形成：

1. field evidence manifest / route.csv / replay JSONL 的只读归档输入。
2. O6 archive store 中 task、trajectory、events、evidence_refs、field_evidence 的可查询读模型。
3. PC O7 consumer detail 能显示这条来源，并继续保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 范围边界

- 不连接真实 production DB/queue、OSS/CDN、TLS/4G 或公网云。
- 不 SSH 上车、不读取串口、不启动 ROS2 runtime、不发 `/cmd_vel`。
- 不把 manifest gate、no-motion route 或 mock archive 解释为真实 delivery success。
- 使用本地/mock/file-backed store 完成软件证明。

## Blocker 核对

最近两轮不是同一 `final.md` blocked 结论；当前风险主要是 O7 真实 HIL 未复验。本轮不继续消费该现场 blocker，转向不依赖真实硬件的软件链路。

## Owner 分工

- `robot-software-engineer`：负责 field evidence manifest 到 O6 archive seed payload/CLI 或 helper 的生成、测试和导航/接口文档同步。
- `full-stack-software-engineer`：负责 cloud-relay/O6 HTTP ingest 或 PC O7 consumer read 入口接入、测试和产品/接口文档同步。

## 验收口径

- 能从本地 fixture/真实历史 artifact 生成 O6 archive seed。
- 能通过 local/mock cloud relay 写入并读回 O6 consumer detail。
- O7 PC adapter/UI 能读取对应 detail，且危险能力字段全为 false。
- 文档和 `tech-done.md` 记录实际改动、验证输出和剩余风险。
