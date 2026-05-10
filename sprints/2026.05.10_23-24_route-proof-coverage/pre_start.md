# Sprint 2026.05.10 23-24 Route Proof Coverage - Pre Start

## 状态

- 阶段：pre_start completed。
- 时间：2026-05-10 23:24 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- Sprint：`sprints/2026.05.10_23-24_route-proof-coverage/`。
- 实现 owner：`autonomy-engineer`、`full-stack-software-engineer`（并行）。

## 用户价值和产品北极星

用户要的不是“看起来会导航”，而是“能被证明这条固定路线在软件层面可重复、可诊断、可收口”。

本轮围绕北极星推进：普通手机用户把垃圾交给小车后，系统能沿固定路线出发并可解释当前是否可发车、为什么不可发车、下一步要处理什么。

## OKR 映射

- 主目标：Objective 3（可验证导航与固定路线，当前完成度最低）。
  - KR2：固化 `route_data_recorder` / `route_csv_to_yaml` / fixed-route 输入输出与测试护栏。
  - KR3：增强 fixed-route dry-run 的 route coverage 证明与状态输出。
  - KR4：明确 fixed-route 与 behavior/operator 的接口边界与参数语义。
- 次目标：Objective 5（手机触点可理解性）。
  - 通过 diagnostics/operator 展示 route proof 状态，支持用户侧异常解释。

## KR 拆解或更新（本轮）

- KR-3A：fixed-route proof 增加“路线覆盖率/缺口点位/最近失败原因”结构化输出。
- KR-3B：behavior/operator 消费统一 proof contract，并在 diagnostics 页面展示可执行提示。
- KR-3C：在无 HIL 条件下完成 unittest + py_compile + smoke + scoped diff-check 护栏验证。

## 本轮核心抓手

- 抓手 1：先补 Objective 3 的 proof 证据密度，而不是扩功能面。
- 抓手 2：导航 owner 与触点 owner 并行推进，文件范围完全隔离。
- 抓手 3：测试只做护栏，保障快节奏前进，不引入硬件依赖。

## 做什么 / 不做什么

做：

- 在 `src/ros2_trashbot_nav/` 与 `docs/navigation/` 增强 route-proof coverage 能力和文档。
- 在 `src/ros2_trashbot_behavior/` 与 `docs/interfaces/` 对齐 operator/diagnostics contract 与展示。
- 产出可直接进入 implementation 的双 owner 并行执行计划。

不做：

- 不做硬件实机/HIL 验证（WAVE ROVER、相机、串口上车）。
- 不做跨包大重构。
- 不做模型训练或视觉算法升级。

## 优先级和验收口径

- P0：两位 owner 的文件范围互不重叠，可同轮并行开工。
- P0：fixed-route proof contract 在 nav 与 behavior 口径一致。
- P0：每位 owner 必须提供 unittest + py_compile + smoke + scoped diff-check 证据。
- P1：文档明确失败降级语义与 remaining risk，不夸大为实机成功。

## 对应责任 Engineer

- `autonomy-engineer`：Objective 3 功能切片主责，仅限 `src/ros2_trashbot_nav/`、`docs/navigation/`。
- `full-stack-software-engineer`：operator/diagnostics 契约对齐主责，仅限 `src/ros2_trashbot_behavior/`、`docs/interfaces/`。
- Product 仅负责价值边界、并行拆解和验收口径。

## 风险、阻塞和需要补齐的证据链

- 风险：两侧对 proof 字段命名或状态语义理解不一致，导致对接漂移。
- 风险：targeted unittest pattern 选取不当会出现 `NO TESTS RAN` 假阳性。
- 风险：smoke 通过只代表软件护栏，不代表 Nav2/HIL 实跑成功。
- 证据缺口：真实路线采集、真实相机输入、真实 Nav2 waypoint/fixed-route 仍缺上车证据。

## 需要创建或更新的 sprint 文档

本轮已创建并完成：

- `sprints/2026.05.10_23-24_route-proof-coverage/pre_start.md`
- `sprints/2026.05.10_23-24_route-proof-coverage/prd.md`
- `sprints/2026.05.10_23-24_route-proof-coverage/tech-plan.md`

实现阶段必须更新：

- `sprints/2026.05.10_23-24_route-proof-coverage/tech-done.md`
- `sprints/2026.05.10_23-24_route-proof-coverage/side2side_check.md`
- `sprints/2026.05.10_23-24_route-proof-coverage/final.md`
