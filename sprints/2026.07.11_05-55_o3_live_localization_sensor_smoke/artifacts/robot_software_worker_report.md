# Robot Software Worker Report

## 改动文件

- [`/Users/m1/apps/rober/onboard/scripts/field_route_evidence_preflight.py`](/Users/m1/apps/rober/onboard/scripts/field_route_evidence_preflight.py)
- [`/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_preflight.py`](/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_preflight.py)
- [`/Users/m1/apps/rober/docs/navigation/field_route_evidence_preflight.md`](/Users/m1/apps/rober/docs/navigation/field_route_evidence_preflight.md)
- [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/tech-done.md`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/tech-done.md)
- [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.raw.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.raw.json)
- [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.pretty.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.pretty.json)
- [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.summary.json)
- [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.raw.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.raw.json)
- [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.pretty.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.pretty.json)
- [`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.summary.json)

## 实际实现内容

1. 在 `field_route_evidence_preflight.py` 新增 live localization smoke：
   - `/scan`
   - `/amcl_pose`
   - `tf2_echo map odom`
   - `tf2_echo map base_link`

2. 在同一脚本里新增固定 no-motion `/api/nav2/proof/refresh` readback：
   - 固定 body 为 managed runtime + initialpose + path generation proof 参数；
   - 顶层危险字段固定 false；
   - 若 refresh payload 里出现 `safe_to_control=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`sends_motion_commands=true`、`robot_control_executed=true` 等危险 true，脚本会直接 fail-closed。

3. 修复 timeout artifact 兼容性：
   - 当前 Python 环境下 `TimeoutExpired.stdout/stderr` 可能是 bytes；
   - 现在先统一做 decode，再脱敏和写 JSON，避免 timeout 过程本身崩掉。

4. 更新文档与单测：
   - 文档补充 live localization smoke 用法、状态和 proof boundary；
   - 单测新增 localization smoke 只读模板、refresh 固定 body、危险字段 fail-closed、dry-run 禁止 `/cmd_vel` 与 `/api/base/manual`。

## 验证命令、结果和关键日志

### 1. `python3 -m py_compile onboard/scripts/o11_nav2_goal_execution_proof.py onboard/scripts/field_route_evidence_preflight.py`

- 结果：通过

### 2. `python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof onboard.tests.test_field_route_evidence_preflight`

- 结果：通过
- 关键输出：
  - `Ran 25 tests in 0.022s`
  - `OK`

### 3. `git diff --check -- onboard/scripts/o11_nav2_goal_execution_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_o11_nav2_goal_execution_proof.py onboard/tests/test_field_route_evidence_preflight.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke`

- 结果：通过

### 4. live smoke artifact

- raw：[`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.raw.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.raw.json)
- summary：[`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.summary.json)
- 结果：
  - `status=blocked_refresh_readback_failed`
  - `localization_blocked_reasons=[blocked_amcl_pose_not_observed, blocked_map_to_odom_not_observed, blocked_map_to_base_link_not_observed]`
  - `/scan` 本轮读到有效 `LaserScan` 样本
  - `/amcl_pose` 读回 `WARNING: topic [/amcl_pose] does not appear to be published yet`
  - `nav2_proof_refresh.status=refresh_command_failed`

### 5. local fallback artifact

- summary：[`/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/local_preflight.summary.json)
- 结果：
  - `status=dry_run_template_only_not_proven`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
  - `route_execution_success=false`
  - `hil_pass=false`

## 失败定位

1. `/amcl_pose` 仍不是 healthy publish
   - 当前 readback 只有 warning 和 type 解析失败；
   - 返工后它不会再被误记为 `observed=true`，而是正确收口到 `blocked_amcl_pose_not_observed`。

2. `map` frame 当前不存在
   - `tf2_echo map odom` 与 `tf2_echo map base_link` 都反复返回 `Invalid frame ID "map"`；
   - 这不是 planner 层单点问题，而是定位图谱前置条件没建立起来。

3. `/scan` 当前窗口已经 healthy observed
   - `returncode=0`；
   - 输出包含 `header:` 与 `ranges:`；
   - 因此当前 LiDAR topic 本轮不再是主 blocker。

4. `/api/nav2/proof/refresh` 当前轮 readback 超时
   - 本轮脚本已经在 localization smoke 之后尝试固定 no-motion body refresh；
   - 但 curl 在预算内没有回包，因此最终状态落在 `blocked_refresh_readback_failed`。

## 剩余风险

- 当前没有新的 same-run path generation success。
- 当前没有新的 `map.yaml`、`route.csv`、keyframes、rosbag 或 replay JSONL。
- 当前 refresh 只证明“readback 超时”，还不足以说明 endpoint 内容已经从上一轮 blocker 演化；最新可确认 blocker 仍是 `/amcl_pose`、`map->odom`、`map->base_link`，而不是 `/scan`。

## 是否需要协同

- `Product`：需要，用于 epic 收口与 OKR 口径。
- `Hardware`：本轮不再是 `/scan` 主 blocker；如下一轮仍涉及 LiDAR，只需只读核对其稳定性和持续发布。
- `Autonomy`：需要，只读聚焦 `/amcl_pose`、`map` frame、`map->odom` 与 refresh timeout。
- `Full-Stack`：不需要。
