# O3 AMCL TF Final Artifact Bounded Probe Tech Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Execution mode: single-owner closed loop, no fake parallelism
- Safety mode: strict no-motion

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 O5，约 `85%`。
2. 本 sprint 不直接针对 O5。
3. 不针对 O5 的具体理由：
   - O5 当前缺口是 `真实公网 HTTPS/TLS`、`真实 4G/SIM`、`production DB/queue`、`production worker/cutover`、`OSS/CDN live traffic` 和 `真实手机/browser`；
   - 最近 O5 support-only/readback/cutover readiness 已明确 `okr_credit_allowed=false`；
   - 没有真实 production/external evidence 时，继续 O5 只会重复包装 readiness、readback 或 checklist，不会产生主 OKR 增量；
   - O3/O1 no-motion localization/path readiness 当前已经越过旧 source/CLI blocker，是可推进、可验证、且能直接解锁 current-run route/material chain 的最低可动链路。

本轮 OKR 方向：暂停 O5 support-only 包装，继续 O3/O1 no-motion AMCL/TF/path readiness。除非 worker 产出新的 same-run path、route、delivery/operator、HIL 或 production external evidence，否则本轮不预设 OKR 百分比变化、不归档 KR。

## 最近两轮 Blocker 扫描

- 18-45 `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/final.md`
  - blocker: `board_source_preflight_ros2_cli_unavailable`
  - 事实：`ros2_cli_ok=false`，`rclpy_import_ok=true`，map lifecycle preflight 被跳过。
- 19-46 `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/final.md`
  - blocker 已推进到 `board_source_preflight_ready`
  - 事实：`ros2_cli_ok=true`，`rclpy_import_ok=true`，`source_stage_ok=true`
  - live artifact 状态：`status=interrupted_before_final_artifact`
  - 下游 blocker：`sigterm_before_final_artifact`、`/amcl_pose_once_not_observed`、`map_to_odom_not_observed`、`map_to_base_link_blocked_by_missing_map_to_odom`
  - path 读数：`path_generation_requested=true`，`path_generation_attempted=false`，`path_generated=false`

结论：本轮不触发同一 blocker 第三轮升级。旧 `ros2_cli_ok=false` / source blocker 已实质移动；本轮必须转向 AMCL lifecycle、`/amcl_pose`、动态 `map->odom`、`map->base_link` 和 final artifact bounded closeout。

## Owner 和分工

只派 `robot-algorithm-engineer` 单线闭环。

理由：

- 文件范围集中在 Algorithm helper、unit tests、导航文档、本 sprint artifacts 和 `tech-done.md`；
- 不涉及 cloud/O6/O7 UI；
- 不涉及硬件驱动配置、WAVE ROVER UART、电气或 vendor 参数；
- 所有验收证据可由一个 owner 在 local/live no-motion 链路中产出；
- 多 owner 并行没有独立接口面，会变成假并行。

## 文件范围

Algorithm worker 允许修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/tech-done.md`
- `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts/`

Product closeout 后续允许修改：

- `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/side2side_check.md`
- `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

本轮 Algorithm worker 不应修改：

- cloud relay / O6 archive / O7 workstation；
- WAVE ROVER、UART、硬件驱动或 vendor docs；
- 其它 sprint 目录；
- 与 AMCL/TF/path final artifact 无关的代码。

## 接口影响

预期接口影响：

- 扩展或收紧 `o10_amcl_nav2_runtime_proof.py` 输出 artifact 的 AMCL、TF 和 final/partial closeout 字段；
- 增加 `sigterm_before_final_artifact`、AMCL lifecycle、`/amcl_pose`、`map->odom`、`map->base_link` 的结构化 root cause；
- 在 localization ready 时，仅通过 planner-only `ComputePathToPose` path probe 写 path generation 字段；
- 保持现有 CLI 参数兼容，除非在 `tech-done.md` 明确记录新增参数和默认值；
- 同步导航文档，说明本轮字段的 proof boundary 和 no-motion 限制。

不得产生的接口影响：

- 不新增或调用运动控制 API；
- 不发布 `/cmd_vel`；
- 不调用 `/api/base/manual`；
- 不发送 NavigateToPose goal；
- 不打开 WAVE ROVER UART；
- 不让 UI/O6/O7 消费端把本轮 artifact 误判为 delivery 或 route execution success。

## 实施步骤

1. 读取 19-46 `tech-done.md`、`final.md` 和 live artifact，确认旧 source/CLI blocker 已 ready。
2. 在 helper 中补齐 final/partial artifact 写出路径，确保 SIGTERM、timeout 或 managed runtime interruption 时尽量落盘。
3. 拆分 AMCL lifecycle 与 `/amcl_pose` sample 结果，写出 active、topic type、subscriber/publisher、sample timing 和 blocked reason。
4. 拆分 TF edge：
   - dynamic `map->odom`；
   - odom/base edge；
   - downstream `map->base_link`；
   - freshness/source/boundary。
5. 保持 planner-only path probe：只有 localization/TF gate ready 时才 attempt `ComputePathToPose`。
6. 补充 unit tests，覆盖 success、fail-closed、partial artifact、dangerous fields false 和 path generation not attempted 的分支。
7. 更新导航文档与本 sprint `tech-done.md`。
8. 运行 local 和 live no-motion 验收命令；失败时先定位修复，再复验。

## No Motion 风险边界

固定禁止：

- `/cmd_vel`
- `/api/base/manual`
- NavigateToPose goal
- WAVE ROVER UART
- safe-to-control claim
- HIL pass claim
- route execution success claim
- delivery success claim

固定 false 字段：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

允许 true 的字段仅限 no-motion runtime/readback 类事实，例如：

- `starts_nav2=true`
- `managed_runtime_started=true`
- `map_server_active=true`
- `amcl_active=true`
- `path_generation_requested=true`
- `path_generation_attempted=true`
- `path_generated=true`

其中 `path_generated=true` 只能表示 planner-only path probe 成功，不等于 route execution、NavigateToPose、HIL 或 delivery success。

## 验收命令

Algorithm worker 必须在仓库根目录执行以下命令，并把日志片段写入 `tech-done.md`。

### 1. Python 语法检查

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

### 2. Targeted unit tests

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

### 3. Local fail-closed artifact smoke

```bash
mkdir -p sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts/local_o10_amcl_tf_final_artifact_bounded_probe.raw.json
```

预期：local 环境可以 exit `2` fail-closed，但必须写出 artifact，且危险字段保持 false。

### 4. Push helper to live board

```bash
scp -P 37878 \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

### 5. Live no-motion helper run

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py \
    --timeout-s 30 \
    --managed-timeout-s 90 \
    --managed-runtime-opt-in \
    --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
    --initialpose-opt-in \
    --path-generation-opt-in \
    --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

预期：允许 exit `0` 或 fail-closed nonzero；不允许运动控制；必须尽量写出 final 或 structured partial artifact。

### 6. Pull live artifact

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts/live_o10_amcl_tf_final_artifact_bounded_probe.raw.json
```

### 7. Artifact invariant check

```bash
python3 - <<'PY'
import json
from pathlib import Path

path = Path("sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts/live_o10_amcl_tf_final_artifact_bounded_probe.raw.json")
data = json.loads(path.read_text())
text = json.dumps(data, ensure_ascii=False, sort_keys=True)

required_false = [
    '"safe_to_control": false',
    '"robot_control_executed": false',
    '"route_execution_success": false',
    '"delivery_success": false',
    '"hil_pass": false',
]
for marker in required_false:
    if marker not in text:
        raise SystemExit(f"missing invariant: {marker}")

required_terms = [
    "amcl",
    "map_to_odom",
    "map_to_base_link",
    "path_generated",
]
for term in required_terms:
    if term not in text:
        raise SystemExit(f"missing artifact term: {term}")

print("artifact_invariants_ok")
PY
```

### 8. Documentation and scoped diff check

```bash
rg -n "amcl|map_to_odom|map_to_base_link|path_generated|no-motion|no motion" \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/tech-done.md

git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe
```

Product planning validation for this planning-only change:

```bash
git diff --check -- sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe
```

## 验收标准

Accepted as progress only if:

- source/CLI blocker is not re-consumed as the main conclusion;
- artifact includes AMCL lifecycle and `/amcl_pose` layer results;
- artifact includes dynamic `map->odom` and downstream `map->base_link` layer results;
- artifact includes path generation requested/attempted/generated results;
- false safety/control/HIL/delivery invariants hold;
- tests and scoped diff check pass;
- docs/navigation and sprint `tech-done.md` are updated.

Accepted as OKR score movement only if final evidence crosses a real gate:

- same-run planner-only `path_generated=true` with point count greater than 0 may support O1/O3 readiness, but still needs Product closeout before score movement;
- route execution, delivery/operator acceptance, HIL, or production cloud evidence are out of scope and must remain false unless separately proven in a later sprint.

## 失败处理

如果验证失败，Algorithm worker 不能把第一轮失败直接交差。必须：

1. 阅读失败日志；
2. 定位 root cause；
3. 修复 helper/test/doc 或收紧 fail-closed artifact；
4. 重跑相关验收命令；
5. 在 `tech-done.md` 记录失败定位、修复和剩余风险。

如果 live board 不可达或 SIGTERM 仍无法写出 artifact，则本轮可 fail-closed，但必须提供：

- SSH/SCP 失败或中断日志片段；
- local helper artifact；
- 不能证明的字段列表；
- 下一轮最小执行命令。
