# Sprint 2026.05.10 21-22 Review Progress Metrics - Tech Done

## 状态

- 阶段：tech-done completed
- 时间：2026-05-10 22:45 Asia/Shanghai
- 实现 owner：`full-stack-software-engineer`
- 证据基线 commit：`5cd60d8`

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
- `summarize_review_progress()` 口径固定：
  - `total`：当前 manifest 中可复核样本总数
  - `decided`：已有有效最后决策的样本数（同样本按最后有效记录）
  - `pending=max(total-decided,0)`
  - `coverage_rate=decided/total`（`total=0` 时 `0.0`）
- `OperatorGateway.vision_review_queue()` 透传上述统计字段到 `/api/vision/review-queue`。

### 2) Operator 页面统计展示与待处理入口

改动文件：
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`

实现点：
- Vision Review Queue 区域新增：
  - `Progress`
  - `Decision distribution`
  - `Next pending sample`
- 新增 `Jump To Next Pending`：
  - 有 pending 时定位到下一个待处理样本
  - 无 pending 或样本不在当前窗口时给明确提示
- diagnostics 页复核摘要复用同一统计口径。

### 3) 最小护栏测试与 contract 文档

改动文件：
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `docs/interfaces/ros_contracts.md`

覆盖内容：
- 统计 contract 字段与口径
- 空数据（`total=0`）
- 部分已判定
- 重复决策最后有效记录
- HTTP endpoint 与页面静态元素/函数存在性

## 验收命令与关键输出（按 tech-plan 原样）

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_*review*py'`
- 结果：失败（exit 5）
- 关键输出：`Ran 0 tests in 0.000s` / `NO TESTS RAN`
- 定位：当前测试文件命名不匹配 `*review*` pattern（非业务逻辑失败）

2. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_*operator*py'`
- 结果：通过
- 关键输出：`Ran 42 tests in 9.618s` / `OK`

3. `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- 结果：通过（exit 0，无报错）

4. `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- 结果：通过
- 关键输出节选：`Ran 122 tests ... OK`、`Ran 13 tests ... OK`（最终 exit 0）

5. `git diff --check`
- 结果：失败（exit 2）
- 关键输出：`README.md: ... trailing whitespace`
- 定位：范围外并行改动触发

6. `git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py docs/interfaces/ros_contracts.md sprints/2026.05.10_21-22_review-progress-metrics/tech-done.md sprints/2026.05.10_21-22_review-progress-metrics/side2side_check.md sprints/2026.05.10_21-22_review-progress-metrics/final.md`
- 结果：通过（exit 0）

## 偏差与处理

- 偏差 1：`test_*review*py` pattern 无匹配测试文件，导致 discover 返回 `NO TESTS RAN`。
  - 处理：保留失败证据；本轮不越界新增/重命名测试文件。
- 偏差 2：全量 `git diff --check` 受范围外 `README.md` 尾随空白影响。
  - 处理：不越界修改 `README.md`，补 scoped diff-check 并通过。

## 剩余风险

1. 未来若仍要求 `test_*review*py` 为硬门禁，需要补充符合命名 pattern 的测试文件或调整验收命令。
2. `review_queue` 仍为窗口化展示，`next_pending_sample` 可能不在当前窗口内，页面会提示但无法直接选中。
3. 本轮为软件侧 contract/页面闭环，不包含真实硬件/HIL 上车验证。
4. 本文档收口基于已存在 commit `5cd60d8` 与当前 sprint 文档，不新增上车结论。
