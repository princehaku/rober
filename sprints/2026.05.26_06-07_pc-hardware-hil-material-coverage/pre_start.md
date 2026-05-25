# PC Hardware HIL Material Coverage Pre-Start

## 1. Sprint 声明

- sprint_type: epic
- sprint_id: `2026.05.26_06-07_pc-hardware-hil-material-coverage`
- Automation ID: `daily-bug-scan`
- 启动时间：2026-05-26 06:00-07:00 Asia/Shanghai
- 当前阶段：planning
- 产品负责人：`product-okr-owner`
- 实现主责：`full-stack-software-engineer`
- 硬件事实咨询：`rober-hardware-engineer`

本轮不做产品代码、测试代码、硬件配置或 `OKR.md` 改动。Product 只创建 `pre_start.md`、`prd.md`、`tech-plan.md`，为后续 Engineer 并行执行提供清晰范围、验收命令和证据边界。

## 2. 用户价值和产品北极星

北极星仍是：让 `rober` 变成普通手机用户能信任的低成本自主垃圾投递机器人。Objective 1 的当前价值短板不是继续重复写“缺真实硬件”，而是让 PC 工作站能把现有 WAVE ROVER/HIL 材料扫描清楚，告诉团队哪些 required materials 已覆盖、哪些缺口仍是 `not_proven`，避免评审、硬件履约和 OKR 进度被散落 fixture 卡住。

本轮用户价值：

- CEO / Product 能在 PC 工作站看到 WAVE ROVER HIL/material coverage 的只读状态，而不是靠口头问“材料齐了吗”。
- Hardware 能按同一张缺口表补材料，减少 PR #5 / HIL 证据反复消费。
- Full-Stack 保持 Node/Vue 主入口，不恢复旧 Python evidence gate，降低架构漂移。

## 3. 上轮事实和重复 blocker 红线

已核对事实：

- `OKR.md` 4.1 当前最低完成度为 Objective 5 约 76%，但本轮 CEO 指定重心推进 Objective 1 可执行证据链；Objective 1 当前约 81%，仍低于 Objective 2/3/4 的约 99%。
- 用户明确给定：最近多轮 Objective 1 主要风险反复是缺真实 WAVE ROVER/UART/HIL/2D LiDAR/ToF/PR #5 材料，本轮不能把“缺真实硬件材料”再次作为主结论消费。
- 最近 PC 工作站 sprint 已完成 Node/Vue 主入口，旧 Python evidence gate 已删除，`pc-tools/evidence/fixtures/**` 保留为非 Python 证据资产。
- 当前工作树只有 `.idea/rober.iml` 未暂存，属于本轮无关改动，不触碰、不回滚。

因此本轮不以“没有真硬件所以 blocked”收口；必须交付一个本地可执行的 coverage/readiness 只读能力，让缺口从 blocker 变成可排序、可补齐、可复核的材料清单。

## 4. 目标和核心抓手

产品目标：在 `pc-tools/workstation` 中新增 Node/Vue WAVE ROVER HIL/material coverage 只读能力，扫描已有 `pc-tools/evidence/fixtures/wave_rover_*` 材料，展示 required materials 覆盖、缺口和 `not_proven` 边界。

核心抓手：

- 扫描 `pc-tools/evidence/fixtures/wave_rover_*`，识别可用材料组、文件类型和 fixture pass/fail 语义。
- 定义 required materials coverage：五件套必须精确覆盖 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report`；其他 review/intake/execution pack 类 JSON 只能作为辅助上下文。
- UI/接口明确 fail-closed：材料存在不等于 HIL 通过，不等于 WAVE ROVER/UART 真机验证，不等于 delivery success。
- 保持 Node/Vue 主入口：禁止恢复 `pc-tools` 旧 Python evidence gate。

## 5. Owner 分工

| Owner | 职责 | 允许动作 |
| --- | --- | --- |
| `product-okr-owner` | 本轮 sprint 启动、PRD、tech-plan、后续 closeout/OKR/sprint 文档 | 只改 sprint 文档；实现完成后再更新 `tech-done.md` / `side2side_check.md` / `final.md` / `OKR.md` |
| `full-stack-software-engineer` | 实现 Node-native scanner/API/UI/tests/docs | 修改 `pc-tools/workstation/**`、必要时更新 `pc-tools/evidence/README.md` 和 `docs/product/pc_tools_workstation.md` |
| `rober-hardware-engineer` | 只读确认 required materials 和 vendor/source 事实边界 | 读取 `docs/vendor/VENDOR_INDEX.md` 及指向资料，返回材料清单建议；不改硬件配置 |

## 6. 风险、阻塞和证据链缺口

- 真实 WAVE ROVER/UART/HIL、2D LiDAR、ToF、PR #5 reviewer resolution 仍未由本轮直接证明；本轮只把现有材料 coverage 可视化、结构化。
- `wave_rover_*` fixture 文件可能只是软件证明或脱敏样例，不能被 UI 解释为真机通过。
- 如果 required materials 定义不清，Hardware 必须先用 vendor/source 事实补充材料类别，Full-Stack 不得自己发明硬件结论。
- 任何新增代码技术注释必须中文，且注释比例超过 20%；Product closeout 需要把这点纳入验收。

## 7. 本轮需要创建或更新的 sprint 文档

计划阶段创建：

- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/pre_start.md`
- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/prd.md`
- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/tech-plan.md`

实现完成后继续更新：

- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/tech-done.md`
- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/side2side_check.md`
- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/final.md`
- `OKR.md`
- 相关 `docs/` 文档：预计 `docs/product/pc_tools_workstation.md`，必要时 `pc-tools/evidence/README.md` 作为工具边界文档补充。
