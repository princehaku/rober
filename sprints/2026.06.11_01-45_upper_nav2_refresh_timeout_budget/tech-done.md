# Upper Nav2 Refresh Timeout Budget

## sprint_type

micro

## 自主能力目标和本轮抓手

目标是修复真实上位机 Nav2 no-motion proof refresh 的 HTTP 返回预算漂移，让 PC `检查路径` 固定 POST 不再先于上位机超时。本轮抓手是收敛 `run_nav2_runtime_proof_helper()` 的 subprocess timeout：PC 固定 body `timeout_s=8`、`path_generation_timeout_s=8`、`managed_runtime_opt_in=false`、`initialpose_opt_in=false` 时，上位机 helper 等待预算为 `36s`，低于 PC proxy `46s`。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `nav2_runtime_proof_process_timeout_budget()`。
  - 将旧的 `max(timeout_s * 8 + 20.0, 45.0)` 替换为结构化预算：
    - collector 基础窗口：`timeout_s`
    - path generation 窗口：仅 `path_generation_opt_in=true` 时计入
    - managed runtime 窗口：仅 `managed_runtime_opt_in=true` 时计入
    - initialpose 小余量：仅 `initialpose_opt_in=true` 时计入
    - cap：`42s`，给 PC proxy `46s` 留 HTTP 返回余量
  - `command_result` 增加 `timeout_budget` 和 `process_timeout_s`，便于现场定位是 helper timeout 还是 PC timeout。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 PC no-motion path generation 固定 body 的预算测试，锁定 `process_timeout_s=36.0`。
  - 新增 managed + path generation 极端输入的 cap 测试，锁定 `process_timeout_s=42.0`。
- `docs/navigation/fixed_route_workflow.md`
  - 补充 Nav2 proof refresh timeout budget 与 PC `检查路径` 46s proxy 预算的关系。
- `sprints/2026.06.11_01-45_upper_nav2_refresh_timeout_budget/artifacts/`
  - 保存远端部署前状态、部署重启状态、direct no-motion smoke 原始响应、summary 和 smoke 后服务状态。

## 接口影响

- `/api/nav2/proof/refresh` 入参不变。
- `/api/nav2/proof/refresh` 响应中的 `command_result` 增加只读诊断字段：
  - `timeout_budget`
  - `process_timeout_s`
- 安全字段保持 fail-closed：
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
  - `publishes_cmd_vel=false`
  - `calls_base_manual=false`
  - `sends_base_motion_commands=false`
- 未新增 `/api/nav2/start`、`/api/nav2/stop`、NavigateToPose、`/cmd_vel`、`/api/base/manual` 或任何底盘动作入口。

## 验证结果

运行时间：2026-06-11 CST。

通过：

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：

```text
Ran 18 tests in 0.062s
OK
```

通过：

```bash
python3 -m unittest onboard.tests.test_upper_robot_api
```

结果：

```text
Ran 7 tests in 0.007s
OK
```

通过：

```bash
git diff --check
```

结果：无 whitespace error。

## 真实上位机部署与 no-motion smoke

部署方式：

- 远端路径确认：`/root/rober/onboard/scripts/upper_robot_api.py`
- 远端服务确认：`trashbot-upper-robot-api.service`
- 同步文件：仅 `onboard/scripts/upper_robot_api.py`
- 远端语法检查：`python3 -m py_compile /root/rober/onboard/scripts/upper_robot_api.py.tmp_codex_timeout_budget`
- 备份远端旧文件：`/root/rober/onboard/scripts/upper_robot_api.py.pre_timeout_budget_20260611_0145`
- 重启方式：`systemctl restart trashbot-upper-robot-api.service`
- 重启后状态：`active`
- 新远端 sha256：`649f0860a9288c36f1a4522fd1eeae734c016241e8e1dceb6ebc5dd4047a0aae`

真实 no-motion direct smoke：

```bash
curl -sS --max-time 46 -X POST http://127.0.0.1:8787/api/nav2/proof/refresh \
  -H 'Content-Type: application/json' \
  -d '{"timeout_s":8,"managed_runtime_opt_in":false,"managed_timeout_s":8,"managed_map_yaml":"","initialpose_opt_in":false,"path_generation_opt_in":true,"path_generation_timeout_s":8,"path_goal_frame_id":"map","path_goal_x":0.8,"path_goal_y":0,"path_goal_yaw":0}'
```

结果摘要：

- HTTP：`200`
- curl total：`36.072669s`
- `command_result.process_timeout_s=36.0`
- `command_result.timeout_budget.budget_policy=finish_before_pc_proxy_timeout_or_return_structured_timeout`
- `command_result.ok=false`
- `command_result.error.type=TimeoutExpired`
- `failure_reason=configured_command_failed`
- `path_generated=true`
- `path_generation_succeeded=true`
- `path_point_count=31`
- `hard_dangerous_true_fields=[]`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

解释：真实 helper 本轮仍慢于 36s subprocess 预算，因此上位机主动返回结构化 `TimeoutExpired`；但 HTTP POST 自身已在 PC 46s 预算内返回，并带回 latest no-motion path proof。相比上一轮 PC proxy `fetch_timeout_46000ms`，现在失败边界从 PC 端超时前移到上位机结构化响应。

## 主节点补充验收

本地启动 PC workstation：

```bash
PORT=8797 npm run api
```

再通过 PC proxy 端到端调用真实上位机：

```bash
curl -sS --max-time 60 -X POST \
  'http://127.0.0.1:8797/api/robot-control/nav2/proof/refresh?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

结果摘要：

- HTTP：`200`
- total：`36.143869s`
- `proxy_status=refresh_forwarded`
- `remote_http_status=200`
- `last_result_status=refreshed`
- `failure_reason=""`
- `blocked_reasons=[]`
- `path_generated=true`
- `path_generation_succeeded=true`
- `path_point_count=31`
- `hard_dangerous_true_fields=[]`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

这条验收说明 PC 真实入口已经不再出现 `fetch_timeout_46000ms`，也不再需要依赖 PC latest fallback 才能表达路径证据。临时 workstation 服务验收后已停止。

## Artifact

- `artifacts/remote_pre_deploy_status.txt`
- `artifacts/remote_deploy_restart_status.txt`
- `artifacts/upper_nav2_refresh_no_motion_direct_raw.txt`
- `artifacts/upper_nav2_refresh_no_motion_direct_summary.json`
- `artifacts/pc_proxy_nav2_refresh_after_upper_budget_raw.txt`
- `artifacts/pc_proxy_nav2_refresh_after_upper_budget_summary.json`
- `artifacts/remote_post_smoke_status.txt`

## 剩余风险

- 真实 helper 本身仍未在 `36s` 内正常退出，当前 smoke 是“HTTP budget 修复 + latest proof 回带成功”，不是 helper 新鲜执行完整成功。
- `latest_result` 中的 no-motion path proof 来自现有 latest artifact；后续如果要证明每次 refresh 都能新鲜生成路径，需要继续优化 `o10_amcl_nav2_runtime_proof.py` 的内部采样顺序或减少 ROS2 命令累计耗时。
- 本轮没有做 Nav2 start/stop、NavigateToPose、map click goal、keyboard control、`/cmd_vel`、`/api/base/manual` 或真实运动验证。

## OKR 说明

本轮推进 O3 现场验证 lane 与 O7 PC `检查路径` 入口的衔接：上位机 POST refresh 已能在 PC 预算内返回 no-motion 规划证据或结构化 root cause，但仍不宣称 fixed-route execution、HIL 或 delivery success。
