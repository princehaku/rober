# O6 Labeling API Epic Pre-Start

## sprint_type

sprint_type: epic

## 用户价值与北极星

北极星是让 O7 功能链在真实生产化前就能有统一、可验证的数据输入与回路：路线回放、异常复盘、标注与训练队列都从同一份 O6-shaped 数据形状消费。前两轮已把 archive 存档 API 建好，本轮继续往前补齐**标注回路**，把 `O6 archive` 的 `tasks` 变成可供 `PC labeling queue` 消费与提交审核反馈的状态体。

本轮价值不在于“已经上线打标平台”，而在于“把真实 O7 标注能力能做的最小接口轮廓、字段边界与 fail-closed 规则冻结”，避免下游反复变更与 UI/后台误读成 production。

## OKR 映射与方向判断

- 当前最低 Objective：`O6：云端核心后端——数据存档、模型推理与打标平台`
- 4.1 快照仍是 `O6：0%`，优先级排序中 O6 仍是最低。
- 本轮方向：**继续推进（continue）O6**，聚焦 `KR4`。
- 判断依据：
  - O7 路线回放和标注页已经有前置契约占位（`labeling_queue_snapshot`/`archive` 预览），但缺少可提交与查询标注结果的 local/mock API。
  - 目前唯一可闭环的工程证据是 local/mock O6 archive；在不接生产云 DB/OSS 的边界下，先补齐 `KR4` 的软件形状比直接转向其他 KR 风险更低。

## 本轮覆盖的 KR 与历史归档

### 本轮目标 KR

- `O6-KR4`：提供数据打标/标注 API，支持 PC 提交与查询标注结果。

### 已完成 KR 说明（本轮不复写）

- `O6-KR2 / KR3 / KR6` 的软件证据在上一轮记录：
  - `sprints/2026.06.09_01-02_o6-cloud-archive-api/tech-done.md`
  - `sprints/2026.06.09_01-02_o6-cloud-archive-api/pre_start.md`

### 本轮不覆盖 KR

- `KR1`（隧道/在线离线连通）
- `KR5`（模型推理接口）
- 真实 OSS、生产 cloud DB/queue、真实训练集导出、真实 robot 控制与 HIL

## 本轮核心抓手

把 O7 标注回路的接口形状写死为：

- `POST /api/o6/archive/labels`：提交/更新标注结果，idempotent upsert。
- `GET /api/o6/archive/labels`：按任务查询“待标注/已标注”安全摘要。
- `GET /api/o6/archive/labels/<task_id>`：按 task 查询标注详情。
- 固化 boundary 字段和 fail-closed 语义：禁止把 local/mock 当 production、禁止控制/云存储/训练成功语义。
- 文档固定：`docs/interfaces/o6_cloud_archive_api.md` 与 `docs/product/pc_tools_workstation.md` 的 API 边界。

## 优先级

P0：冻结 labeling API contract + fail-closed 规则（坏 JSON、缺字段、数组过大、unsafe、越权/未知 task_id）。

P1：定义可复用的 O7 安全摘要（待标注 vs 已标注）与上游消费入口。

P2：收口阶段前不引入真实数据库、真实云标注服务、真实训练导出。

## Owner 与执行方式

- Owner：`product-okr-owner`
- 主责实现：`full-stack-software-engineer`
- 咨询角色：默认不需要硬件 / ROS2 / 算法并行。

## 预期交付文档

- `pre_start.md`：本文件。
- `prd.md`：业务需求与验收口径。
- `tech-plan.md`：接口范围、验收命令、风险边界与提交规则。

## 启动风险

- 本轮是设计/验收阶段，不改代码、不跑大规模测试。
- 现有 O6 archive 逻辑已固定 `not_proven local mock boundary`，新接口不能改写为 production 语义。
- `task_id` 未在 archive store 存在时，必须 fail-closed，不能自动创建或回填到“空任务”。
