# Sprint 2026.05.10 21-22 Review Progress Metrics - PRD

## 状态

- 阶段：prd completed。
- 时间：2026-05-10 21:10 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现 owner：`full-stack-software-engineer`。

## 背景

上一轮已经打通 vision review decision 提交与落盘，但 operator 仍缺管理视角：无法快速判断“今天还要复核多少样本、处理覆盖率是否足够、哪类 decision 在堆积”。这导致 Objective 4 虽有动作但完成度提升慢。

## 用户价值和产品北极星

- 用户价值：让 operator 在同一界面完成“看进度 + 看分布 + 进待处理”，减少人工抄表和二次检索。
- 北极星一致性：感知模块产品化不仅要能判定，还要能持续运营和复盘，支持稳定送垃圾闭环的质量管理。

## OKR 映射

- Objective 4（主）
  - KR3：补齐复核进度统计与覆盖率，让样本处理状态可运营。
  - KR4：维持稳定感知 contract，统计结果可被行为/产品链路共用。
- Objective 5（次）
  - operator 触点前移到“可行动的进度面板”。

## KR 拆解或更新

- KR-A：定义并产出 `review_progress_summary`：`total`、`decided`、`pending`、`coverage_rate`。
- KR-B：定义并产出 `decision_distribution`：`approved/rejected/needs_retry` 的 count + ratio。
- KR-C：在 operator 端提供下一步待处理入口（pending first sample 或 pending route）。
- KR-D：最小护栏测试覆盖统计 contract、口径边界和空数据降级。

## 本轮核心抓手

- 抓手 1：先固化统计口径（总量、已判定、待判定、覆盖率）。
- 抓手 2：把决策分布和待处理入口做成 operator 可直接消费的数据/交互。
- 抓手 3：测试以护栏为主，保证快节奏推进 Objective 4。

## 做什么 / 不做什么

做：

- 增加 review progress 聚合逻辑和 API 输出。
- 增加 operator 端统计卡片与分布展示。
- 增加待处理样本快速入口。
- 增加 targeted tests（统计 contract 与关键失败路径）。

不做：

- 不做算法升级、样本标注平台、权限系统。
- 不做硬件/HIL 和真实相机上车验证。
- 不做 unrelated UI/接口重构。

## 产品需求

- operator 页面必须显示：
  - 已判定数量。
  - 待判定数量。
  - 总样本数量。
  - 覆盖率（百分比，固定小数位策略需一致）。
- 页面必须显示三类 decision 分布（count + ratio）。
- 页面必须提供“下一步待处理样本”入口。
- 无 pending 时需显示明确状态（如“已全量处理”）而不是空白。
- 统计数据必须与 decision source 同口径，避免 UI 自行推断导致偏差。

## 非功能需求

- 容错：脏 decision 或缺字段数据不能导致接口崩溃。
- 可复盘：统计结果可追溯到当前 queue 与 decision source。
- 低侵入：改动限定在 vision review/operator 相关路径。
- 速度优先：测试仅护栏，不阻塞功能推进。

## 优先级和验收口径

- P0：统计卡片（已判定/待判定/总量/覆盖率）可用。
- P0：决策分布（count + ratio）可用。
- P0：待处理入口可用。
- P0：实现后通过 tech-plan 指定的 targeted tests + py_compile + smoke + diff check。
- P1：异常/空数据文案清晰。

## 对应责任 Engineer

- 实现与验证 owner：`full-stack-software-engineer`。
- Product 仅负责口径、边界与收口证据，不直接写实现。

## 风险、阻塞和证据链

- 风险：历史 decision 去重策略不清，导致覆盖率失真。
- 风险：distribution 和 summary 使用不同数据源，出现口径冲突。
- 阻塞：如果 queue 样本唯一标识不稳定，pending 入口可能跳转错误。
- 证据链缺口：本轮不含 HIL，不代表真实相机链路处理率。

## 需要创建或更新的 sprint 文档

- 本轮计划文档：`pre_start.md`、`prd.md`、`tech-plan.md`（已 completed）。
- 实现收口文档：`tech-done.md`、`side2side_check.md`、`final.md`（待实现阶段更新）。
