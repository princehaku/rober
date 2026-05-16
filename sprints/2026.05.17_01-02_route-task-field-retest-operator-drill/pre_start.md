# Sprint 2026.05.17_01-02 Route Task Field Retest Operator Drill - Pre Start

sprint_type: epic

## 1. 启动背景

本轮按自动化 `skill-progression-map` 启动下一轮迭代，目标是根据近期 PR 和评审继续推进 OKR，优先选择当前完成度低且 Docker-only 环境可执行的方向。

当前 `OKR.md` 4.1 快照更新时间为 2026-05-17 00:19 Asia/Shanghai：

- Objective 1：约 75%
- Objective 2：约 85%
- Objective 3：约 85%
- Objective 4：约 94%
- Objective 5：约 66%

Objective 5 数值最低，但本机没有真实硬件、真实 4G/SIM、真实公网 HTTPS/TLS、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。继续堆本地 O5 metadata wrapper 不能形成真实 O5 外部 proof。本轮切换到 Objective 2 / Objective 3 的 route/task field retest operator drill，服务于真实材料到位后的同一 `evidence_ref` 执行和复账。

## 2. 近期 PR / 评审证据

- PR #4 `Add elevator-assisted delivery capability to agents, registry and OKR`：把 elevator-assisted delivery 写入主链路，要求状态机和证据链覆盖门状态、目标楼层、人工协助边界和失败解释。
- PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline`：进一步把跨楼层送垃圾和硬件传感 baseline 写入 OKR、agent prompt 和产品约束。
- PR #5 Codex review P1：`docs/product/production_hardware_boundary.md` 的默认硬件集合与 `monocular + 2D LiDAR + ToF` mandatory baseline 曾存在矛盾，导致后续 BOM/procurement/bringup 容易漏传感器。
- PR #5 Codex review P2：mandatory sensor baseline 缺 vendor source 引用，说明硬件和现场材料链路必须继续保留本地资料来源与 evidence boundary。
- 最新 sprint `2026.05.17_00-01_route-task-field-retest-material-pack/final.md`：material pack 已能校验八类现场材料目录，但下一步仍缺真实同一 `evidence_ref` 的 material directory，并建议若无 O5 外部材料，则继续围绕真实现场材料回填和复账推进。

## 3. 本轮目标

新增 `route_task_field_retest_operator_drill`：

- PC 侧读取上一轮 `route_task_field_retest_material_pack` artifact / summary，生成可执行的 operator drill artifact / summary。
- Drill 必须串联 material pack -> result intake -> result reconciliation 的命令、输入输出文件、同一 `evidence_ref`、缺失材料和下一步补证据动作。
- Robot diagnostics 只消费 metadata-only summary，不启用 collect / dropoff / cancel / ACK / Nav2 / HIL。
- mobile/web 只读展示“现场操作演练”，让现场人员能理解下一条命令、材料缺口和 proof boundary。

## 4. Owner 与并行策略

本轮是 Epic sprint，默认 4 owner 并行：

- Task A Autonomy：PC operator drill gate。
- Task B Robot：diagnostics metadata-only consumer。
- Task C Full-stack：mobile/web 只读 panel。
- Task D Product：closeout、OKR、progress log 和证据边界收口。

文件范围互不重叠，按 AGENTS.md 并行启动强制规则执行。

## 5. 风险与边界

- 本轮仍是 Docker-only software proof，不是真实 route/elevator field pass。
- 不声明真实 Nav2/fixed-route、真实电梯、真实 dropoff/cancel completion、delivery success、真实手机/browser、WAVE ROVER、UART、HIL 或 Objective 5 external proof。
- 不第三次消费 PR #5 硬件 source/config blocker；硬件材料只作为风险与后续真实材料缺口记录。
