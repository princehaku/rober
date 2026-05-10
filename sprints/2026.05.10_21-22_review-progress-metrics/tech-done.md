# Sprint 2026.05.10 21-22 Review Progress Metrics - Tech Done

## 状态

- 阶段：tech-done completed
- 时间：2026-05-10 21:44 CST
- 实现 owner：`full-stack-software-engineer`

## 本轮实际改动

### 1) 后端复核进度聚合与分布

改动文件：
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`

实现点：
- 在 `summarize_vision_manifest()` 输出新增：
  - `progress_summary.total/decided/pending/coverage_rate`
  - `decision_distribution.approved|rejected|needs_retry.{count,ratio}`
  - `next_pending_sample`（无 pending 时为 `null`）
- 新增 `summarize_review_progress()`，口径：
  - `total`：当前 manifest 中可复核样本总数（按 `sample_review_reason` 判定）
  - `decided`：可复核样本中已有有效“最后决策”的样本数
  - `pending=max(total-decided,0)`
  - `coverage_rate=decided/total`，`total=0` 时返回 `0.0`
  - 决策分布 `ratio=count/decided`，`decided=0` 时返回 `0.0`
- `load_review_decision_log()` 的 last-write-wins 行为沿用并被显式验证：同一样本重复决策按最后有效记录生效。
- `OperatorGateway.vision_review_queue()` 透传上述统计字段到 `/api/vision/review-queue`。

### 2) Operator 页面统计展示与待处理入口

改动文件：
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`

实现点：
- Vision Review Queue 区域新增展示：
  - `Progress`
  - `Decision distribution`
  - `Next pending sample`
- 新增按钮 `Jump To Next Pending`：
  - 有 pending 时快速定位到下一个待处理样本
  - 无 pending 或样本不在当前窗口时给明确提示
- diagnostics 页面复核摘要改为使用同一统计口径：
  - `diagReviewQueue` 显示 `pending / total`
  - `diagNextReviewSample` 优先显示 `next_pending_sample`

### 3) 最小护栏测试与 contract 文档

改动文件：
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `docs/interfaces/ros_contracts.md`

测试补充覆盖：
- 统计 contract 基本字段存在与值校验
- 空数据（total=0）
- 部分已判定
- 重复决策按最后有效记录生效
- HTTP endpoint 和 operator 页面静态元素/函数存在性

文档更新：
- 在 `docs/interfaces/ros_contracts.md` 增补 `progress_summary`、`decision_distribution`、`next_pending_sample` 字段与口径说明。

## 验收命令与关键输出

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_diagnostics.py'`
- 输出：`Ran 16 tests in 0.467s` -> `OK`

2. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_http.py'`
- 输出：`Ran 18 tests in 9.084s` -> `OK`

3. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_static.py'`
- 输出：`Ran 8 tests in 0.060s` -> `OK`

4. `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- 输出：无报错，exit 0

5. `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- 输出节选：多组测试通过，包含 `Ran 122 tests in 17.872s` -> `OK`，最终退出码 0

6. `git diff --check`
- 结果：失败（exit 2）
- 原因：并行改动中的 `README.md` 存在大量 trailing whitespace（本任务范围外）
- 追加范围内确认：
  - `git diff --check -- <本任务允许文件列表>` -> 通过（exit 0）

## 偏差与处理

- 偏差：全量 `git diff --check` 被范围外并行改动阻塞。
- 处理：未越界修复 `README.md`；已对本任务允许文件执行 scoped diff-check 并通过。

## 剩余风险

1. 当前统计口径依赖 manifest 的“可复核样本判定规则”（`sample_review_reason`）；若后续规则变化，`total/coverage/distribution` 会同步变化，需要产品和运营对齐。
2. `review_queue` 仍是窗口化展示（上限限制），`next_pending_sample` 可能不在当前选择框窗口内，页面会给出明确提示，但用户仍需刷新或翻页策略（后续可扩展）。
3. 本轮全部是软件侧验证，不包含真实硬件/HIL 与真实相机上车验证。

## 2026-05-10 22:15 CST 验收复跑（本次回归）

按验收优先任务要求，基于当前工作区增量只做验收复跑，不扩展改动范围。

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_diagnostics.py'`
- 结果：通过
- 关键输出：`Ran 16 tests in 0.422s`、`OK`

2. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_http.py'`
- 结果：通过
- 关键输出：`Ran 18 tests in 9.058s`、`OK`

3. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_static.py'`
- 结果：通过
- 关键输出：`Ran 8 tests in 0.063s`、`OK`

4. `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- 结果：通过
- 关键输出：无输出，exit 0

5. `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- 结果：通过
- 关键输出：`Ran 122 tests in 17.853s`、`OK`；`Ran 13 tests in 0.707s`、`OK`；进程 exit 0

6. `git diff --check`
- 结果：失败（exit 2）
- 失败定位：范围外 `README.md` 存在 trailing whitespace（并行脏改动）
- 处理：按范围约束未修复 `README.md`，补跑 scoped 校验：
  - `git diff --check -- <allowed files>` -> 通过（exit 0）

## 2026-05-10 22:15 复验补充（按本轮验收命令原样执行）

### 功能一致性复核结论

- 结论：`summary/distribution/next_pending` 三项后端字段与 operator 页面展示/跳转逻辑一致，且 diagnostics 与 review queue 使用同一统计口径。
- 代码对照：
  - `operator_gateway_diagnostics.py`：`summarize_review_progress()` 聚合并在 `summarize_vision_manifest()` 合并输出。
  - `operator_gateway.py`：`vision_review_queue()` 透传 `progress_summary`、`decision_distribution`、`next_pending_sample`。
  - `operator_gateway_http.py`：`applyReviewProgress()` 渲染统计；`jumpToNextPending()` 实现待处理样本聚焦和窗口外提示。

### 验收命令结果（本轮）

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_*review*py'`
   - 结果：失败（exit 5）
   - 关键输出：`Ran 0 tests in 0.000s` / `NO TESTS RAN`
2. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_*operator*py'`
   - 结果：通过
   - 关键输出：`Ran 42 tests in 9.558s` / `OK`
3. `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
   - 结果：通过（exit 0，无报错）
4. `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
   - 结果：通过
   - 关键输出节选：`Ran 6 tests ... OK`、`Ran 24 tests ... OK`、`Ran 39 tests ... OK`、`Ran 9 tests ... OK`、`Ran 122 tests ... OK`、`Ran 13 tests ... OK`
5. `git diff --check`
   - 结果：失败（exit 2）
   - 失败定位：仅 `README.md`（范围外并行改动）存在 trailing whitespace。
6. `git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py docs/interfaces/ros_contracts.md sprints/2026.05.10_21-22_review-progress-metrics/tech-done.md sprints/2026.05.10_21-22_review-progress-metrics/side2side_check.md sprints/2026.05.10_21-22_review-progress-metrics/final.md`
   - 结果：通过（exit 0）

### 失败定位与最小修复说明

- `test_*review*py` 失败根因：当前测试文件命名均不匹配 `*review*` 模式，导致 discover 结果为 0。
- 本轮处理：不越界新增/重命名测试文件，仅保留失败证据并由 `test_*operator*py` + smoke 作为当前可执行护栏。
- `git diff --check` 失败根因：范围外 `README.md` 尾随空白；按任务边界未修改/回滚该文件，并补充 scoped diff-check 通过证据。
