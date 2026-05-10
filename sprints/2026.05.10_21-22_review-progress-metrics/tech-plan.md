# Sprint 2026.05.10 21-22 Review Progress Metrics - Tech Plan

## 状态

- 阶段：tech-plan completed。
- 时间：2026-05-10 21:10 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现 owner：`full-stack-software-engineer`。
- 执行方式：单 owner 单线闭环。

## 执行声明（主节点约束）

本 `tech-plan` 完成后，主节点不直接写产品代码、测试代码或硬件配置；实现、验证、失败修复由 `full-stack-software-engineer` 子 agent 执行，并在 `tech-done.md` 回填证据。

## Goal

在现有 vision review decision 功能上补齐“复核进度统计与待处理覆盖率”：让 operator 直接看到已判定/待判定数量、决策分布、覆盖率，并给出下一步待处理样本入口。

## Scope Boundary

- 只做 review progress metrics 与 pending-entry 切片。
- 测试只做护栏，优先推进 Objective 4 完成度。
- 不做模型升级、不做硬件/HIL、不做跨模块重构。

## 文件范围（实现阶段）

实现 owner `full-stack-software-engineer` 仅可修改 vision review/operator 相关文件（以现有代码路径为准），建议范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_*.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/review_*.*`
- `src/ros2_trashbot_behavior/test/test_*review*`
- `src/ros2_trashbot_behavior/test/test_*operator*`
- `src/ros2_trashbot_behavior/static/*review*`
- `sprints/2026.05.10_21-22_review-progress-metrics/tech-done.md`
- `sprints/2026.05.10_21-22_review-progress-metrics/side2side_check.md`
- `sprints/2026.05.10_21-22_review-progress-metrics/final.md`

禁止范围：

- 所有硬件驱动、串口/底盘协议、launch 硬件参数、vendor 文档。
- 与 review metrics 无关的 behavior/nav/vision 主链路代码。

## 接口边界

在现有 review queue / decision API 的基础上，仅新增或扩展统计字段，不重写主 contract：

- `GET /api/vision/review-queue`（或当前等价 endpoint）
  - 扩展返回：
    - `progress_summary.total`
    - `progress_summary.decided`
    - `progress_summary.pending`
    - `progress_summary.coverage_rate`
    - `decision_distribution.approved.count|ratio`
    - `decision_distribution.rejected.count|ratio`
    - `decision_distribution.needs_retry.count|ratio`
    - `next_pending_sample`（sample_id 或入口 ref）
- `POST /api/vision/review-decisions` contract 保持兼容；新增统计不得破坏写入链路。

数据口径边界：

- `total` 以 queue 可复核样本总量为准。
- `decided` 以有效 decision 的去重样本数为准（同一样本多次判定按最后有效策略或既定策略，需在实现中固定）。
- `pending = max(total - decided, 0)`。
- `coverage_rate = decided / total`（`total=0` 时返回 `0.0` 并给出明确状态）。

## 实现任务拆解（给 full-stack-software-engineer）

1. 在 review 数据层新增 progress 聚合函数。
2. 在 queue API 返回 summary + distribution + next_pending_sample。
3. 在 operator 页面新增统计卡片与分布展示。
4. 在 operator 页面增加 pending 快速入口。
5. 增加 targeted tests，覆盖正常、空数据、脏数据、重复决策去重口径。

## 风险边界

- 风险 1：口径漂移
  - 边界：summary 与 distribution 必须来自同一数据源与同一批次快照。
- 风险 2：历史脏数据导致统计异常
  - 边界：对无效 decision 进行跳过并记录降级，不允许接口 500。
- 风险 3：pending 入口失效
  - 边界：无 pending 时返回明确空状态，不给失效链接。
- 风险 4：功能蔓延
  - 边界：本轮禁止扩到模型/标注平台/权限系统。

## 验收命令

实现阶段必须由 `full-stack-software-engineer` 执行并在 `tech-done.md` 提供关键输出：

1. targeted tests（review progress / operator diagnostics）

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_*review*py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_*operator*py'
```

2. py_compile

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
```

3. smoke

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
```

4. diff check（实现改动 + sprint 文档）

```bash
git diff --check
```

本计划阶段文档检查（当前执行）：

```bash
git diff --check -- sprints/2026.05.10_21-22_review-progress-metrics/pre_start.md sprints/2026.05.10_21-22_review-progress-metrics/prd.md sprints/2026.05.10_21-22_review-progress-metrics/tech-plan.md
ls -la sprints/2026.05.10_21-22_review-progress-metrics
```

## 优先级和验收口径

- P0：progress summary、decision distribution、next pending entry 三项都可用。
- P0：targeted tests + py_compile + smoke + diff check 全部通过。
- P0：不越界改动，不引入 HIL 误导结论。
- P1：空数据和异常数据降级可读。

## 完成前自检

- 是否严格服务 Objective 4 低完成度补齐。
- 是否把测试控制在“护栏”而非大规模扩写。
- 是否未修改范围外文件。
- 是否在 `tech-done.md` 留下完整验证证据与剩余风险。
