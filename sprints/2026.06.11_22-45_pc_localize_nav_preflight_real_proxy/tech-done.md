# PC Localize/Nav Preflight Real Proxy

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 将 PC `POST /api/robot-control/localize/reset` 固定 no-motion body 从 `timeout_s=8 / managed_timeout_s=12` 提升到 `timeout_s=30 / managed_timeout_s=30`。
  - 将 localization reset 的 PC fetch cap 从 `60000ms` 提升到 `120000ms`，避免真实定位 runtime 在 TF 完整观测前被 workstation 代理截断。
- `onboard/scripts/upper_robot_api.py`
  - 将上位机 `/api/localize/reset` 默认窗口同步提升到 `timeout_s=30 / managed_timeout_s=30`。
  - 仍保持 `path_generation_opt_in=False`，不执行 NavigateToPose、不发布 `/cmd_vel`、不调用 `/api/base/manual`。
- `pc-tools/workstation/test/catalog.test.ts`、`onboard/tests/test_upper_robot_api.py`
  - 更新 fixed body / default 参数断言。
- `docs/product/pc_tools_workstation.md`、`docs/hardware/board_sensor_stack_smoke.md`
  - 记录 PC 定位 reset + Nav2 no-motion + 导航目标预检真实代理结果和安全边界。

## 真实上车验证结果

真实上位机：`http://192.168.1.11:8787`
PC 本机代理：`http://127.0.0.1:18811`

- 修复前 `POST /api/robot-control/localize/reset`
  - HTTP `200`
  - `proxy_status=refresh_forwarded`
  - `last_result_status=blocked_with_root_cause`
  - readback 已有 `initialpose_published=true`、`amcl_pose_observed=true`
  - 但 `localization_reset_observed=false`、`managed_runtime_cleanup_ok=false`
- 修复后 `POST /api/robot-control/localize/reset`
  - HTTP `200`
  - `proxy_status=refresh_forwarded`
  - `last_result_status=refreshed`
  - readback 显示 `latest_proof_status=nav2_no_motion_localization_runtime_observed`
  - `initialpose_published=true`
  - `amcl_pose_observed=true`
  - `managed_runtime_cleanup_ok=true`
  - `localization_reset_observed=true`
- 修复后 `POST /api/robot-control/nav2/proof/refresh`
  - HTTP `200`
  - `proxy_status=refresh_forwarded`
  - `last_result_status=refreshed`
  - `path_generated=true`
  - `path_generation_succeeded=true`
  - `path_point_count=31`
  - `planner_server_active=true`
- 修复后 `POST /api/robot-control/nav2/goal/preflight`
  - HTTP `400`
  - `proxy_status=preflight_rejected`
  - `failure_reason=operator_report_preflight_required`
  - localization summary 已满足：`localization_reset_observed=true`、`map_to_base_link=true`
  - path summary 已满足：`path_generated=true`、`path_generation_succeeded=true`、`path_point_count=31`
  - operator report 仍缺：`external_video_recorded`、`visible_content_proven`、`wheel_feedback_lr_nonzero_proven`、`physical_motion_lidar_delta_proven`

主要 artifacts：

- `artifacts/02_localize_reset.json`
- `artifacts/04_nav_goal_preflight.json`
- `artifacts/09_localize_reset_after_budget_fix.json`
- `artifacts/10_nav2_refresh_after_budget_fix.json`
- `artifacts/11_nav_goal_preflight_after_budget_fix.json`
- `artifacts/13_remote_cleanup_after_budget_fix.txt`
- `artifacts/14_result_summary_after_fix.json`

## 软件验证结果

- `cd pc-tools/workstation && npm run test -- catalog.test.ts`
  - 通过，`76 passed`。
- `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_localize_reset_uses_builtin_no_motion_helper_defaults`
  - 通过，`OK`。
- `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_localize_reset_uses_builtin_no_motion_helper_defaults onboard.tests.test_nav2_runtime_proof_helper`
  - 通过，`29 tests`。
- `cd pc-tools/workstation && npm run test`
  - 通过，`92 passed`。
- `cd pc-tools/workstation && npm run build`
  - 通过，Vite production build 完成。
- `cd pc-tools/workstation && npm run lint`
  - 通过，ESLint 无报错。
- `git diff --check`
  - 通过，无 whitespace error。

## 剩余风险

- 本轮只证明 PC 能完成真实定位 reset、no-motion 路径刷新和导航目标预检 gate，不证明 NavigateToPose、controller、固定路线执行或真实运动。
- 导航目标预检仍被 operator report 材料 gate 正确拒绝，剩余缺口是外部视频、相机可见内容、轮速非零反馈和 LiDAR motion delta。
- 相机仍是 `/dev/video1` first-frame timeout，实时图传可见内容未恢复。
