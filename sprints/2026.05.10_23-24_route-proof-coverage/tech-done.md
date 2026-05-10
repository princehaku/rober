# Sprint 2026.05.10 23-24 Route Proof Coverage - Tech Done

## 状态

- 阶段：tech-done completed
- 时间：2026-05-11 00:18 Asia/Shanghai
- 实现 owner：`autonomy-engineer`、`full-stack-software-engineer`
- 收口方式：基于两位工程子 agent 已完成实现与验证证据做文档收口（本轮 Product 不执行长命令）

## 本轮实际改动（按 owner）

### 1) Objective 3 主切片：route proof coverage（`autonomy-engineer`）

改动文件：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_proof_summary.py`（新增）
- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py`
- `src/ros2_trashbot_nav/test/test_route_proof_summary.py`（新增）
- `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
- `src/ros2_trashbot_nav/test/test_visual_gate_proof.py`
- `docs/navigation/fixed_route_workflow.md`

结果摘要：

- fixed-route status 增强了 `route_proof_summary` 结构化字段（coverage、missing checkpoints、gate status、last block reason）。
- 文档补齐了 route proof 字段口径与稳定性规则。
- nav 侧提供 coverage source-of-truth，供 behavior/operator 消费，不引入第二口径。

### 2) Objective 3/5 接口触点切片：operator diagnostics route-proof mapping（`full-stack-software-engineer`）

改动文件：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `docs/interfaces/ros_contracts.md`

结果摘要：

- diagnostics 增加 route proof summary 抽取与分类（`ready` / `waiting_visual_gate` / `insufficient_coverage` / `blocked` / `unknown`）。
- operator 页能消费同一 route proof contract 并给出可读阻塞原因。
- 接口文档明确“behavior 只映射不重算 coverage”。

## 验证证据（子 agent 回传）

1. nav tests：通过
   - 关键输出：`Ran 42 tests ... OK`
2. behavior operator tests：通过
   - 关键输出：`Ran 47 tests ... OK`
3. smoke：通过
   - 关键输出：`Ran 127 tests ... OK`
   - 关键输出：`Ran 13 tests ... OK`

说明：以上为两位工程子 agent 实现阶段回传证据；本轮 Product 收口不重复执行 `run_smoke_tests.sh`。

## 偏差与处理

- 无新增功能偏差需要回滚。
- 本轮按约束只做文档收口，不扩展文件范围，不改动范围外代码。

## 剩余风险

1. 本轮仍是软件/离线验证证据，不代表真实 Nav2、真实相机输入或真实 WAVE ROVER 行驶成功。
2. 无 HIL/实机证据（串口、底盘反馈、实车路线采集、实车视觉门控）仍是 Objective 3/1 的关键缺口。
3. route proof 可解释性已提升，但现场可达性仍需后续上车验证闭环。

## 2026-05-11 Full-Stack 收口补充（behavior/operator）

- 执行 owner：`full-stack-software-engineer`
- 目标：复核 operator 侧 `route_proof_summary -> route_proof_status` 映射是否覆盖 nav 当前 gate_status 语义，并补齐接口文档一致性。

本次实际改动（限定范围内）：

- `docs/interfaces/ros_contracts.md`
  - 增补 `route_proof_status.state` 的明确映射规则表，声明等待态 gate_status 白名单和判定优先级（先 `waiting_visual_gate`，再 `blocked`），与 behavior 当前实现一致。

复核结论：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py` 已包含 `ready` / `waiting_visual_gate` / `insufficient_coverage` / `blocked` / `unknown` 五态映射。
- 已包含 nav 当前常见等待态 gate_status（如 `waiting_camera_frame`、`missing_keyframe`、`keyframe_preflight_failed` 等）并优先归类为 `waiting_visual_gate`，避免被 `last_block_reason` 误判为 `blocked`。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 已有对应回归用例（`test_route_proof_summary_waiting_gate_status_wins_over_block_reason`）。

验收命令与关键输出：

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_*operator*py'`
   - `Ran 48 tests in 9.619s`
   - `OK`
2. `PYTHONDONTWRITEBYTECODE=1 bash -lc "changed_py=$(git diff --name-only -- src/ros2_trashbot_behavior docs/interfaces | grep -E '\\.py$' || true); if [ -n \"$changed_py\" ]; then python3 -m py_compile $changed_py; else echo 'no python files changed for py_compile'; fi"`
   - `no python files changed for py_compile`
3. `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
   - `Ran 128 tests in 17.776s` / `OK`
   - `Ran 13 tests in 0.635s` / `OK`
4. `git diff --check -- src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.10_23-24_route-proof-coverage/tech-done.md sprints/2026.05.10_23-24_route-proof-coverage/side2side_check.md sprints/2026.05.10_23-24_route-proof-coverage/final.md`
   - 无输出（通过）

剩余风险：

- 本次为 behavior/operator 语义与文档收口，不新增 HIL 或实机验证证据。
- nav 侧后续如果新增 gate_status 枚举，需同步更新 behavior 等待态映射白名单和接口文档。

### 3) Objective 3 nav contract 复验补录（`autonomy-engineer`，2026-05-11 00:25 Asia/Shanghai）

本次基于当前工作区已有改动做了最小语义补强与复验，目标是稳定 `route_proof_summary` 在 dry-run / visual gate 下的解释口径。

追加改动（仅 nav 允许范围）：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_proof_summary.py`
- `src/ros2_trashbot_nav/test/test_route_proof_summary.py`
- `docs/navigation/fixed_route_workflow.md`

补强点：

- 新增 unittest：`test_partial_coverage_can_keep_passed_gate_when_not_blocked`，明确“部分 coverage 但当前无 gate 阻塞时，`gate_status` 可为 `passed`，可发车判断必须结合 `coverage_rate + missing_checkpoints`”。
- `build_route_proof_summary()` 对 `missing_checkpoints` 做 contract 归一：过滤已覆盖索引，仅保留未覆盖尾段索引，避免 `covered_checkpoints` 与 `missing_checkpoints` 自相矛盾。
- 新增 unittest：`test_build_route_proof_summary_ignores_missing_indexes_below_coverage`，锁定上述归一化规则。
- 导航文档补充 `missing_checkpoints` 归一化说明与稳定性规则，避免只看 `gate_status` 误判 readiness。

本轮验收命令结果（nav owner 命令集）：

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_*py'`
   - 关键输出：`Ran 44 tests in 2.514s`，`OK`
2. `PYTHONDONTWRITEBYTECODE=1 bash -lc "changed_py=$(git diff --name-only -- src/ros2_trashbot_nav docs/navigation | grep -E '\\.py$' || true); if [ -n \"$changed_py\" ]; then python3 -m py_compile $changed_py; else echo 'no python files changed for py_compile'; fi"`
   - 关键输出：空（`py_compile` 对改动 Python 文件检查通过）
3. `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
   - 关键输出：`Ran 128 tests in 17.752s`，`OK`
   - 关键输出：`Ran 13 tests in 0.613s`，`OK`
4. `git diff --check -- src/ros2_trashbot_nav docs/navigation sprints/2026.05.10_23-24_route-proof-coverage/tech-done.md sprints/2026.05.10_23-24_route-proof-coverage/side2side_check.md sprints/2026.05.10_23-24_route-proof-coverage/final.md`
   - 关键输出：空（无 whitespace 错误）

风险结论（本段复验维度）：

- contract 语义和离线/单测证据已补齐，但仍不代表 Nav2 实机与真实相机流的 HIL 成功。
- readiness 仍需由上层同时参考 `coverage_rate`、`missing_checkpoints` 与 `gate_status`，不能单看任一字段。
