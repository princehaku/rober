# O3 Map Odom TF Path Recovery Tech Done

## sprint_type

`sprint_type: epic`

## 实际改动

本轮我只补了一个很窄的 runtime 修复和对应回归验证，没有扩散到 O5/O6/O7、硬件参数或 launch 默认值。

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 把 `ros2 topic info /initialpose --verbose` 改成 lazy probe。
  - 当 rclpy burst publish 或 CLI fallback 已经拿到 `initialpose_subscriber_count` 时，不再重复跑这条只读 CLI。
  - 这样做的原因是：现场 direct helper 已证明这条 probe 可能把 managed runtime 卡死在 `topic_probe`，但它对 root cause 已没有新增信息。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增文本级回归测试，锁定 `/initialpose` verbose info 只能在缺少 subscriber count 时才触发。
- `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/tech-done.md`
  - 记录本轮验证、失败定位和剩余风险。
- `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/artifacts/local_preflight.raw.json`
  - 本地 dry-run 模板产物。
- `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/artifacts/live_nav2_direct_helper_partial_after_lazy_initialpose.raw.json`
  - 真实板 direct helper 最新落盘产物；已越过旧的 `/initialpose` topic-info 卡点。

说明：

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`

这些文件在我开始前已经处于本 sprint 的工作树改动中；本轮没有继续修改它们。

## 验证命令与结果

### 1. Python 语法

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py
```

结果：通过，无输出。

### 2. 目标单测

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api
```

结果：

- `Ran 171 tests in 2.488s`
- `OK (skipped=1)`

### 3. 本地 dry-run artifact

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/artifacts/local_preflight.raw.json
```

结果：

- `schema=trashbot.board_field_evidence_preflight.v1`
- `status=dry_run_template_only_not_proven`

### 4. 真实板 SSH 可达性

```bash
ssh -o ConnectTimeout=12 -o BatchMode=yes -o StrictHostKeyChecking=accept-new -p 37878 root@192.168.1.11 'hostname && date'
```

结果：

- `op-z3-b6.home`
- `Sat Jul 11 11:47:24 AM CST 2026`

说明真实板 SSH 可达，本轮不是网络不可达 blocker。

### 5. live preflight 尝试

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 12 --output sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/artifacts/live_map_odom_tf_path.raw.json
```

结果：

- 本轮这条命令在主会话里没有自然返回；
- 我中断时，traceback 显示它仍卡在 `check_localization_smoke()` 的远端 ROS 只读命令链，尚未走到 refresh body 回读；
- 具体卡点落在 `run_ros_command(..., ["ros2", "topic", "echo", "--once", "/amcl_pose"])` 之前后的远端 SSH/ROS CLI 探测路径，而不是 SSH 建连。

按验收口径，因 preflight 仍未自然回读 helper final body，本轮补跑 direct helper。

### 6. 真实板 direct helper

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
ssh -p 37878 root@192.168.1.11 'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' > sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/artifacts/live_nav2_direct_helper_partial_after_lazy_initialpose.raw.json
```

结果摘要：

- `status=blocked_with_root_cause`
- `last_phase=final`
- `last_successful_phase=cleanup`
- `elapsed_ms=136389`
- `managed_runtime_started=true`
- `initialpose_publish_method=ros2_topic_pub_once_cli_fallback`
- `initialpose_subscriber_count=1`
- `amcl_pose_observed=false`
- `map_to_odom=null`
- `map_to_base_link=null`
- `path_generated=false`

关键 root causes：

- `Nav2 sensor input: /scan_once_not_observed`
- `AMCL initialpose: cli_initialpose_publish_failed`
- `AMCL localization: /amcl_pose_once_not_observed`
- `Localization TF: map_to_odom_not_observed`
- `Localization TF: map_to_base_link_blocked_by_missing_map_to_odom`
- `planner readiness: localization_not_ready_for_path_generation`

本轮最重要的新事实：

- helper 不再卡死在 `ros2 topic info /initialpose --verbose`；
- `initialpose_subscriber_count=1` 已经由 publish 路径直接证明；
- 旧的 initialpose info probe blocker 已被替换成更前置的现场 read-only probe/AMCL/TF blocker。

### 7. diff hygiene

```bash
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_upper_robot_api.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery
```

结果：通过，无 whitespace / conflict 标记问题。

## 失败定位

这轮没有把 `map_to_odom` 推到 true，也没有拿到 same-run path success。当前失败已经继续收敛：

1. 旧 blocker 已消除：
   - helper 不再停在 `ros2 topic info /initialpose --verbose`。
   - `initialpose_subscriber_count=1` 证明 `/initialpose` 订阅匹配至少出现过。
2. 新的现场 blocker 更具体：
   - direct helper 最终依然拿不到 `/scan_once`、`/amcl_pose_once`；
   - 因而 `map_to_odom` 与 `map_to_base_link` 都没有形成可证明的 TF 链；
   - path generation 继续被 `localization_not_ready_for_path_generation` 阻断。
3. preflight 当前主问题不是 API 不可达，而是 localization smoke 的远端 ROS 只读命令链过慢，导致主会话里仍难以自然回读 helper final body。

## 剩余风险

- 本轮仍未证明 `map_to_odom=true`、`map_to_base_link=true` 或 `path_generated=true`。
- `amcl_pose_observed=false` 与 `/scan_once_not_observed` 说明当前 AMCL broadcast 条件仍未满足，或者只读 CLI 在真实板上仍存在采样抖动。
- 现场 `field_route_evidence_preflight.py` 仍需要进一步压缩/分层 localization smoke，避免外层 preflight 再次被远端 ROS CLI 链拖住。
- 本轮继续保持 no-motion 边界，未证明也未执行：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `hil_pass=false`

## 协同判断

- `Product`：暂不需要，新目标和 proof boundary 仍清楚。
- `Hardware`：当前不是新的 UART/vendor 参数问题，暂不需要先介入。
- `Algorithm`：建议下一轮介入一次，重点复核为什么 managed runtime 已启动但 `/scan_once`、`/amcl_pose_once` 和 `map_to_odom` 仍拿不到。
- `Full-Stack`：不需要。

## 下一轮建议

1. 先把 preflight 的 localization smoke 继续拆层，优先把 `/scan_once`、`/amcl_pose_once`、`tf2_echo` 这些只读 CLI 的单条耗时和失败模式各自落盘，而不是长链串行阻塞。
2. 在 direct helper 路径上优先解释：
   - 为什么 `initialpose_subscriber_count=1` 但 `cli_initialpose_publish_failed`；
   - 为什么 `managed_runtime_started=true` 但 `/scan_once_not_observed`。
3. 只有在 `/scan_once`、`/amcl_pose_once` 恢复后，`map_to_odom` 与 path proof 才有意义继续追。

## 文档补充追加

按 AGENTS.md 文档同步规则，本轮补充了导航文档而不再改代码：

- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`

补充点如下：

1. 明确记录 `o10_amcl_nav2_runtime_proof.py` 已把
   `ros2 topic info /initialpose --verbose` 改成 lazy probe，只有 publish 路径没有
   `subscriber_count` 时才补跑。
2. 明确记录本轮 live direct helper 的新边界：
   - 已越过旧 `/initialpose` topic-info 卡点；
   - 仍 fail-closed 在 `/scan_once_not_observed`、`cli_initialpose_publish_failed`、
     `/amcl_pose_once_not_observed`、`map_to_odom_not_observed`；
   - `path_generated=false`，没有 path proof。
3. 再次强调 no-motion proof boundary 不变：
   - `safe_to_control=false`
   - `robot_control_executed=false`
   - `hil_pass=false`
   - `delivery_success=false`
