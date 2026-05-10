# Sprint 2026.05.10 20-21 Vision Review Loop - Tech Plan

## 状态

- 阶段：tech-plan completed。
- 时间：2026-05-10 20:12 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现 owner：`full-stack-software-engineer`。
- 执行方式：单 owner 单线闭环。

## 执行声明（主节点约束）

本 `tech-plan` 完成后，主节点不会自己写产品代码、测试代码或硬件配置；后续实现、测试、修复必须由 `full-stack-software-engineer` 子 agent 执行，并在 `tech-done.md` 回填证据。

## Goal

把 operator 端 vision review queue 从“只读提示”升级为“可执行人工复核闭环”：支持提交 review decision 并落盘，且 queue 能回显决策状态。

## Scope Boundary

- 只推进软件链路：operator UI/API/decision store/queue 状态。
- 明确不做真实硬件/HIL、上车验证、相机实测。
- 测试仅护栏：覆盖关键 contract 和失败路径，不做全量扩展。

## 文件范围

实现阶段允许 `full-stack-software-engineer` 修改（以实际代码结构为准，必须限制在 vision review/operator 相关文件）：

- operator queue API/handler 相关文件。
- operator 前端页面/静态资源中 vision review queue 相关文件。
- vision review queue 数据访问与 decision 落盘相关文件。
- 对应最小测试文件。
- `sprints/2026.05.10_20-21_vision-review-loop/tech-done.md`
- `sprints/2026.05.10_20-21_vision-review-loop/side2side_check.md`
- `sprints/2026.05.10_20-21_vision-review-loop/final.md`

禁止范围：

- 硬件驱动、底盘协议、串口参数、launch 硬件配置。
- vendor 文档与非本功能切片无关模块。
- 任何真实 HIL 相关配置或脚本改造。

## 接口设计

建议新增或扩展接口（命名以现有代码为准）：

- `POST /api/vision/review-decisions`
  - Request：
    - `sample_id` (string, required)
    - `decision` (enum: `approved|rejected|needs_retry`, required)
    - `reason` (string, optional)
    - `comment` (string, optional)
    - `operator` (string, optional)
  - Response：
    - `ok` (bool)
    - `decision_id` (string)
    - `sample_id` (string)
    - `decision` (string)
    - `stored_at` (ISO timestamp)
    - `error` (optional structured error)

- `GET /api/vision/review-queue`
  - 在现有样本结构上补充：
    - `review_status` (`pending|decided`)
    - `last_decision` (optional summary)
    - `last_decision_at` (optional)

落盘 contract（建议）：

- 文件：`review_decisions.jsonl`（或现有 store 的等价实现）
- 每行最小字段：
  - `decision_id`
  - `sample_id`
  - `decision`
  - `reason`
  - `comment`
  - `operator`
  - `source_ref`
  - `timestamp`

## 任务拆解（给 full-stack-software-engineer）

1. queue 数据模型补齐 `review_status` 与最近判定摘要。
2. 新增 review decision 提交接口与参数校验。
3. 新增 decision 落盘逻辑，保证失败时结构化报错。
4. 将 decision 写入结果回显到 queue。
5. 增加最小护栏测试：
   - 正常提交并落盘。
   - 非法 decision 被拒绝。
   - sample_id 不存在或不可处理。
   - 落盘失败时返回可读错误。

## 验收命令

本计划阶段验收命令（当前必须执行）：

```bash
git diff --check -- sprints/2026.05.10_20-21_vision-review-loop/pre_start.md sprints/2026.05.10_20-21_vision-review-loop/prd.md sprints/2026.05.10_20-21_vision-review-loop/tech-plan.md
```

实现阶段验收命令（由 `full-stack-software-engineer` 在 `tech-done.md` 提供输出）：

- 与 review queue/review decision 相关的 targeted tests。
- 必要静态检查或最小可行运行验证。
- `git diff --check`（限定本 sprint 改动范围）。

## 优先级和验收口径

- P0：operator 可提交 review decision 并成功落盘。
- P0：queue 明确显示已判定/待判定状态。
- P0：关键护栏测试通过。
- P0：无真实硬件/HIL承诺或误导性结论。
- P1：错误提示可操作。

## 风险边界与回退策略

- 风险：decision schema 变动导致读写不兼容。
  - 边界：本轮固定最小字段集，不做历史兼容重构。
- 风险：并发提交冲突。
  - 边界：先明确单样本最后写入策略或拒绝重复策略。
- 风险：文件系统写失败导致闭环中断。
  - 边界：接口必须返回结构化失败，queue 主流程不崩溃。
- 风险：功能蔓延到模型/硬件。
  - 边界：超出本切片需求一律 defer 到后续 sprint。

## 完成前自检

- 是否只在本 sprint 目标上前进，未扩 scope。
- 是否严格遵守“测试仅护栏”。
- 是否未触发任何硬件/HIL承诺。
- 是否把验证输出、失败定位、剩余风险回填到 `tech-done.md`。
