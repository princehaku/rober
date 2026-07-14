# O3 No-Motion Planner Path Proof Tech Done

## sprint_type

sprint_type: epic

## 自主能力目标和本轮抓手

- 目标：在 **不触发真实运动** 的前提下，验证真实上位机 `HTTP/SSH` 是否还能产出 `no-motion` planner/path proof；若不能，则必须 fail-closed 并给出分层 blocker。
- 抓手：优先验证 `root@192.168.1.11:37878` 与 `http://192.168.1.11:8787/api/nav2/proof/latest` / `/api/nav2/proof/refresh`，最后补跑 local/mock fallback，固定 `safe_to_control=false`、`delivery_success=false`、`hil_pass=false`、`route_execution_success=false`。

## 实际改动

- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/tech-done.md`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/tech-done.md)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/algorithm_worker_report.md`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/algorithm_worker_report.md)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/ssh_probe.txt`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/ssh_probe.txt)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh_raw.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh_raw.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh.pretty.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh.pretty.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh.summary.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/local_preflight.pretty.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/local_preflight.pretty.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/local_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/local_preflight.summary.json)

本轮 **没有改产品代码**，因为现有 `upper_robot_api.py`、`pc-tools/README.md`、`docs/navigation/*` 已明确 `/api/nav2/proof/refresh` 是 no-motion proof 入口，并固定阻断 `/cmd_vel`、`/api/base/manual`、`NavigateToPose`。

## 真实 HTTP/SSH 结果

### 1. SSH 只读预检

- 命令：`ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.1.11 -p 37878 "echo board_live_ssh_ok && hostname && date"`
- 结果：成功
- 摘要：
  - `board_live_ssh_ok`
  - `hostname=op-z3-b6.home`
  - `date=Sat Jul 11 04:44:19 AM CST 2026`

### 2. HTTP latest 只读结果

- 命令：`curl --max-time 5 -sS http://192.168.1.11:8787/api/nav2/proof/latest`
- 结果：成功返回既有 latest artifact。
- latest 中可见历史 no-motion proof 材料，包含：
  - `status=nav2_no_motion_path_generation_runtime_observed`
  - `path_generated=true`
  - `path_generation_succeeded=true`
  - `path_point_count=31`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `robot_control_executed=false`
  - `blocked_commands_not_sent` 含 `/cmd_vel`、`/api/base/manual`

### 3. HTTP refresh 当前轮结果

- 命令：`POST /api/nav2/proof/refresh`
- body：固定 no-motion planner proof 参数，显式 `managed_runtime_opt_in=true`、`initialpose_opt_in=true`、`path_generation_opt_in=true`
- 结果：**当前轮 refresh fail-closed**
- artifact：[`nav2_proof_refresh.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh.summary.json)
- 关键字段：
  - `status=blocked_with_root_cause`
  - `path_generated=false`
  - `path_generation_succeeded=false`
  - `path_point_count=0`
  - `planner_server_active=false`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `hil_pass=false`
  - `robot_control_executed=false`
  - `blocked_commands_not_sent` 含 `/cmd_vel`、`/api/base/manual`、`navigate_to_pose`、`compute_path_to_pose`

### 4. refresh 失败分层

`proof.root_causes[]` 记录为：

- `Nav2 sensor input: /scan_once_not_observed`
- `AMCL localization: /amcl_pose_once_not_observed`
- `Localization TF: map_to_odom_not_observed`
- `Localization TF: map_to_base_link_blocked_by_missing_map_to_odom`
- `planner readiness: localization_not_ready_for_path_generation`

结论：真实上位机 **SSH 可达**，`latest` 里也能看到旧的 no-motion path proof；但 **2026-07-11 当前轮 refresh** 没有复现出 planner/path generation，而是按设计 fail-closed 收口到传感器/AMCL/TF/planner readiness blocker。

## local fallback 结果

- 命令：`python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output /tmp/trashbot_o3_no_motion_preflight_local.json`
- pretty artifact：[`local_preflight.pretty.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/local_preflight.pretty.json)
- summary artifact：[`local_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/local_preflight.summary.json)
- 关键字段：
  - `mode=local`
  - `status=dry_run_template_only_not_proven`
  - `blocked_reason=dry_run_template_only_not_proven`
  - `not_proven=true`
  - `delivery_success=false`
  - `primary_actions_enabled=false`

该 fallback 同时给出了后续模板：

- 真实上位机 SSH 可达证据
- ROS2 setup / package 可用证据
- `/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map` topic smoke
- `map.yaml`、`route.csv`、keyframes、rosbag 或 replay JSONL

## proof boundary

- 本轮真实板子 readback / refresh 结论边界：
  - `software_proof_real_board_no_motion_planner_path_only`
  - 或 `blocked_api_or_ssh_layered_not_proven`
- 本轮 local fallback 边界：
  - `software_proof_local_mock_no_motion_planner_path_only`

无论哪条路径，本轮都保持：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `hil_pass=false`
- `route_execution_success=false`
- `robot_control_executed=false`

## 验证结果

- `python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output /tmp/trashbot_o3_no_motion_preflight_local.json`
  - 输出：`{"output": "/tmp/trashbot_o3_no_motion_preflight_local.json", "schema": "trashbot.board_field_evidence_preflight.v1", "status": "dry_run_template_only_not_proven"}`
- `python3 -m json.tool /tmp/trashbot_o3_no_motion_preflight_local.json > .../local_preflight.pretty.json`
  - 通过
- `test -f sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/tech-done.md`
  - 通过
- `rg -n "no-motion|path proof|blocked_|safe_to_control=false|delivery_success=false|/api/nav2/proof/refresh|/cmd_vel|/api/base/manual|NavigateToPose" ...`
  - 见本文件与 worker report，命中所需边界关键字
- `git diff --check -- sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof`
  - 通过，当前 sprint 范围无 whitespace error

## 剩余风险

- 当前 real-board refresh 失败根因落在 `/scan`、`/amcl_pose`、`map->odom`、planner readiness，同一时间窗口未能复现历史 `path_generated=true`。
- `GET /api/nav2/proof/latest` 读到的是既有 latest artifact，不能替代 **同一轮** refresh 成功证明。
- 本轮没有生成新的 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL，因此还不足以让 O6/O7 计入新的 same-run mission delta。

## 下一轮建议

1. 在真实上位机先做 no-motion ROS graph 清场与 `/scan`、`/amcl_pose`、`/tf` 同窗 smoke，再重跑 `/api/nav2/proof/refresh`。
2. 若 refresh 仍卡在 `map_to_odom_not_observed`，优先查 AMCL runtime 与 map source，而不是继续包装 O5/O6/O7 surface。
3. 只有在同一轮拿到 `path_generated=true` 或新的 `map.yaml/route.csv/keyframe/replay` 材料后，才值得继续推动 O6/O7 消费链。
