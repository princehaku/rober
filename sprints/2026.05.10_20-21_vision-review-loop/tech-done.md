# Sprint 2026.05.10 20-21 Vision Review Loop - Tech Done

## 状态

- 阶段：tech-done completed
- 时间：2026-05-10 20:53 Asia/Shanghai
- 实现 owner：`full-stack-software-engineer`
- 范围：Objective 4 低完成度切片（vision review queue 人工复核闭环）

## 本轮实际改动

1. 新增 review decision 提交能力（API）
- `POST /api/vision/review-decisions`
- 校验 `sample_id`、`decision`（`approved|rejected|needs_retry`）
- 结构化错误返回：`error.code` / `error.message` / `error.details`

2. decision 落盘（JSONL）
- 新增参数：`review_decision_log_ref`（默认 `~/.ros/trashbot_vision_samples/review_decisions.jsonl`）
- 每次提交 append 一条 JSONL 记录，包含 `decision_id`、`sample_id`、`decision`、`option`、`comment`、`operator`、`timestamp`、`stored_at`、`sample_ref`

3. diagnostics/queue 反映 review 状态
- `review_queue` item 新增：
  - `review_status` (`pending|decided`)
  - `last_decision` 摘要
- diagnostics 新增：
  - `review_decision_log_ref`
  - `review_decision_log` 健康摘要（`status/exists/decision_count/sample_count/read_error`）

4. operator 页面最小交互
- 新增 queue 区块：sample 选择、decision 选择、option/operator/comment 输入
- 新增按钮：`Refresh Queue`、`Submit Review Decision`
- 支持显示结构化错误与提交结果

5. 文档与测试更新
- `docs/interfaces/ros_contracts.md` 增补新 endpoint、参数与字段约定
- 新增/更新 diagnostics、http、static 测试覆盖新 contract

## 改动文件

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.10_20-21_vision-review-loop/tech-done.md`

## 验收命令与结果

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_diagnostics.py'`
- 结果：PASS
- 关键输出：`Ran 15 tests in 0.416s` / `OK`

2. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_http.py'`
- 结果：PASS
- 关键输出：`Ran 18 tests in 9.084s` / `OK`

3. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_static.py'`
- 首次结果：FAIL（1）
- 失败点：静态断言仍匹配旧调用文本，未适配 `summarize_vision_manifest(..., decision_index=...)`
- 修复后重跑：PASS（`Ran 8 tests in 0.064s` / `OK`）

4. `python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- 结果：PASS（无输出，退出码 0）

5. `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- 结果：PASS
- 关键输出（摘录）：
  - `Ran 6 tests ... OK`
  - `Ran 24 tests ... OK`
  - `Ran 39 tests ... OK`
  - `Ran 9 tests ... OK`
  - `Ran 121 tests ... OK`
  - `Ran 13 tests ... OK`

6. `git diff --check`
- 结果：PASS（无输出，退出码 0）

## 失败定位（本轮）

- 唯一失败发生在命令 3 首轮：`test_operator_gateway_static` 的旧字符串断言与新实现不一致。
- 已修复静态断言并重跑通过。

## 剩余风险

- 本轮仅完成软件与测试闭环；未包含真实硬件/HIL、上车验证、真实相机链路验证。
- `review_decision_log_ref` 默认写本地文件，部署环境需保证目录可写。
