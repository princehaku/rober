# Sprint 2026.05.10 21-22 Review Progress Metrics - Pre Start

## 状态

- 阶段：pre_start completed。
- 时间：2026-05-10 21:10 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现 owner：`full-stack-software-engineer`。
- Sprint：`sprints/2026.05.10_21-22_review-progress-metrics/`。

## 用户价值和产品北极星

当前 vision review decision 已能提交，但 operator 还看不到“还剩多少待处理、当前覆盖率是否达标、判定分布是否偏斜”。用户价值是把“能判定”推进到“能管理进度”：operator 一眼看到已判定/待判定、决策分布、覆盖率，并能直接进入下一批待处理样本。

本轮继续服务北极星：机器人要面向普通手机用户稳定可维护运行，感知链路必须可复盘、可运营，而不是只留零散 decision 记录。

## OKR 映射

- 主目标：Objective 4（感知模块产品化，当前完成度最低）
  - 推进 KR3：样本/manifest contract 从“可写 decision”升级为“可统计复核进度与覆盖率”。
  - 推进 KR4：保持稳定感知 contract，让行为与产品层基于统一统计口径协作。
- 次目标：Objective 5（手机触点可用性）
  - operator 页面增加进度看板与待处理入口，减少人工筛选成本。

## KR 拆解或更新

- Sprint KR-A：输出 review 总量、已判定量、待判定量、覆盖率（`decided/total`）。
- Sprint KR-B：输出决策分布（`approved/rejected/needs_retry` 的计数与占比）。
- Sprint KR-C：operator 页面可直达“下一步待处理样本”入口（例如第一条 pending sample 或 pending filter link）。
- Sprint KR-D：测试仅做护栏，覆盖统计 API contract、空队列/脏数据/部分决策等关键边界。

## 本轮核心抓手

- 把 review loop 从“可提交 decision”推进为“可管理处理进度”。
- 先打通最小闭环：统计聚合 -> API 暴露 -> UI 展示 -> 待处理入口。
- 严格执行“功能往前走，测试只做护栏”。

## 做什么 / 不做什么

做：

- 增加 review progress 聚合统计和覆盖率计算。
- 在 operator 端展示已判定/待判定、决策分布、覆盖率。
- 增加待处理入口（pending sample 快速入口或等价交互）。
- 补最小 targeted tests，确保统计口径和入口行为稳定。

不做：

- 不做模型训练、自动重标注、权限体系改造。
- 不做硬件/HIL、相机实机验证。
- 不做跨模块大重构，只做本切片必需改动。

## 优先级和验收口径

- P0：operator 可看到总量、已判定、待判定、覆盖率。
- P0：operator 可看到三类 decision 分布（数量与占比）。
- P0：operator 可直接进入下一步待处理样本。
- P0：本轮计划定义的验收命令（targeted tests + py_compile + smoke + diff check）在实现后可执行并通过。
- P1：空数据、脏数据、无 pending 场景有可读降级文案。

## 对应责任 Engineer

- 主责实现与验证：`full-stack-software-engineer`。
- Product 负责范围边界、验收口径、sprint 收口证据。

## 风险、阻塞和需要补齐的证据链

- 风险：`total` 口径和 `decision` 去重策略不一致，会导致覆盖率失真。
- 风险：历史 decision 数据缺字段时，统计可能偏差或报错。
- 风险：若待处理入口只依赖 UI 侧筛选，可能和后端 pending 定义不一致。
- 证据缺口：本轮仅软件闭环，不包含 HIL/上车证据，不能外推真实运行质量。

## 需要创建或更新的 sprint 文档

本轮已创建并完成：

- `sprints/2026.05.10_21-22_review-progress-metrics/pre_start.md`
- `sprints/2026.05.10_21-22_review-progress-metrics/prd.md`
- `sprints/2026.05.10_21-22_review-progress-metrics/tech-plan.md`

后续实现阶段必须更新：

- `sprints/2026.05.10_21-22_review-progress-metrics/tech-done.md`
- `sprints/2026.05.10_21-22_review-progress-metrics/side2side_check.md`
- `sprints/2026.05.10_21-22_review-progress-metrics/final.md`
