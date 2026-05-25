# PC Tools Node/Vue Workstation Tech Plan

## 目标架构

在 `pc-tools/workstation/` 新增 PC-only Node.js + Vue 工作站。第一阶段采用本地单体结构：

- Node.js API：读取 `pc-tools/evidence/` 和 `pc-tools/route/` 的文件清单、测试配对和只读摘要。
- Vue UI：提供 Route Debug、Evidence Tools、Training/Labeling、Proof Boundary 四个入口。
- 旧 Python gate：继续保留在 `pc-tools/evidence/` 和 `pc-tools/route/`，不删除、不重命名、不改变 CLI 语义。
- 软件证明边界：所有 API/UI 默认声明 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

推荐技术选型由执行 owner 在实现前结合仓库现状确认：

- Vue 3 + Vite + TypeScript。
- Node.js API 可使用 Express/Fastify 或 Vite dev middleware 分离实现；若选择单进程，必须保证 build/test/lint 命令清楚。
- 测试可使用 Vitest；UI 组件测试和 API 单元测试优先覆盖边界字段、工具索引和 route empty state。
- lint 可使用 ESLint，规则保持轻量，避免为第一阶段引入过重框架。

## 文件范围

后续实现允许改动：

- `pc-tools/workstation/**`
- `docs/product/pc_tools_workstation.md`
- 当前 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`

后续实现禁止改动，除非另开 sprint 或 CEO 明确授权：

- `pc-tools/evidence/**` 现有 Python gate 和测试
- `pc-tools/route/**` 现有 Python gate 和测试
- `onboard/**`、`mobile/**`、`cloud-relay/**`
- 硬件配置、ROS2 launch、串口参数、vendor 文档事实

## API 契约

第一阶段至少提供以下只读接口。路径可由执行 owner 按框架习惯调整，但语义必须保持：

- `GET /api/health`
  - 返回工作站版本、运行模式、PC-only 声明。
- `GET /api/tools/evidence`
  - 返回 evidence Python 工具索引：文件名、类别、是否存在 `test_*.py`、是否属于 hardware/cloud/mobile/route/field evidence 类。
- `GET /api/route/debug-summary`
  - 返回 route debug 摘要、数据来源、缺失字段、只读状态。
  - 不调用 ROS2，不打开串口，不写文件，不触发导航。
- `GET /api/proof-boundary`
  - 返回软件证明边界和未证明事项列表。

所有 API 必须包含或可追溯到以下边界字段：

- `source: "software_proof"`
- `proof_status: "not_proven"`
- `safe_to_control: false`
- `delivery_success: false`
- `primary_actions_enabled: false`
- `pc_only: true`

## UI 信息架构

页面必须以工具工作站为第一屏，不做营销页：

- Route Debug：展示 route 只读摘要、数据源、缺失状态、最近可用测试入口说明。
- Evidence Tools：按类别列出现有 Python 工具和测试配对，提供只读索引，不提供执行按钮作为第一阶段必需项。
- Training/Labeling：展示训练、标注、样本集入口占位，明确"未接入真实训练/标注"。
- Proof Boundary：展示软件证明能证明什么、不能证明什么，避免 reviewer 或后续 agent 误读。

UI 必须是 PC 工具风格：密度适中、信息可扫描、导航明确、避免移动端一键任务文案。不要把 PC 工作站做成普通用户手机控制台。

## 工程约束

- 新增代码中的技术注释必须使用中文，注释比例超过 20%。
- 注释应解释边界和原因，例如为什么 API 只读、为什么不执行 Python gate、为什么 proof boundary 必须 fail-closed。
- 工作站不得直接执行硬件控制、ROS2 topic 写入、真实导航、云端生产命令。
- 旧 gate 保留为外部资产；第一阶段可以读取文件清单和只读摘要，但不能替代旧 gate 的判定权威。
- 若需要 sample/fixture，只能明确标记为 sample 或 empty state，不得伪造成真实现场材料。

## 验收命令

后续 `full-stack-software-engineer` 必须执行并记录输出：

```bash
cd pc-tools/workstation && npm install
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
python -m unittest discover pc-tools/route -p "test_*.py"
```

如任一命令失败，执行 owner 必须先定位根因、修复并重跑；不能把第一轮失败直接作为最终结果。

## 并行与执行计划

本 sprint 是 Epic。实现阶段建议按以下方式派发：

1. `full-stack-software-engineer` 主责实现 `pc-tools/workstation/**`、Node/Vue UI/API、测试、lint 和 docs 同步。
2. 如 route debug 契约不清，可并行派 `robot-algorithm-engineer` 只读确认 `pc-tools/route/README.md`、`route_debug_web.py` 和 `test_route_debug_web.py` 的输入输出边界。
3. 如 evidence 证明边界不清，可并行派 `robot-software-engineer` 只读确认现有 `software_proof`、`not_proven`、`safe_to_control=false` 约束，不改 Python gate。

如果实现阶段只派 1 个子 agent，必须在 `tech-done.md` 说明原因：本阶段写范围集中在 `pc-tools/workstation/**` 和产品文档，其他 owner 只读咨询未形成独立改动面。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，上一轮 final 记录约 68%。
- 本 sprint 是否针对该 Objective：否。
- 理由：CEO 明确指定 `pc-tools` PC 端重构；本轮主要对齐 Objective 3 的 PC 关键帧/route debug/路径学习工具能力，并为 PC 端打标、展示、训练入口打架构骨架。Objective 5 的云中转、4G、OSS/CDN、外部证明材料不在本轮 PC-only 范围内。
- final.md 收口时需复核：本轮是否仍未产生 Objective 5 真实云/外部证明证据，是否仍不得提升 Objective 5 完成度。

## 风险与边界

- Node/Vue app 可能引入新的依赖和构建链路，后续必须用 npm build/test/lint 兜底。
- 只读索引如果直接扫描大量 Python 文件，需避免路径硬编码和 Windows/macOS/Linux 路径差异。
- 第一阶段不做真实训练/标注，必须在 UI 上清楚显示占位状态，避免产品误读。
- 本计划不涉及硬件事实，因此无需查阅 `docs/vendor/VENDOR_INDEX.md`；后续若任何实现触及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、反馈协议、引脚、电压、固件或机械尺寸，必须重新查阅 vendor index 并在代码或说明中标源。

