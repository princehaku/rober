# PC Tools Node/Vue Workstation Pre-start

## Sprint 声明

sprint_type: epic

- 启动时间：2026-05-25 08:40
- CEO 原话："./pc-tools 这里都是垃圾代码，没有架构，重构一下；因为是 PC 用的，所以用 Node.js 和 Vue 重构"
- 本轮 Product Owner 目标：创建 Epic sprint 计划链路，明确 PC-only Node.js + Vue 工作站第一阶段范围、验收口径、执行 owner 和证据边界。
- 本轮不进入实现：只产出 `pre_start.md`、`prd.md`、`tech-plan.md` 和产品说明文档，后续由 `full-stack-software-engineer` 执行实现、测试和修复。

## 背景与问题

`pc-tools/` 当前已经沉淀大量 Python evidence gate、route gate 和测试，但目录更像脚本堆叠：

- evidence 工具数量多，缺少统一 PC 入口、分类索引和可读状态说明。
- route debug 已有 Python 工具和测试，但没有统一的 PC 工作站 UI/API 作为后续路径学习、打标、展示、训练入口。
- 旧工具里大量 `software_proof`、`not_proven`、`safe_to_control=false` 等安全边界是已有资产，重构不能删除旧 gate，也不能把第一阶段 UI/API 误包装为真实 ROS2、硬件、Nav2、HIL、手机或云端证明。

本轮选择 PC-only Node.js + Vue，是因为 PC 端定位是开发/标注/训练/展示工作站，不是普通手机用户入口，也不是车端 runtime。Node.js 提供本地 API 与工具索引能力，Vue 提供统一可视化工作台。

## Owner 与协作边界

- Product Owner：本轮负责 PRD、范围、验收口径和 sprint 留档。
- 主责执行 owner：`full-stack-software-engineer`，后续负责 `pc-tools/workstation/` Node/Vue app、API、UI、测试和 docs 同步。
- 咨询 owner：`robot-software-engineer` 或 `robot-algorithm-engineer` 可在后续实现前只读确认 route debug 数据契约；本轮不要求他们改代码。
- 禁止改动：现有 Python evidence/route gate、硬件配置、ROS2 runtime、手机端、云端生产链路。

## 本轮范围

本轮只允许改动：

- `sprints/2026.05.25_08-40_pc-tools-node-vue-workstation/`
- `docs/product/pc_tools_workstation.md`
- `OKR.md` 可新增说明，但不得无证据提升完成度

本轮实际计划不修改 `OKR.md`，因为没有新增可运行产品代码、测试通过证据或真实证明材料。

## 预期产物

- `pre_start.md`：锁定 sprint 类型、CEO 需求、owner、范围和风险。
- `prd.md`：明确第一阶段 PC 工作站用户价值、页面/API 能力、非目标和验收口径。
- `tech-plan.md`：明确后续实现目录、推荐架构、接口边界、验证命令、并行规则和 OKR 最低优先级核对。
- `docs/product/pc_tools_workstation.md`：同步产品定位和第一阶段边界，供后续工程实现引用。

## Blocker 扫描

- 最近有效 sprint `2026.05.25_01-03_repo-wide-structure-comment-refactor/final.md` 主结论为已完成结构治理，Docker/Humble 未验证根因是当前环境没有 Docker CLI，不是本轮 PC 工作站规划 blocker。
- 本轮不消费 Docker registry、真实串口、WAVE ROVER、HIL、OSS/CDN、真实手机等 blocker。
- 本轮若后续实现失败，应优先定位 Node/Vue app 本地构建、测试或 lint 问题，不得把 PC-only 骨架失败转写成硬件 blocker。

## 证据边界

本轮计划和后续第一阶段实现只能证明：

- `pc-tools/workstation` 作为 PC-only Node.js + Vue 统一入口能本地启动、构建、测试、lint。
- UI/API 能只读展示 route debug、evidence 工具索引、训练/标注占位入口和软件证明边界。
- 旧 Python evidence/route gate 被保留，并可继续通过既有 unittest 验证。

本轮不能证明：

- 真实 ROS2 runtime、Nav2/fixed-route 现场通过、WAVE ROVER/UART/HIL、真实硬件控制、真实手机/browser、4G/云端/OSS/CDN、真实投放或真实交付成功。

