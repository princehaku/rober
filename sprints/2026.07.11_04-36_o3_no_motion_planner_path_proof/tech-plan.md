# O3 No-Motion Planner Path Proof Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective：O5，约 `~85%`。
2. 本 sprint 不直接针对 O5。
3. 不针对理由：`sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/final.md` 已明确上一轮在“真实 production external evidence 不可得且无新 field execution material”条件下 fail-closed，继续 O5 readiness、probe、wrapper、support packet、readback 或 checklist 仍会得到 `okr_credit_allowed=false`，不会形成新的 `external_artifact_delta`。因此本轮切到现场 O3 验证 lane，尝试 no-motion planner/path proof，给 O6/O7 后续消费真实材料。

## 用户价值和方向判断

### 用户价值

用户现在需要的是一份新的、可复验的现场上游材料，而不是更多 support-only 状态面板。本轮通过 no-motion planner/path proof 去回答：真实上位机是否已经具备最小 planner/path 证据生成能力；如果没有，具体卡在哪一层。

### 方向判断

- O5：**暂停**
- O3 no-motion planner/path proof lane：**继续**
- O6/O7 surface 新切片：**暂停，等待新材料**
- O1 historical/current-HIL 变体：**暂停，避免重复消费同一 blocker**

## 证据边界

本轮 proof boundary 固定为以下三类之一：

- `software_proof_real_board_no_motion_planner_path_only`
- `blocked_api_or_ssh_layered_not_proven`
- `software_proof_local_mock_no_motion_planner_path_only`

不论哪条路径，顶层都必须保持：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `hil_pass=false`
- `route_execution_success=false`

## 文件范围

主责任 `robot-algorithm-engineer` 执行时允许改动：

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/scripts/o11_nav2_goal_execution_proof.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/tech-done.md`
- `sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/algorithm_worker_report.md`

禁止改动：

- 任何产品代码范围外文件
- `OKR.md`
- `docs/process/okr_progress_log.md`
- 其他 sprint 目录
- 任何 launch 默认运动参数、硬件配置默认值或底盘控制默认入口

## 接口边界

### 允许触达的只读 / no-motion 接口

- `ssh root@192.168.1.11 -p 37878`
- `/api/nav2/proof/refresh`
- 只读 `ros2 topic list` / `ros2 topic echo --once` / `ros2 service list` / `ros2 action list`
- `learn.launch.py --show-args` 或等价参数面检查

### 明确禁止的接口与动作

- 禁止发送 `/cmd_vel`
- 禁止调用 `/api/base/manual`
- 禁止执行 Nav2 `NavigateToPose`
- 禁止启动真实底盘运动
- 禁止把 `robot_control_executed`、`safe_to_control`、`delivery_success`、`hil_pass` 写成 true

### 为什么允许 `/api/nav2/proof/refresh`

`/api/nav2/proof/refresh` 在本轮只作为 no-motion planner/path proof 的刷新或 readback 入口使用，目标是拉取或刷新 proof artifact，而不是发起 route execution。若该入口实际要求启动 motion controller、managed runtime 或 goal execution，则本轮必须 fail-closed 并退回 SSH/local mock fallback。

## 技术方案

### 路径 A：真实上位机 SSH / HTTP no-motion proof

`robot-algorithm-engineer` 先走真实上位机只读预检：

1. `ssh root@192.168.1.11 -p 37878` 连通性
2. ROS2 setup / package / topic / map / planner proof API 可见性
3. `/api/nav2/proof/refresh` 是否能在 no-motion 条件下返回 planner/path 摘要
4. 若 proof API 不可用，则仅通过 SSH 收集分层 blocker，不升级为 motion 执行

允许的正向结果：

- 生成 no-motion planner/path summary
- 确认 path generation requested / generated / blocked reason
- 产出可供后续 O6/O7 消费的安全摘要材料

### 路径 B：API/SSH 分层失败

若真实上位机不可达、setup 缺失、topic 缺失、map/save/proof 接口不可用，必须返回 fail-closed 结果，明确是：

- `blocked_ssh_unreachable`
- `blocked_ros2_cli_missing`
- `blocked_setup_missing`
- `blocked_required_topics_missing`
- `blocked_map_or_planner_proof_missing`

这一分层结果本身就是本轮可接受产物，但不能冒充 planner ready。

### 路径 C：本地 mock fallback

若真实 SSH/HTTP 都不可用，允许复用 `field_route_evidence_preflight.py` 的 dry-run/local 模板，产出 mock fallback proof，用于验证命令模板、JSON contract、fail-closed 分层与安全边界仍成立。

## KR 拆解和本轮核心抓手

### KR 拆解

1. 生成或确认一条 no-motion planner/path proof 入口；
2. 把真实上位机路径与 fallback 路径的失败分层固定下来；
3. 产出能让 O6/O7 后续消费的真实或 mock 安全摘要；
4. 明确下一轮需要的真实材料：`task_id`、`map.yaml`、`route.csv`、keyframe、planner/path summary、replay JSONL。

### 本轮核心抓手

不是再做 surface，而是推动一个最小现场证据闭环：

- 优先真实上位机 no-motion planner/path proof
- 次选 API/SSH fail-closed 分层
- 最后才是 local mock fallback

## 任务分工

### 主责任务：robot-algorithm-engineer

目标：在不触发任何真实运动的前提下，尝试产出 no-motion planner/path proof 或 fail-closed fallback。

文件范围：

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/scripts/o11_nav2_goal_execution_proof.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/tech-done.md`

实现要求：

- 若触达真实上位机，只允许只读预检或 proof refresh/readback。
- 将 `/api/nav2/proof/refresh` 明确约束为 no-motion proof 入口；若发现它会触发 NavigateToPose 或运动控制，必须直接 fail-closed。
- 输出要明确 `safe_to_control=false`、`delivery_success=false`。
- 所有新增技术注释必须使用中文。

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py onboard/scripts/o11_nav2_goal_execution_proof.py
python3 -m unittest onboard.tests.test_field_route_evidence_preflight onboard.tests.test_o11_nav2_goal_execution_proof
git diff --check -- onboard/scripts/field_route_evidence_preflight.py onboard/scripts/o11_nav2_goal_execution_proof.py onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_o11_nav2_goal_execution_proof.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof
```

### 条件咨询：robot-software-engineer

仅当以下事实需要澄清时介入：

- `/api/nav2/proof/refresh` 的真实行为边界
- 上位机 HTTP/SSH proof 入口是否已有只读安全模式
- 现有脚本是否会隐式触发 `NavigateToPose`、managed runtime 或控制面

文件范围：

- 只读咨询，默认不改文件

验收命令：

```bash
rg -n "/api/nav2/proof/refresh|NavigateToPose|cmd_vel|base/manual" onboard/scripts docs/navigation
```

## 优先级和验收口径

优先级从高到低：

1. 真实上位机 no-motion planner/path proof
2. API/SSH 分层 blocker 证据
3. local mock fallback

验收通过的最低标准：

- 有一条可复验的 no-motion proof 或 fail-closed blocker 证据；
- 计划与实现证据中明确包含 `safe_to_control=false`、`delivery_success=false`；
- 没有 `/cmd_vel`、`/api/base/manual`、`NavigateToPose` 或真实底盘运动；
- 结果能清楚告诉后续 O6/O7 该消费什么新材料，或明确说明仍缺哪一层真实输入。

## 验收命令

本轮计划文档验收：

```bash
test -f sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/pre_start.md && test -f sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/prd.md && test -f sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/tech-plan.md
```

```bash
rg -n "OKR 最低优先级核对|O5|no-motion|path generation|/api/nav2/proof/refresh|ssh root@192.168.1.11|验收命令|文件范围|接口边界|safe_to_control=false|delivery_success=false" sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof
```

```bash
git diff --check -- sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof
```

## 风险、阻塞和需要补齐的证据链

- 风险 1：真实上位机当前 proof API 与 runtime 行为可能没有把 readback 和 execution 完全隔离，需先验证边界。
- 风险 2：即便 no-motion path proof 成功，也可能仍缺 `map.yaml`、`route.csv`、keyframe 或 replay JSONL，导致 O6/O7 后续只能部分消费。
- 风险 3：若 SSH 和 HTTP 都不可达，本轮只能形成 mock/fallback 证据，OKR 不应上调。

需要补齐的后续真实证据链：

- `task_id`
- `map.yaml`
- `route.csv`
- keyframes
- planner/path summary
- replay JSONL 或等价 no-motion artifact

## 需要创建或更新的 sprint 文档

- `pre_start.md`
- `prd.md`
- `tech-plan.md`
- 后续执行完成后由对应 owner 更新 `tech-done.md`
- 若形成可验收结果，再补 `side2side_check.md` 与 `final.md`
