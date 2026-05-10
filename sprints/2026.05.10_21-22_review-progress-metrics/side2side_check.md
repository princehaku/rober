# Sprint 2026.05.10 21-22 Review Progress Metrics - Side2Side Check

## 检查状态

- 时间：2026-05-10 22:45 Asia/Shanghai
- 结论：功能切片已完成，接口与页面链路一致；验收命令存在 2 个已定位偏差（pattern 无匹配、范围外 README 格式问题）。本轮收口基于 commit `5cd60d8`，未新增 HIL/上车证据。

## 需求对照

1. 后端输出 `progress_summary.total/decided/pending/coverage_rate`
- 状态：已完成
- 证据：`summarize_vision_manifest()` 聚合并由 `/api/vision/review-queue` 透传。

2. 后端输出 `decision_distribution.approved|rejected|needs_retry.{count,ratio}`
- 状态：已完成
- 证据：同源聚合输出；`test_*operator*py` 回归通过。

3. 后端输出 `next_pending_sample`（无 pending 返回空）
- 状态：已完成
- 证据：接口返回 `next_pending_sample`，空状态为 `null`。

4. operator 页面展示统计并支持 `Jump To Next Pending`
- 状态：已完成
- 证据：页面存在统计展示与跳转逻辑，窗口外样本有明确提示。

5. 更新最小护栏测试与接口文档
- 状态：已完成
- 证据：`test_operator_gateway_*` 与 `docs/interfaces/ros_contracts.md` 已补齐相关断言和字段说明。

## 验收命令对照（本轮最终）

- `test_*review*py`：失败（`NO TESTS RAN`，pattern 无匹配文件）
- `test_*operator*py`：通过（`Ran 42 tests ... OK`）
- `py_compile`：通过
- `scripts/run_smoke_tests.sh`：通过
- `git diff --check`：失败（范围外 `README.md` trailing whitespace）
- scoped `git diff --check -- <allowed files>`：通过

## 用户验收建议

- 重点核验 `next_pending_sample` 对运营复核效率是否有实际提升。
- 下一轮如需严格全绿，需先对齐 `test_*review*py` 命名策略与 `README.md` 范围外格式清理 owner。
