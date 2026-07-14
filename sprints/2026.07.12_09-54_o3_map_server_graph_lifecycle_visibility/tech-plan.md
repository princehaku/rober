# Tech Plan - O3 Map Server Graph/Lifecycle Visibility

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_graph_lifecycle_visibility_only`
- Plan status: ready for Robot Software single-owner implementation

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective：O5，约 `85%`。
2. 本 sprint 是否针对该最低 Objective：否，本 sprint 针对 O3/O1 strict no-motion `/map_server` graph/lifecycle visibility。
3. 不针对 O5 的理由：O5 当前缺真实 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 和 external production evidence。最近多轮已确认继续 O5 readiness/readback/support-only 是 `okr_credit_allowed=false` 的 support-only，不应再消费同一 external production blocker，也不应涨分。
4. 本 sprint 针对 O3/O1 的理由：O1 仍缺 current same-run path generation success 与 Nav2 route execution success；最新可推进且不运动的前置链路是 O3/O1 strict no-motion live board runtime diagnosis。`08-55` 已把 `/amcl` retry 推进到 `active [3]`，但 `/map_server` retry 仍是 `Node not found`，因此本轮优先恢复 `/map_server` graph/lifecycle visibility。

## 上一轮起点

`08-55` 最新 live artifact 已证明：

- `board_source_preflight_ready`
- `lightweight_cli_ready=true`
- `cli_ready=true`
- `runtime_ready=true`
- `/amcl` first attempt `lifecycle_command_timeout`
- `/amcl` retry stdout contains `active [3]`
- `/map_server` first attempt `lifecycle_command_timeout`
- `/map_server` retry `returncode=1`
- `/map_server` retry `stderr="Node not found\n"`
- downstream gating 正确保持，未抢跑 `/scan`、`/map`、`/odom`、TF
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

`07-53` 下游恢复曾证明：

- map/AMCL blocker 已从 generic inactive 收窄为 lifecycle command timeout。
- `/scan` publisher visible，但 sample timeout。
- `/map_topic_missing`、`/tf_topic_missing` 仍存在。

本轮不能回到 O5 support-only、source/path mismatch、`ros2 --help` single gate、generic lifecycle timeout，或把 `/scan`/TF downstream 当 primary。主要目标是恢复 `/map_server` graph/lifecycle visibility，并区分 node absence、lifecycle manager/process startup、daemon/DDS graph visibility、helper budget/timing。

## 任务分工

主责 owner：`robot-software-engineer`，单 owner 闭环。

Robot Software 需要完成：

1. 扩展 strict no-motion helper，让 `/map_server` graph/lifecycle visibility 形成结构化 artifact。
2. 保留 `/amcl active [3]` 的事实或明确记录新 live state。
3. 补充 targeted unittest，覆盖 `/map_server` node absence、daemon/DDS graph visibility、lifecycle manager/process startup、helper budget/timing 和 dangerous booleans false。
4. 同步更新 navigation docs。
5. 运行验收命令，写 `tech-done.md`，并把 local / true-board artifact 放入本 sprint artifacts 目录。

Product owner 只做验收和收口，不直接修改产品代码、不运行实现命令。

## 允许文件范围

Robot Software 允许修改或创建：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/tech-done.md`
- `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/artifacts/`

Robot Software 不得修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 历史 sprint 目录
- WAVE ROVER、UART、硬件配置或 launch 参数
- Full-stack/O7 UI surface

如果实施中必须触碰硬件事实，先停止并向 Product 说明，需要另派 `rober-hardware-engineer` 读取 `docs/vendor/VENDOR_INDEX.md`。

## 接口影响

- 输入边界：复用 existing local / true-board helper execution；不得要求新的硬件参数、串口参数或 WAVE ROVER 接线假设。
- 输出边界：新增或扩展 helper artifact 字段，用于表达 `/map_server` graph inventory、daemon/DDS visibility、lifecycle command first/retry、stdout/stderr、elapsed、returncode、timeout budget 和 classification。
- ROS2 边界：只读执行 node graph、daemon status、lifecycle readback、topic/TF probe；不得调用 NavigateToPose，不得发布 `/cmd_vel`。
- API 边界：不得调用 `/api/base/manual`。
- 硬件边界：必须使用 `--no-base-uart`，不得打开 WAVE ROVER UART。
- Mission 边界：本轮不做 path generation、route execution、delivery success、operator acceptance、HIL pass 或 production cloud proof。

## 技术方案

### 1. 保持 readiness 不回退

保留 `08-55` 的 source/lightweight readiness 成果。`ros2 --help` 继续是 diagnostic，不得重新成为 single hard gate。测试必须覆盖 `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 后进入 `/map_server` visibility probe。

### 2. `/map_server` graph/lifecycle visibility 分层

在 helper artifact 中为 `/map_server` 记录：

- node graph inventory：是否出现 `/map_server`。
- daemon/DDS graph visibility：daemon 是否可读、node list 是否 timeout、是否存在 graph stale 或 graph hidden。
- lifecycle command：必须能看到 `ros2 lifecycle get /map_server`。
- timeout budget、elapsed、stdout、stderr、returncode。
- first attempt 与 retry attempt。
- managed runtime / lifecycle manager / process startup context。
- canonical classification。

分类至少覆盖：

- `map_server_node_absent`
- `lifecycle_manager_or_process_startup_missing`
- `daemon_or_dds_graph_visibility_failed`
- `helper_budget_or_timing_exhausted`
- `map_server_lifecycle_active`

### 3. `/amcl active [3]` 事实保护

`08-55` 已证明 `/amcl` retry stdout contains `active [3]`。新 artifact 必须：

- 复验并保留 `/amcl` command summary；或
- 如果新 run 中 `/amcl` 回退，明确写成 new live state regression，并保留 08-55 是上一轮已接受事实。

不能把 `/amcl` 写成 generic inactive 或 generic timeout。

### 4. Downstream guarded context

本轮可以保留下游 context，但不把它当 primary：

- `/scan` publisher-visible sample timeout。
- `/map_topic_missing`。
- `/tf_topic_missing`。

只有 `/map_server` graph/lifecycle visibility clean 后，才继续展开下游状态；本轮仍不得执行 path generation 或 motion。

### 5. No-motion safety invariants

本 sprint 必须固定：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- `path_generation_attempted=false`
- `path_generated=false`

### 6. 文档和留档

更新 navigation docs 说明 `09-54` 读法、proof boundary、`/map_server` visibility blocker、与 `08-55`/`07-53` 的区别、command-summary 字段和 safety invariants。实施完成后写 `tech-done.md`，必须包含实际改动、验证结果、失败定位和剩余风险。

## 验收命令

Robot Software 必须运行并记录以下命令。

### 1. 语法检查

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

### 2. 定向单测

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

### 3. Local strict no-motion dry-run

本地 dry-run 写到 sprint artifacts 下；macOS 缺 ROS2 环境时预期可以 fail-closed，但必须保持危险字段 false。

```bash
mkdir -p sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/artifacts
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --output-json sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/artifacts/local_o10_map_server_graph_lifecycle_visibility.raw.json
```

### 4. True-board strict no-motion run/pull artifact

沿用现有 helper/SSH 模式。若 true board、SSH、scp 或 helper 不可用，必须 fail-closed 写明风险，不能写成 mission progress。

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --output-json /tmp/rober_o10_artifacts/live_o10_map_server_graph_lifecycle_visibility.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_graph_lifecycle_visibility.raw.json \
  sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/artifacts/live_o10_map_server_graph_lifecycle_visibility.raw.json
```

### 5. Scoped diff check

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation \
  sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility
```

## Product 计划阶段验收命令

Product planning 阶段用 scoped rg/diff check 验证文档与关键词：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|85%|map_server|graph/lifecycle|strict no-motion|robot-software-engineer|python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper|git diff --check" sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility
```

```bash
git diff --check -- sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility
```

## 输出要求给 Robot Software

Robot Software 返回必须包含：

1. 实际改动的文件列表。
2. 验证命令输出结果，包含关键日志片段。
3. 失败定位，如 true board 不可达、`/map_server` node absent、lifecycle manager/process startup missing、daemon/DDS graph visibility failure、helper budget/timing exhausted 等。
4. 剩余风险。
5. 新 artifact 路径和关键字段。
6. 明确说明没有 NavigateToPose、没有 `/cmd_vel`、没有 `/api/base/manual`、没有 WAVE ROVER UART。

## Product 收口边界

Product closeout 必须保守：

- 如果只得到更清楚的 `/map_server` visibility blocker，记为 O3/O1 supporting diagnostic delta，不调整 OKR 百分比，不归档 KR。
- 如果 `/map_server` visibility clean 但仍暴露 `/map_topic_missing`、`/tf_topic_missing` 或 `/scan` sample timeout，仍记为 no-motion diagnostic delta。
- 如果 lifecycle clean 后出现 planner-only path opportunity，本 sprint 仍不执行 path generation；另起 sprint 评估 planner-only no-motion path gate。
- 只有同轮出现 current-run path generation success、route execution、delivery/operator acceptance、current live HIL 或 external production evidence，才允许讨论 OKR 百分比变化。
