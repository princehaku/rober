# O3 ROS2 CLI Source Probe Repair Tech Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Scope: O3/O1 no-motion helper source probe repair

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 `85%`。
2. 本 sprint 是否针对该最低 Objective：否。本 sprint 针对 O3/O1 no-motion localization/path generation 前置 blocker。
3. 不针对 O5 的理由：O5 缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、真实手机/browser 证据，最近多轮已证明继续 support-only/readback/wrapper 不允许计主 OKR 增量。本轮选择 O3 是为了推进当前环境中最接近 mission path generation 的可执行链，并避免继续消费同一 O5 blocker。

## 技术方案

在 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 中增强 `board_source_preflight`，把当前 `board_source_preflight_ros2_cli_unavailable` 拆成更小的只读 probe：

1. Source 阶段：
   - 记录 `/opt/ros/humble/setup.bash` 是否存在、source 是否执行、elapsed、timeout、stderr 短摘要。
   - 记录 workspace setup 是否存在、source 是否执行或跳过。
   - 保留 `ros_setup_source_boundary=run_ros_bash_lc_source_prefix` 或更精确的 source boundary。
2. PATH/which 阶段：
   - 分别执行或等价采样 `command -v ros2`、`type -a ros2`、`which ros2`。
   - 记录 returncode、stdout basename/path 短摘要、stderr、elapsed、timed_out。
   - 不能把空 stdout + timeout 和 command missing 混成同一个结论。
3. CLI invocation 阶段：
   - 在 no-motion 边界内运行最小 `ros2` invocation，例如 `ros2 --help` 或 `ros2 --version`，并记录是否 timeout、returncode、stderr。
   - 如果 `command -v ros2` 成功但 invocation timeout/失败，classification 必须落到 `board_source_preflight_ros2_cli_invocation_timeout` 或等价更窄值。
4. Python/rclpy 阶段：
   - 保留当前 `python3 -c` rclpy import probe。
   - 继续记录 `python_executable`、`rclpy_file`、`sys.path` 短摘要和 import classification。
   - 不能用 `rclpy_import_ok=true` 覆盖 `ros2_cli_ok=false`。
5. 下游 gating：
   - 只有 `ros2_cli_ok=true` 且 `rclpy_import_ok=true` 时才进入 `map_lifecycle_preflight` 与后续 `/scan`、`/amcl_pose`、TF、path generation。
   - 否则下游必须 fail-closed skipped，并携带上游 classification。

## 文件范围

Algorithm owner 允许改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/tech-done.md`
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/artifacts/local_o10_ros2_cli_source_probe_repair.raw.json`
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/artifacts/live_o10_ros2_cli_source_probe_repair.raw.json`

Product owner 本计划阶段只允许改动：

- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/pre_start.md`
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/prd.md`
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/tech-plan.md`

禁止改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- WAVE ROVER、ESP32、UART、串口、底盘协议、launch 默认硬件参数
- O6/O7 archive/UI、cloud relay、手机/PC 操作面

## 接口边界

- Artifact schema 仍属于 O10 no-motion runtime proof；新增字段应在 `proof.board_source_preflight` 内向后兼容扩展。
- 新字段只允许保留短摘要：returncode、elapsed、timed_out、classification、stdout/stderr 安全短句、环境变量路径片段或 basename。不得回显 token、私钥、长 raw stdout/stderr 或无关本地绝对路径。
- `managed_runtime_started=true` 仍只代表 no-motion runtime 被拉起，不代表运动。
- 所有危险字段必须固定 false：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。
- 本轮不得发布 `/cmd_vel`，不得调用 `/api/base/manual`，不得发送 `NavigateToPose`，不得打开 `/dev/ttyS5`。

## 验收命令

Algorithm owner 必须运行并回填结果：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --output sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/artifacts/local_o10_ros2_cli_source_probe_repair.raw.json
```

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest_19_46.json'
```

```bash
ssh -p 37878 root@192.168.1.11 'cat /root/rober/onboard/runtime/nav2_lifecycle_latest_19_46.json' > sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/artifacts/live_o10_ros2_cli_source_probe_repair.raw.json
```

```bash
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair
```

Product plan-stage check:

```bash
git diff --check -- sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair
```

## 验收字段

`local_o10_ros2_cli_source_probe_repair.raw.json` 和 live artifact 至少应包含：

- `proof.board_source_preflight.classification`
- `proof.board_source_preflight.ros2_cli_ok`
- `proof.board_source_preflight.rclpy_import_ok`
- source/PATH/which/CLI invocation/rclpy 的分层摘要字段
- 下游 skipped reason 或 lifecycle/path 结果
- no-motion safety false 字段

推荐 classification：

- `board_source_preflight_source_timeout`
- `board_source_preflight_ros2_cli_path_missing`
- `board_source_preflight_ros2_cli_which_timeout`
- `board_source_preflight_ros2_cli_invocation_timeout`
- `board_source_preflight_ros2_cli_invocation_failed`
- `board_source_preflight_rclpy_import_timeout`
- `board_source_preflight_rclpy_import_failed_*`
- `board_source_preflight_ready`

命名可按实现收敛，但必须能区分 source、PATH/which、CLI invocation 和 rclpy。

## Blocker 第三轮升级口径

本轮是连续第三轮围绕 board sourced shell / ROS2 CLI blocker 推进：

- `17-43`：`ros2_command_unavailable_after_bash_source`
- `18-45`：`board_source_preflight_ros2_cli_unavailable`，且 `rclpy_import_ok=true`
- `19-46`：必须进一步拆分或修复该 blocker

收口规则：

- 若 `ros2_cli_ok=true`，本轮进入下一层 lifecycle/path 诊断，但不直接计 OKR，除非出现 same-run `path_generated=true` 或更强 mission evidence。
- 若 `ros2_cli_ok=false` 但 classification 已缩到 source/PATH/which/CLI invocation 中任一具体层级，本轮只能作为 fail-closed diagnostic progress，OKR 百分比保持不变。
- 若 `ros2_cli_ok=false` 且仍只有泛化 `board_source_preflight_ros2_cli_unavailable` 或 `ros2_command_unavailable_after_bash_source`，`final.md` 必须升级 CEO 决策，不能继续包装成 O3 progress。

## 风险与回滚

- 如果 helper 改动导致 local unit test 失败，Algorithm owner 必须先修复再跑 live。
- 如果 true-board SSH 失败或 artifact 拉取失败，`tech-done.md` 必须写明失败命令、退出码和影响；不得口头声称 live 结论。
- 如果新增字段破坏旧 artifact 形状，必须用单测锁定向后兼容。
- 本轮没有产品代码以外的破坏性回滚动作；不得覆盖或回滚已有未关联改动。

## 输出要求

Algorithm owner 返回时必须包含：

1. 实际改动的文件列表。
2. 验证命令输出结果，包含 exit code 和关键日志片段。
3. 失败定位，如有。
4. 剩余风险。
5. live artifact 对 `ros2_cli_ok`、`rclpy_import_ok`、classification、path generation 和 safety false 字段的结论。
