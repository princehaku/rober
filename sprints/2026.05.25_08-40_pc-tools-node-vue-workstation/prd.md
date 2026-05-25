# PC Tools Node/Vue Workstation PRD

## 产品目标

把 `pc-tools/` 第一阶段从脚本堆叠整理成 PC-only Node.js + Vue 工作站：保留现有 Python evidence/route 工具和旧 gate，在其上新增一个统一入口，服务开发者、算法调试者和证据复盘者。

工作站第一阶段不是替换 ROS2、不是手机端、不是云端生产控制台，而是本地 PC 上的可视化工具壳：

- 看路线：只读 route debug 和固定路线数据状态。
- 找工具：索引 evidence gate、route gate 和常用证明脚本。
- 留入口：预留训练/标注/数据集工作区，但只做占位，不伪造模型训练能力。
- 讲边界：持续显示 `software_proof` / `not_proven` / `safe_to_control=false` 等证据边界。

## 用户与场景

目标用户：

- Robot/Algorithm engineer：需要调试路线、关键帧、路径学习数据和任务证据。
- Full-stack engineer：需要统一 PC 工具入口、API 契约和可测试 UI。
- Product/Reviewer：需要从 PC 页面看清哪些只是软件证明、哪些还没有真实现场材料。

核心场景：

1. 工程师打开 PC 工作站，看到 `pc-tools` 能力地图，而不是在大量 Python 文件名里找入口。
2. 工程师进入 Route Debug，只读查看当前可解析的路线调试数据、状态、失败原因字段和来源说明。
3. 工程师进入 Evidence Tools，按类别查看现有 evidence gate、测试入口和证明边界，不删除也不绕过旧 Python gate。
4. 工程师进入 Training/Labeling，占位看到未来训练、标注、样本集入口，但所有动作标记为未接入。
5. Reviewer 在页面上明确看到本工作站不证明真实 ROS2、Nav2、硬件、HIL、手机或云端生产链路。

## 第一阶段功能范围

### 必须交付

- 新增 `pc-tools/workstation/`，使用 Node.js + Vue 构建 PC-only app。
- 提供本地 API，至少支持：
  - 工作站健康状态。
  - evidence 工具索引。
  - route debug 只读摘要。
  - proof boundary 摘要。
- 提供 Vue UI，至少包含：
  - 左侧或顶部导航：Route Debug、Evidence Tools、Training/Labeling、Proof Boundary。
  - Route Debug 页面：只读展示路线调试摘要、数据来源、失败/缺失状态，不触发 ROS2 或硬件动作。
  - Evidence Tools 页面：索引现有 Python evidence 工具，展示脚本名、类别、用途、是否有测试文件。
  - Training/Labeling 页面：仅占位，显示未接入训练、未接入标注、未接入数据上传。
  - Proof Boundary 页面：明确 `software_proof` 范围和未证明事项。
- 保留现有 `pc-tools/evidence/`、`pc-tools/route/` Python 文件和旧 gate，不删除、不改语义、不绕过测试。
- 同步更新 `docs/product/pc_tools_workstation.md`。

### 可选交付

- 为 evidence 工具索引提供分类规则，例如 route、field evidence、hardware evidence、mobile proof、cloud proof。
- 为 route debug 页面提供 fixture/sample 空状态，避免没有数据时页面不可用。
- 提供 `npm run dev` 方便本地开发，但验收以 build/test/lint 为准。

### 明确不做

- 不改 ROS2 package、不接真实 `/cmd_vel`、`/odom`、`/imu/data` 或 `/battery`。
- 不接 WAVE ROVER、ESP32、Orange Pi、UART、串口、波特率或任何硬件配置。
- 不改现有 Python evidence gate 和 route gate。
- 不声称 Nav2/fixed-route runtime pass、HIL pass、真实手机/browser proof、4G/云/OSS/CDN proof。
- 不实现真实训练、真实标注流水线、真实模型管理或数据上传。
- 不做手机端替代；普通用户手机入口仍归属 mobile/web，不归属 PC 工作站。

## 验收口径

第一阶段完成后，必须满足：

- `pc-tools/workstation` 可安装依赖、构建、测试、lint。
- Python route 旧 gate 仍可通过 unittest discovery。
- UI 文案清楚区分 PC 工作站、软件证明和未证明事项。
- API 返回只读状态，不包含硬件控制、ROS2 topic 写入或云端生产动作。
- 技术注释必须使用中文，且新增代码注释比例超过 20%；注释解释边界、原因和复杂逻辑，而不是重复代码表面行为。
- docs 已同步，且没有无证据提升 `OKR.md` 完成度。

## 失败与降级

- 若 Node/Vue 构建失败：由 `full-stack-software-engineer` 定位依赖、构建配置、TypeScript/Vue 或测试环境问题并重试。
- 若 Python route unittest 失败：不得删除旧 gate，应定位是工作站集成引入路径污染，还是旧测试在当前环境存在独立问题。
- 若无法运行 Node 命令：必须记录 Node/npm 版本缺失或依赖安装失败，不能把环境缺口写成产品完成。

## 成功定义

本阶段成功不是"PC 工具全部重写完"，而是形成一个可运行、可测试、边界清楚的 Node/Vue 工作站骨架，让后续 route debug、标注、训练、证据复盘都能进入同一架构入口，并且旧 Python gate 不被破坏。

