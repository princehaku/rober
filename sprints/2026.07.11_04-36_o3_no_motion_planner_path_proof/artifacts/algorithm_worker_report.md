# Algorithm Worker Report

## 自主能力目标和本轮抓手

- 目标：验证真实上位机 `no-motion planner/path proof` 是否仍可复现。
- 抓手：先核验 `/api/nav2/proof/refresh` 的本地代码与文档边界，再执行真实 SSH/HTTP，最后补 local/mock fallback JSON 模板。

## 改动文件和接口影响

- 新增 sprint artifact 与留档：
  - [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/tech-done.md`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/tech-done.md)
  - [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/algorithm_worker_report.md`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/algorithm_worker_report.md)
  - [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/ssh_probe.txt`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/ssh_probe.txt)
  - [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh_raw.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh_raw.json)
  - [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh.pretty.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh.pretty.json)
  - [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/nav2_proof_refresh.summary.json)
  - [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/local_preflight.pretty.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/local_preflight.pretty.json)
  - [`/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/local_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/local_preflight.summary.json)

- 接口影响：无产品接口改动。本轮只消费既有 `/api/nav2/proof/refresh`、`/api/nav2/proof/latest`、SSH read-only 入口。

## 实现内容

1. 先读取本地实现与文档，确认 `/api/nav2/proof/refresh` 走 `o10_amcl_nav2_runtime_proof.py` no-motion helper。
2. 确认本地代码里 `managed_runtime_opt_in`、`initialpose_opt_in`、`path_generation_opt_in` 都必须显式开启，且返回固定 `safe_to_control=false`。
3. 执行真实 SSH 预检，确认 `root@192.168.1.11:37878` 在线。
4. 执行 `GET /api/nav2/proof/latest`，读取既有 latest no-motion path proof。
5. 执行固定 body 的 `POST /api/nav2/proof/refresh`，得到当前轮 fail-closed blocker。
6. 执行 local dry-run fallback，验证 JSON/命令模板与 next-required-evidence 合同。

## 测试、dry-run 或上车验证结果

- SSH：可达，`board_live_ssh_ok`
- HTTP latest：可达，读到历史 `path_generated=true` / `path_point_count=31` 的 no-motion proof
- HTTP refresh：可达，但当前轮返回 `blocked_with_root_cause`
- local fallback：`dry_run_template_only_not_proven`

## 数据、样本或调试输出变化

- 新增真实板 SSH 摘要：[`ssh_probe.txt`](/Users/m1/apps/rober/sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/artifacts/ssh_probe.txt)
- 新增真实 refresh 全量 JSON / pretty JSON / summary JSON
- 新增 local fallback pretty JSON / summary JSON

关键 blocker：

- `blocked_/scan_once_not_observed`
- `blocked_/amcl_pose_once_not_observed`
- `blocked_map_to_odom_not_observed`
- `blocked_localization_not_ready_for_path_generation`

关键安全边界：

- `safe_to_control=false`
- `delivery_success=false`
- `hil_pass=false`
- `robot_control_executed=false`
- `blocked_commands_not_sent` 包含 `/api/nav2/proof/refresh` proof 场景下禁止的 `/cmd_vel`、`/api/base/manual`、`NavigateToPose`

## 失败定位

- SSH 不构成 blocker。
- `GET /api/nav2/proof/latest` 也不构成 blocker，但它只说明历史 latest artifact 存在。
- 真实 blocker 出现在 **当前轮 refresh**：
  - `Nav2 sensor input -> /scan_once_not_observed`
  - `AMCL localization -> /amcl_pose_once_not_observed`
  - `Localization TF -> map_to_odom_not_observed`
  - `planner readiness -> localization_not_ready_for_path_generation`

## 剩余风险

- 当前没有新的 same-run no-motion path proof 成功 artifact。
- 当前也没有新的 `map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL` 产出。
- 后续如果继续只读 latest/readback，而不解决 `/scan` / `AMCL` / `TF` blocker，会重复消费同一类 support-only 现场 blocker。
