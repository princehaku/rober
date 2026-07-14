# Tech Plan - O3 Map/AMCL/Scan/TF Downstream Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_downstream_recovery_only`
- Plan status: ready for Robot Software single-owner implementation

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective：O5，约 `85%`。
2. 本 sprint 是否针对该最低 Objective：否，本 sprint 针对 O3/O1 strict no-motion runtime lane。
3. 不针对 O5 的理由：近几轮 Product closeout 已判定 O5 只有 support-only readiness/readback 包装，缺真实 external production evidence。继续 O5 会重复消费同一 blocker，不能产生 production cloud、production DB/queue、HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实手机/browser 或 external production evidence。本轮选择最新可推进的 O3/O1 true-board strict no-motion 链，直接处理 `map_lifecycle_preflight_map_server_and_amcl_inactive`、`amcl_lifecycle_not_active`、`/scan_no_publisher`、`/map_once_not_observed`、`/tf_topic_missing`。

## 上一轮起点

`06-54` canonical artifact 已证明：

- `board_source_preflight_ready`
- `lightweight_cli_ready=true`
- `cli_ready=true`
- `runtime_ready=true`

本轮不得回退到 O5 support-only、source/path mismatch 或 `ros2 --help` gate。本轮 primary target 是 `map_amcl_scan_tf_downstream` recovery。

## Owner 和文件范围

主责 owner：`robot-software-engineer`。

允许 Robot Software 修改或创建：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/tech-done.md`
- `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts/`

Robot Software 不得修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 历史 sprint 目录
- WAVE ROVER、UART、硬件配置或 launch 参数
- Full-stack/O7 UI surface

如果实施中必须触碰硬件事实，先停止并向 Product 说明，需要另派 `rober-hardware-engineer` 读取 `docs/vendor/VENDOR_INDEX.md`。

## 技术方案

### 1. 保持 readiness 不回退

保留 `06-54` heavy/light/`rclpy` readiness 逻辑。`ros2 --help` 继续是 diagnostic，不得重新成为 `cli_ready` hard gate。测试必须覆盖 `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 后进入 downstream probes。

### 2. Map lifecycle 和 AMCL 分层

在 helper artifact 中明确记录：

- `/map_server` lifecycle command、stdout、stderr、returncode、timeout。
- `/amcl` lifecycle command、stdout、stderr、returncode、timeout。
- `map_lifecycle_preflight.classification` 是否仍为 `map_lifecycle_preflight_map_server_and_amcl_inactive`。
- `amcl_readiness_summary.blocked_reason` 是否仍为 `amcl_lifecycle_not_active`。
- 若 lifecycle active，继续记录 `/amcl_pose` 和 localization readiness，不得直接宣称 path ready。

### 3. `/scan` 和 `/map` topic 分层

对 `/scan_no_publisher` 和 `/map_once_not_observed` 形成结构化差异：

- topic type 是否可见。
- publisher count 和 publisher nodes。
- subscriber count。
- once probe 是否执行、是否 timeout、是否 sample observed。
- BEST_EFFORT / RELIABLE 读法是否需要区分。
- graph 不可见、publisher 不存在、publisher 存在但 sample timeout、QoS/window timeout 的分类。

### 4. TF topic 和 dynamic source 分层

对 `/tf_topic_missing` 形成结构化差异：

- `/tf` topic 是否可见。
- `/tf_static` topic 是否可见。
- dynamic `map->odom` 是否 observed。
- static `base_link->laser_frame` 是否 observed。
- `map->base_link` 是否只是被 missing `map->odom` 阻塞。
- TF source probe 是否执行、是否 timeout、是否 graph blocker。

### 5. Planner-only path gate

默认不触发 path generation。如果 helper 已证明 lifecycle、topic、AMCL、TF 都 readiness clean，可进入 planner-only no-motion path gate：

- 只允许 ComputePathToPose 类路径计算。
- 禁止 NavigateToPose。
- 禁止 `/cmd_vel`。
- 禁止 `/api/base/manual`。
- 禁止 WAVE ROVER UART。
- `path_generation_attempted=true` 只有在 artifact 清楚证明 planner-only no-motion 时才允许。
- `route_execution_success`、`delivery_success`、`safe_to_control`、`robot_control_executed`、`hil_pass`、`uses_base_uart` 必须保持 `false`。

### 6. 文档和留档

更新 navigation docs 说明 `07-53` 读法、proof boundary、最新 blocker 和 safety invariants。实施完成后写 `tech-done.md`，必须包含实际改动、验证结果、失败定位和剩余风险。

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
mkdir -p sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --output-json sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts/local_map_amcl_scan_tf_downstream_recovery.raw.json
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
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --output-json /tmp/live_o10_map_amcl_scan_tf_downstream_recovery.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/live_o10_map_amcl_scan_tf_downstream_recovery.raw.json \
  sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts/live_o10_map_amcl_scan_tf_downstream_recovery.raw.json
```

如果 true board 不可达，必须记录 SSH/SCP/timeout 错误和影响范围；不可达不能写成 OKR progress。

### 5. Optional planner-only no-motion path gate

只有当 lifecycle、topic、AMCL、TF readiness 已 clean，才允许运行 planner-only path gate：

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --path-generation-opt-in --output-json /tmp/live_o10_planner_only_path_gate.raw.json'
```

该命令仍禁止 NavigateToPose、`/cmd_vel`、`/api/base/manual` 和 WAVE ROVER UART。若运行，必须拉回 artifact 并证明所有 dangerous fields 保持 false。

### 6. Scoped diff check

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery
```

## Product 验收命令

Product 计划阶段和收口阶段都用 scoped rg/diff check 验证文档与证据关键词：

```bash
rg -n "07-53|map_amcl_scan_tf_downstream|map_lifecycle_preflight_map_server_and_amcl_inactive|amcl_lifecycle_not_active|/scan_no_publisher|/map_once_not_observed|/tf_topic_missing|strict no-motion|OKR 最低优先级核对|robot-software-engineer" sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery
```

```bash
git diff --check -- sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery
```

## 输出要求给 Robot Software

Robot Software 返回必须包含：

1. 实际改动的文件列表。
2. 验证命令输出结果，包含关键日志片段。
3. 失败定位，如 true board 不可达、lifecycle 未 active、topic 无 publisher、sample timeout、TF missing 等。
4. 剩余风险。
5. 新 artifact 路径和关键字段。
6. 明确说明没有 NavigateToPose、没有 `/cmd_vel`、没有 `/api/base/manual`、没有 WAVE ROVER UART。

## Product 收口边界

Product closeout 必须保守：

- 如果只得到更清楚的 map/AMCL/scan/TF blocker，记为 O3/O1 supporting diagnostic delta，不调整 OKR 百分比，不归档 KR。
- 如果得到 planner-only no-motion path proof，可以记录为 path gate delta，但仍不等于 route execution、delivery success、safe-to-control 或 HIL。
- 只有同轮出现 current-run path generation success、route execution、delivery/operator acceptance、current live HIL 或 external production evidence，才允许讨论 OKR 百分比变化。
