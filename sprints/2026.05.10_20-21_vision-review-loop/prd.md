# Sprint 2026.05.10 20-21 Vision Review Loop - PRD

## 状态

- 阶段：prd completed。
- 时间：2026-05-10 20:12 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现 owner：`full-stack-software-engineer`。

## 背景

当前 vision review queue 对 operator 来说是“能看不能判”，这让人工复核停在口头流程：看到可疑样本后只能线下记录，无法在系统中留下标准化 decision。结果是 Objective 4 的“感知模块产品化”长期卡在只读证据层。

## 用户价值和产品北极星

- 用户价值：让 operator 在一个入口内完成“查看样本 -> 人工判定 -> 落盘留痕 -> 状态更新”，减少跨系统沟通成本。
- 北极星一致性：机器人要面向普通用户持续运行，感知链路必须可复盘，不应依赖工程师临时手工记录。

## OKR 映射

- Objective 4（主）：
  - KR3：视觉样本/manifest contract 从可读升级到可执行复核闭环。
  - KR4：行为层依赖稳定感知契约；人工判定成为产品化闭环一环。
- Objective 5（次）：
  - 提升 operator 端触点效率，降低复核操作门槛。

## KR 拆解或更新

- KR-A：新增 `review decision` 接口 contract，支持 `approved` / `rejected` / `needs_retry`。
- KR-B：新增 decision 落盘 contract（结构化 JSON 行或等价结构），可用于后续审计与统计。
- KR-C：queue 增加 decision 状态字段，显示未判定/已判定及最后一次判定摘要。
- KR-D：关键护栏测试覆盖成功、非法输入、目标缺失、写入失败场景。

## 本轮核心抓手

- 抓手 1：先打通最小闭环（UI 提交 + API 写入 + queue 回显），不扩展复杂工作流。
- 抓手 2：定义稳定 decision schema，防止后续分析口径漂移。
- 抓手 3：保持“测试仅护栏”，只补关键 contract 和失败路径。

## 做什么 / 不做什么

做：

- 增加 review decision 的提交入口与后端处理。
- 增加 decision 落盘和读取回显。
- 增加必要护栏测试。

不做：

- 不做真实硬件/HIL，不宣称相机或整机实测能力。
- 不做模型训练、自动化打标平台、跨设备同步。
- 不做大规模 UI 重构。

## 产品需求

- Operator 对每个 queue 样本可提交人工判定。
- 判定最少包含：`sample_id`、`decision`、`timestamp`，可选 `reason/comment`、`operator`。
- 同一样本重复提交时有明确策略（幂等覆盖或冲突提示，需在实现时固定）。
- 判定结果可追溯到源样本引用（manifest 路径或样本 ref）。
- queue 端可见判定状态，支持快速筛选未处理项（如当前实现允许）。

## 非功能需求

- 失败可恢复：写入失败返回结构化错误，不崩溃主流程。
- 数据可审计：落盘格式稳定，后续可被工具读取。
- 低侵入：改动限定在 operator/vision-review 相关路径。
- 测试护栏：仅覆盖关键 contract 与失败路径，控制改动速度。

## 优先级和验收口径

- P0：review decision 提交成功并落盘。
- P0：queue 能回显已判定状态。
- P0：关键护栏测试通过。
- P0：本轮文档与实现边界一致，不越界到 HIL。
- P1：错误提示文案清晰、便于 operator 处理。

## 对应责任 Engineer

- 实现与验证 owner：`full-stack-software-engineer`。
- Product 只负责口径与验收，不直接写实现。

## 风险、阻塞和证据链

- 风险：decision 字段不规范导致后续统计不可用。
- 风险：并发操作导致判定冲突。
- 阻塞：现有 queue 样本若缺唯一标识，需要先补齐 ID 规则。
- 证据链缺口：本轮只证明软件链路前进，不包含硬件/HIL。

## 需要创建或更新的 sprint 文档

- 本轮计划文档：`pre_start.md`、`prd.md`、`tech-plan.md`（已 completed）。
- 实现收口文档：`tech-done.md`、`side2side_check.md`、`final.md`（待实现后更新）。
