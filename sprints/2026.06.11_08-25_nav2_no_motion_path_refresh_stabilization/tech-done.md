# Nav2 No-Motion Path Refresh Stabilization

sprint_type: micro

Run time: 2026-06-11 08:33:30 CST

## 自主能力目标和本轮抓手

目标是稳定 `PC -> workstation proxy -> 上位机 Robot API -> no-motion Nav2 path generation refresh` 的现时可复验证据。

本轮只证明 planner 能在 managed no-motion runtime 内生成全局路径；不是 `NavigateToPose`，不是固定路线执行，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开 WAVE ROVER 底盘 UART `/dev/ttyS5`。

## 根因定位

初始 PC proxy body 是 read-only existing graph 语义：

- `managed_runtime_opt_in=false`
- `initialpose_opt_in=false`
- `path_generation_opt_in=true`
- `path_generation_timeout_s=8`

这会依赖现场已有 active map/AMCL/planner graph。当前真实上位机清场后没有常驻 planner/localization graph，因此返回 `managed_runtime_started=false`、`planner_server_active=false`、`path_generated=false` 是预期结果。

第一次改为 managed no-motion body 后仍 blocked，真实 direct upper artifact 显示：

- `managed_runtime_started=true`
- `initialpose_published=true`
- `amcl_pose_observed=true`
- `last_successful_phase=amcl_pose_probe`
- `root_causes=[sigint_before_final_artifact, helper_process_timeout_after_partial_artifact]`
- `timeout_budget.process_timeout_s=42`

第二次把 upper wrapper cap 放宽后，artifact 已推进到：

- `last_successful_phase=lifecycle_probe`
- `tf_chain_observed.map_to_base_link=true`
- `current_command=timeout 6 ros2 topic echo --once /scan`
- `timeout_budget.process_timeout_s=84`

最终根因收敛为 helper 在 path-generation 模式下没有复用 localization source-inventory fast path，仍重复跑慢速 `/scan`/`/map` topic echo 和 node info 诊断，导致 upper wrapper timeout 先打断。修复后 path-generation 模式在 TF source inventory 已证明完整链路时也跳过慢 topic echo，直接进入 planner lifecycle recheck 和 ComputePath。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 将 `source_chain_complete` fast path 扩展到 path-generation opt-in 场景。
  - planner lifecycle 仍由 localization ready 后的 recheck 确认，不把 source inventory 误包装成 planner active。
- `onboard/scripts/upper_robot_api.py`
  - 将 Nav2 helper subprocess cap 从 `42s` 调整为 `84s`，低于 PC proxy `90s` 窗口。
  - managed no-motion proof 回包使用 `starts_ros2=true`、`starts_nav2=false`，避免 PC 把 proof helper runtime 误判成 Nav2 start/执行。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `检查路径（高级）` 固定 body 改为 managed no-motion path proof：`timeout_s=20`、`managed_runtime_opt_in=true`、`managed_timeout_s=20`、`managed_map_yaml=/root/rober/onboard/runtime/maps/trashbot_map.yaml`、`initialpose_opt_in=true`、`path_generation_opt_in=true`、`path_generation_timeout_s=20`、目标点 `map:(0.8,0,0)`。
  - PC proxy timeout 预算更新为 `90s`。
- Tests:
  - `onboard/tests/test_nav2_runtime_proof_helper.py`
  - `onboard/tests/test_upper_robot_api.py`
  - `pc-tools/workstation/test/catalog.test.ts`
  - `pc-tools/workstation/test/App.test.ts`
- Docs:
  - `docs/navigation/fixed_route_workflow.md`
  - `docs/hardware/board_sensor_stack_smoke.md`
  - `docs/product/pc_tools_workstation.md`
  - `pc-tools/README.md`

## 真实上位机证据

上位机：`root@192.168.1.11 -p 37878`

部署：

- 已部署 `onboard/scripts/upper_robot_api.py`
- 已部署 `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `trashbot-upper-robot-api.service` 重启后为 `active`

Direct upper API clean pass:

- Artifact: `sprints/2026.06.11_08-25_nav2_no_motion_path_refresh_stabilization/artifacts/direct_upper/response_fastpath.json`
- Request: `POST http://127.0.0.1:8787/api/nav2/proof/refresh`
- Result summary:
  - `status=refreshed`
  - `proof_state=nav2_no_motion_path_generation_runtime_observed`
  - `evidence_type=robot_runtime_material`
  - `managed_runtime_started=true`
  - `managed_runtime_cleanup_ok=true`
  - `initialpose_published=true`
  - `amcl_pose_observed=true`
  - `planner_server_active=true`
  - `path_generation_succeeded=true`
  - `path_generated=true`
  - `path_point_count=31`
  - `root_causes=[]`

Direct latest readback:

- Artifact: `sprints/2026.06.11_08-25_nav2_no_motion_path_refresh_stabilization/artifacts/direct_upper/latest_fastpath.json`
- Key fields:
  - `evidence_type=robot_runtime_material`
  - `path_generated=true`
  - `path_generation_succeeded=true`
  - `path_point_count=31`
  - `planner_server_active=true`

PC proxy clean readback:

- Artifact: `sprints/2026.06.11_08-25_nav2_no_motion_path_refresh_stabilization/artifacts/pc_proxy/response.json`
- Request: `POST http://127.0.0.1:8791/api/robot-control/nav2/proof/refresh?baseUrl=http://192.168.1.11:8787`
- Result summary:
  - `proxy_status=refresh_forwarded`
  - `status=loaded_fail_closed_summary`
  - `remote_http_status=200`
  - `last_result_status=refreshed`
  - `hard_dangerous_true_fields=[]`
  - `blocked_reasons=[]`
  - `latest_readback_key_values.path_generated=true`
  - `latest_readback_key_values.path_generation_succeeded=true`
  - `latest_readback_key_values.path_point_count=31`
  - `latest_readback_key_values.planner_server_active=true`

## No-Motion 安全字段

Direct upper response 保持：

- `safe_to_control=false`
- `delivery_success=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `starts_nav2=false`

PC proxy response 保持：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `hard_dangerous_true_fields=[]`

## Cleanup

最终清场 artifact：

- `sprints/2026.06.11_08-25_nav2_no_motion_path_refresh_stabilization/artifacts/final_service_status.log`
- `sprints/2026.06.11_08-25_nav2_no_motion_path_refresh_stabilization/artifacts/final_process_check.log`
- `sprints/2026.06.11_08-25_nav2_no_motion_path_refresh_stabilization/artifacts/final_lsof.log`
- `sprints/2026.06.11_08-25_nav2_no_motion_path_refresh_stabilization/artifacts/final_fuser.log`

结果：

- `trashbot-upper-robot-api.service=active`
- 无 residual `o10_amcl_nav2_runtime_proof` / `map_server` / `amcl` / `planner_server` / `lifecycle_manager` / `lidar_driver` 目标进程
- `/dev/ttyS5` 无占用
- `/dev/ttyACM0` 无占用

## 验证结果

```text
python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_nav2_runtime_proof_helper
Ran 47 tests in 2.263s
OK
```

```text
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

```text
cd pc-tools/workstation && npm run build
tsc + vite build + server tsc passed
```

```text
cd pc-tools/workstation && npm run test
Test Files 2 passed
Tests 89 passed
```

```text
cd pc-tools/workstation && npm run lint
eslint . passed
```

```text
git diff --check
exit 0
```

## 剩余风险

- 本轮只证明 no-motion planner path generation，不证明 `NavigateToPose`、controller、BT navigator、fixed-route execution、真实运动、避障或 delivery success。
- `latest` endpoint 顶层仍保留 `status=not_proven` 的 fail-closed 语义；可消费字段在 latest/result proof 中，PC proxy 已能读到关键值。
- 目标点仍是固定 `map:(0.8,0,0)`，不是用户选点或固定路线目标。
- 本轮触发 managed runtime 会短暂占用 `/dev/ttyACM0` 用于 LiDAR/AMCL 证据；cleanup 已证明结束后无残留占用。

## 完成前反思

- 未改 `docs/vendor/**`，未改 WAVE ROVER UART/底盘控制代码、串口配置或硬件 launch 参数。
- PC 普通首屏 UI 文案/布局未改；只改了后端固定 proxy body 和测试。文档继续强调普通首屏不得出现 `检查路径`、`Nav2`、`proof`、`/cmd_vel`、`/api/base/manual` 等工程词。
- 当前仓库另有无关改动 `sprints/2026.06.11_08-20_pc_plain_user_home_second_restore/artifacts/pc_plain_user_home_dom_smoke.json`，本轮未触碰、未回滚。
