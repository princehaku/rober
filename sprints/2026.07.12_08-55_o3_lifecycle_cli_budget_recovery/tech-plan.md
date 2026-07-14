# Tech Plan - O3 Lifecycle CLI Budget Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_lifecycle_cli_budget_recovery_only`
- Plan status: ready for Robot Software single-owner implementation

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective：O5，约 `85%`。
2. 本 sprint 是否针对该最低 Objective：否，本 sprint 针对 O3/O1 strict no-motion lifecycle CLI budget recovery。
3. 不针对 O5 的理由：O5 当前缺真实 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 和 external production evidence。继续 O5 support-only/readback/wrapper 不计分，也会重复消费同一 external production blocker。本轮选择最新可推进的 O3/O1 true-board strict no-motion 链，直接处理上一轮明确留下的 `ros2 lifecycle get /map_server` 与 `ros2 lifecycle get /amcl` timeout，然后在 lifecycle readback clean 后继续观察 `/scan_reliable_and_best_effort_timeout`、`/map_topic_missing`、`/tf_topic_missing`。

## 上一轮起点

`07-53` canonical artifact 已证明：

- `board_source_preflight.classification=board_source_preflight_ready`
- `lightweight_cli_ready=true`
- `cli_ready=true`
- `runtime_ready=true`
- `map_lifecycle_preflight.blocking_reasons.map_server=map_server_lifecycle_command_timeout`
- `map_lifecycle_preflight.blocking_reasons.amcl=amcl_lifecycle_command_timeout`
- `downstream_recovery_summary.scan.publisher_count=1`
- `downstream_recovery_summary.scan.blocked_reason=/scan_reliable_and_best_effort_timeout`
- `downstream_recovery_summary.map.topic_sample.blocked_reason=/map_topic_missing`
- `downstream_recovery_summary.tf.blocked_reason=/tf_topic_missing`
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`

本轮不得回退到 O5 support-only、source/path mismatch、`ros2 --help` gate 或只读 wrapper。本轮 primary target 是 `lifecycle_cli_budget_recovery`。

## Owner 和文件范围

主责 owner：`robot-software-engineer`。

允许 Robot Software 修改或创建：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/tech-done.md`
- `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts/`

Robot Software 不得修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 历史 sprint 目录
- WAVE ROVER、UART、硬件配置或 launch 参数
- Full-stack/O7 UI surface

如果实施中必须触碰硬件事实，先停止并向 Product 说明，需要另派 `rober-hardware-engineer` 读取 `docs/vendor/VENDOR_INDEX.md`。

## 接口边界

- 输入边界：复用 existing true-board / local helper execution；不得要求用户提供新的硬件参数、串口参数或 WAVE ROVER 接线假设。
- 输出边界：新增或扩展 helper artifact 字段，用于表达 lifecycle command-summary、budget、retry、stdout/stderr、elapsed、returncode 和 classification。
- ROS2 边界：只读执行 `ros2 lifecycle get /map_server`、`ros2 lifecycle get /amcl`、node/topic/TF probe；不得调用 NavigateToPose，不得发布 `/cmd_vel`。
- API 边界：不得调用 `/api/base/manual`。
- 硬件边界：必须使用 `--no-base-uart`，不得打开 WAVE ROVER UART。
- Mission 边界：本轮不做 path generation、route execution、delivery success、operator acceptance、HIL pass 或 production cloud proof。

## 技术方案

### 1. 保持 readiness 不回退

保留 `07-53` 的 source/lightweight readiness 成果。`ros2 --help` 继续是 diagnostic，不得重新成为 `cli_ready` hard gate。测试必须覆盖 `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 后进入 lifecycle budget recovery。

### 2. Lifecycle command-summary 分层

在 helper artifact 中为 `/map_server` 与 `/amcl` lifecycle readback 记录：

- command：必须能看到 `ros2 lifecycle get /map_server` 与 `ros2 lifecycle get /amcl`。
- timeout budget 和 elapsed。
- stdout、stderr、returncode。
- first attempt 与 retry attempt。
- node/graph visibility snapshot。
- canonical classification。

分类至少覆盖：

- `lifecycle_command_timeout`
- `inactive stdout`
- `graph ok but lifecycle timeout`
- `active`

### 3. Retry 和预算恢复

Robot Software 可以采用轻量 retry、延长 lifecycle command budget、分离 graph readback 与 lifecycle command readback等方式恢复。验收不要求一定把 lifecycle 修成 active，但要求 artifact 能解释失败层级。

如果 lifecycle command 仍 timeout：

- 必须说明 graph 是否可见。
- 必须保留 retry 结果。
- 必须说明下一步是 budget、daemon、lifecycle manager、process graph 还是 node state 问题。

如果 stdout 为 inactive：

- 必须保留原始 stdout，如 `inactive [2]`。
- 必须标记为 `inactive stdout`，而不是 generic timeout。

如果 stdout 为 active：

- 必须保留原始 stdout，如 `active [3]`。
- 必须标记为 `active`。
- 只能继续采下游 `/scan_reliable_and_best_effort_timeout`、`/map_topic_missing`、`/tf_topic_missing`，仍不做 path generation 或 motion。

### 4. Downstream gating

lifecycle readback clean 后，才继续采集：

- `/scan` publisher-visible sample timeout：保留 `/scan_reliable_and_best_effort_timeout`。
- `/map` topic/sample：保留 `/map_topic_missing` 或新的更窄分类。
- TF topic/source：保留 `/tf_topic_missing` 或新的更窄分类。

lifecycle readback 未 clean 时，不执行 path generation，不扩大到 Hardware 结论。

### 5. No-motion safety invariants

本 sprint 必须固定：

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

### 6. 文档和留档

更新 navigation docs 说明 `08-55` 读法、proof boundary、latest lifecycle blocker、command-summary 字段和 safety invariants。实施完成后写 `tech-done.md`，必须包含实际改动、验证结果、失败定位和剩余风险。

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

### 3. Local dry-run

```bash
mkdir -p sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --output-json sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts/local_o10_lifecycle_cli_budget_recovery.raw.json
```

Local dry-run 在 macOS 缺 `/opt/ros/humble/setup.bash` 时可以 fail-closed，但必须保持所有危险字段 false，并记录失败定位。

### 4. True-board strict no-motion run

如果 true board 可达，必须产出新的 raw artifact：

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --output-json /tmp/live_o10_lifecycle_cli_budget_recovery.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/live_o10_lifecycle_cli_budget_recovery.raw.json \
  sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts/live_o10_lifecycle_cli_budget_recovery.raw.json
```

如果 true board 不可达，必须记录 SSH/SCP/timeout 错误和影响范围；不可达不能写成 OKR progress。

### 5. Scoped diff check

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery
```

## Product 验收命令

Product 计划阶段和收口阶段都用 scoped rg/diff check 验证文档与证据关键词：

```bash
rg -n "08-55|lifecycle_cli_budget_recovery|OKR 最低优先级核对|robot-software-engineer|ros2 lifecycle get /map_server|ros2 lifecycle get /amcl|lifecycle_command_timeout|inactive stdout|graph ok but lifecycle timeout|active|/scan_reliable_and_best_effort_timeout|/map_topic_missing|/tf_topic_missing|path_generation_attempted=false|safe_to_control=false|publishes_cmd_vel=false" sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery
```

```bash
git diff --check -- sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery
```

## 输出要求给 Robot Software

Robot Software 返回必须包含：

1. 实际改动的文件列表。
2. 验证命令输出结果，包含关键日志片段。
3. 失败定位，如 true board 不可达、lifecycle command timeout、inactive stdout、graph ok but lifecycle timeout、active 后下游 `/scan` / `/map` / TF blocker 等。
4. 剩余风险。
5. 新 artifact 路径和关键字段。
6. 明确说明没有 NavigateToPose、没有 `/cmd_vel`、没有 `/api/base/manual`、没有 WAVE ROVER UART。

## Product 收口边界

Product closeout 必须保守：

- 如果只得到更清楚的 lifecycle blocker，记为 O3/O1 supporting diagnostic delta，不调整 OKR 百分比，不归档 KR。
- 如果 lifecycle clean 但仍暴露 `/scan_reliable_and_best_effort_timeout`、`/map_topic_missing` 或 `/tf_topic_missing`，仍记为 no-motion diagnostic delta。
- 如果 lifecycle clean 后出现 planner-only path opportunity，本 sprint 仍不执行 path generation；另起 sprint 评估 planner-only no-motion path gate。
- 只有同轮出现 current-run path generation success、route execution、delivery/operator acceptance、current live HIL 或 external production evidence，才允许讨论 OKR 百分比变化。
