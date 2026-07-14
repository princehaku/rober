# O3 Live Localization Sensor Smoke Tech Done

## sprint_type

sprint_type: epic

## 自主能力目标和本轮抓手

- 目标：在真实上位机 no-motion 场景下，把 `/scan`、`/amcl_pose`、`map->odom`、`map->base_link` 和 `/api/nav2/proof/refresh` 收敛成同一轮可复核 artifact。
- 抓手：在 `field_route_evidence_preflight.py` 上扩展 live localization smoke 与 no-motion refresh readback，保持所有危险字段固定为 false，并把 raw/pretty/summary artifact 直接落到本 sprint。

## 实际改动

- 修改 [`/Users/m1/apps/rober/onboard/scripts/field_route_evidence_preflight.py`](/Users/m1/apps/rober/onboard/scripts/field_route_evidence_preflight.py)
- 修改 [`/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_preflight.py`](/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_preflight.py)
- 修改 [`/Users/m1/apps/rober/docs/navigation/field_route_evidence_preflight.md`](/Users/m1/apps/rober/docs/navigation/field_route_evidence_preflight.md)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/robot_software_worker_report.md`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/robot_software_worker_report.md)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.raw.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.raw.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.pretty.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.pretty.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.summary.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.raw.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.raw.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.pretty.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.pretty.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.summary.json)

本轮没有修改 `onboard/scripts/o11_nav2_goal_execution_proof.py` 或 `onboard/tests/test_o11_nav2_goal_execution_proof.py`，因为 no-motion 安全字段已经满足要求，新增需求集中在 preflight 与 artifact 侧。

## 实现内容

1. 在 `field_route_evidence_preflight.py` 新增 live localization smoke/readback 合同：
   - 保留原有通用 `topic_smoke` 与 learn/fixed-route 模板；
   - 新增 `/scan`、`/amcl_pose`、`tf2_echo map odom`、`tf2_echo map base_link` 的只读 smoke；
   - 新增固定 body 的 `/api/nav2/proof/refresh` no-motion readback；
   - 新增危险 true 字段递归扫描，命中后直接 fail-closed；
   - 顶层固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`。

2. 修复真实板 timeout 兼容性：
   - `subprocess.TimeoutExpired.stdout/stderr` 在当前 Python 环境里可能是 `bytes`；
   - 预检脚本现在先统一转文本再做脱敏和摘要，保证 timeout 本身也能稳定写 artifact。

3. 调整执行顺序以适配本轮目标：
   - 通用 `topics` / `topic_smoke` 缺口只记录，不再阻断 live localization smoke；
   - 即使 localization smoke 失败，仍会继续尝试一次 no-motion refresh readback，把 HTTP/ROS failure 分层开。

4. 补充单测和文档：
   - 单测锁定 localization smoke 模板、refresh 固定 body、危险字段 fail-closed，以及 dry-run 不含 `/cmd_vel`、`/api/base/manual`；
   - 文档补充 2026-07-11 live localization smoke 用法、状态枚举和 proof boundary。

## 验证命令与结果

### 1. `python3 -m py_compile onboard/scripts/o11_nav2_goal_execution_proof.py onboard/scripts/field_route_evidence_preflight.py`

- 结果：通过

### 2. `python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof onboard.tests.test_field_route_evidence_preflight`

- 结果：通过
- 关键输出：
  - `Ran 25 tests in 0.022s`
  - `OK`

### 3. `git diff --check -- onboard/scripts/o11_nav2_goal_execution_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_o11_nav2_goal_execution_proof.py onboard/tests/test_field_route_evidence_preflight.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke`

- 结果：通过

### 4. 真实上位机 no-motion smoke

- 命令：
  - `python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 8 --output sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.raw.json`
- 结果：fail-closed
- summary artifact：[`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.summary.json)
- 关键字段：
  - `status=blocked_refresh_readback_failed`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
  - `route_execution_success=false`
  - `hil_pass=false`
  - `localization_blocked_reasons=[blocked_amcl_pose_not_observed, blocked_map_to_odom_not_observed, blocked_map_to_base_link_not_observed]`
  - `nav2_proof_refresh.status=refresh_command_failed`

### 5. 本地 dry-run fallback

- 命令：
  - `python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.raw.json`
- 结果：通过
- summary artifact：[`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.summary.json)
- 关键字段：
  - `status=dry_run_template_only_not_proven`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
  - `route_execution_success=false`
  - `hil_pass=false`

## 失败定位

### live localization smoke

- `/scan`：这次真实板在当前窗口返回了有效 LaserScan 样本，`returncode=0` 且输出包含 `header:` / `ranges:`，因此现在被正确记为 `observed=true`。
- `/amcl_pose`：命令返回 `WARNING: topic [/amcl_pose] does not appear to be published yet` 和 `Could not determine the type for the passed topic`。返工后脚本要求 `returncode=0`、未 timeout、且命中 `header:` / `pose:` marker，因此它现在正确落为 `blocked_amcl_pose_not_observed`。
- `map->odom`：`tf2_echo map odom` 连续报 `Invalid frame ID "map"`，说明当前图谱里连 `map` frame 都没建立起来。
- `map->base_link`：同样因为 `map` frame 不存在而超时。

### no-motion refresh readback

- `/api/nav2/proof/refresh`：通过 SSH 在板上执行固定 body `curl`，在当前 `68s` readback 窗口内仍然超时，没有拿到 JSON 回包。
- 因为 refresh 本身没有回包，本轮无法再次确认上一轮 `blocked_with_root_cause` 是否演化；目前新的可确认 blocker 是：
  - `blocked_amcl_pose_not_observed`
  - `blocked_map_to_odom_not_observed`
  - `blocked_map_to_base_link_not_observed`
  - 外加 `refresh_command_failed`

## 剩余风险

- 当前真实板已证明 `/scan` 当前窗口 healthy observed，但 `/amcl_pose` 仍无健康发布证据，`map->odom` / `map->base_link` 也仍未 ready。
- 当前 refresh 只证明“固定 no-motion curl readback 在本轮超时”，还不能说明 endpoint 已恢复或 root cause 已变化。
- 本轮没有生成新的 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL，因此 O6/O7 仍不能把这轮算作新的路线材料成功。

## 协同需求

- `Product`：需要基于本文件和 worker report 做 epic 收口，明确这轮是 localization/readback blocker 收敛，不是 route success。
- `Hardware`：本轮不再是 `/scan` 主 blocker；如下一轮仍涉及 LiDAR，只需核对其稳定性和持续发布，而不是回到“有没有样本”。
- `Autonomy`：建议聚焦 `/amcl_pose`、`map` frame、`map->odom` 发布链，以及 refresh timeout 是否和 runtime graph 卡死相关。
- `Full-Stack`：本轮不需要。
